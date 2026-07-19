"""
工作流 API 接口模块
提供启动、查看状态、恢复运行等核心接口
支持SSE流式输出

LangGraph 1.0+ 语法：使用 Command 模式恢复中断的工作流
"""
import uuid
import json
import io
import re
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Literal, AsyncGenerator
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from langgraph.types import Command
import psycopg

from app.graph.workflow import get_graph
from app.graph.state import INITIAL_STATE
from app.graph.utils import get_checkpointer
from app.core.config import settings
from app.core.logger import app_logger
from app.models.user import User
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/workflow", tags=["Workflow"])


# ============== 请求/响应模型 ==============

class NodeMetricInfo(BaseModel):
    """节点执行指标"""
    node_name: str = Field(..., description="节点名称")
    duration_ms: float = Field(default=0, description="执行耗时(毫秒)")
    input_tokens: int = Field(default=0, description="输入token数量")
    output_tokens: int = Field(default=0, description="输出token数量")
    total_tokens: int = Field(default=0, description="总token数量")
    start_time: str = Field(default="", description="开始时间")
    end_time: str = Field(default="", description="结束时间")
    model: str = Field(default="", description="使用的模型")


class StartWorkflowRequest(BaseModel):
    """启动工作流请求"""
    topic_direction: str = Field(
        ..., 
        description="主题方向，例如：AI技术、Python开发",
        min_length=1,
        max_length=200
    )


class StartWorkflowResponse(BaseModel):
    """启动工作流响应"""
    thread_id: str = Field(..., description="工作流线程ID")
    status: str = Field(..., description="当前状态")
    generated_topics: List[str] = Field(default=[], description="生成的选题标题列表")
    message: str = Field(..., description="提示信息")
    interrupt_info: Optional[Dict[str, Any]] = Field(default=None, description="中断信息")
    node_metrics: List[NodeMetricInfo] = Field(default=[], description="节点执行指标")


class WorkflowStateResponse(BaseModel):
    """工作流状态响应"""
    thread_id: str = Field(..., description="工作流线程ID")
    status: str = Field(..., description="当前状态")
    values: Dict[str, Any] = Field(default={}, description="当前状态值")
    next_nodes: List[str] = Field(default=[], description="下一个待执行节点")
    is_completed: bool = Field(default=False, description="是否已完成")
    interrupt_info: Optional[Dict[str, Any]] = Field(default=None, description="中断信息")
    node_metrics: List[NodeMetricInfo] = Field(default=[], description="节点执行指标")


WorkflowAction = Literal["select_topic", "approve", "reject", "approve_images", "regenerate_image", "generate_missing_images"]


class ResumeWorkflowRequest(BaseModel):
    """恢复工作流请求"""
    action: WorkflowAction = Field(
        ..., 
        description="操作类型：select_topic(选择选题)、approve(通过审核)、reject(驳回)、approve_images(通过配图)、regenerate_image(重生成配图)、generate_missing_images(补齐缺失配图)"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="操作数据，select_topic时需要selected_topic，reject时需要feedback，regenerate_image时需要index/feedback"
    )


class ResumeWorkflowResponse(BaseModel):
    """恢复工作流响应"""
    thread_id: str = Field(..., description="工作流线程ID")
    status: str = Field(..., description="当前状态")
    message: str = Field(..., description="提示信息")
    next_nodes: List[str] = Field(default=[], description="下一个待执行节点")
    is_completed: bool = Field(default=False, description="是否已完成")
    result: Optional[Dict[str, Any]] = Field(default=None, description="完成时的结果")
    interrupt_info: Optional[Dict[str, Any]] = Field(default=None, description="下一个中断信息")
    node_metrics: List[NodeMetricInfo] = Field(default=[], description="节点执行指标")


class ThreadInfo(BaseModel):
    """线程信息"""
    thread_id: str = Field(..., description="线程ID")
    topic_direction: str = Field(default="", description="主题方向")
    selected_topic: str = Field(default="", description="选中的选题")
    status: str = Field(default="", description="当前状态")
    is_completed: bool = Field(default=False, description="是否已完成")
    created_at: Optional[str] = Field(default=None, description="创建时间")


class ThreadListResponse(BaseModel):
    """线程列表响应"""
    threads: List[ThreadInfo] = Field(default=[], description="线程列表")
    total: int = Field(default=0, description="总数")


# ============== 辅助函数 ==============

def extract_interrupt_info(state_snapshot) -> Optional[Dict[str, Any]]:
    """
    从状态快照中提取中断信息
    
    LangGraph 1.0+ 的中断信息存储在 tasks 中
    """
    if not state_snapshot or not hasattr(state_snapshot, 'tasks'):
        return None
    
    for task in state_snapshot.tasks:
        if hasattr(task, 'interrupts') and task.interrupts:
            for interrupt_obj in task.interrupts:
                if hasattr(interrupt_obj, 'value'):
                    return interrupt_obj.value
    
    return None


def _strip_markdown_for_publish(content: str) -> str:
    """生成可直接复制到内容平台的纯文本版本。"""
    text = re.sub(r"```[\s\S]*?```", "", content or "")
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    text = re.sub(r"[*_~`]", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _build_publish_tags(title: str, topic_direction: str, article_content: str) -> List[str]:
    """优先沿用正文话题，再根据选题语义补充稳定标签。"""
    tags: List[str] = []

    def add_tag(value: str) -> None:
        cleaned = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff-]", "", value).strip("-_ ")
        if 2 <= len(cleaned) <= 20 and cleaned.lower() not in {tag.lower() for tag in tags}:
            tags.append(cleaned)

    for match in re.findall(r"(?<!\w)#([A-Za-z0-9_\u4e00-\u9fff-]{2,20})", article_content or ""):
        add_tag(match)

    combined = f"{title} {topic_direction} {article_content[:800]}".lower()
    keyword_tags = [
        (("ai", "人工智能"), "AI"),
        (("agent", "智能体"), "AI智能体"),
        (("自动化",), "自动化"),
        (("效率",), "效率提升"),
        (("内容", "文案"), "内容创作"),
        (("运营",), "内容运营"),
        (("小红书",), "小红书运营"),
        (("职场", "打工人"), "职场成长"),
        (("求职", "面试"), "求职干货"),
        (("python",), "Python"),
        (("教程", "方法", "干货"), "实用干货"),
        (("生活", "日常"), "生活分享"),
    ]
    for keywords, tag in keyword_tags:
        if any(keyword in combined for keyword in keywords):
            add_tag(tag)

    for segment in re.split(r"[|｜,，、/;；:：\s]+", topic_direction or ""):
        add_tag(segment)

    if not tags:
        tags.extend(["内容创作", "经验分享"])
    return tags[:10]


def _safe_package_text(value: str) -> bytes:
    """带 UTF-8 BOM，确保 Windows 记事本直接打开中文不乱码。"""
    return (value or "").encode("utf-8-sig")


# ============== API 接口 ==============

@router.post("/start", response_model=StartWorkflowResponse)
async def start_workflow(
    request: StartWorkflowRequest,
    current_user: User = Depends(get_current_user)
) -> StartWorkflowResponse:
    """
    启动新的工作流（选题阶段：非流式 + 结构化输出 + token统计）
    
    接收主题方向，启动工作流并运行到第一个中断点（选题阶段）
    返回生成的5个选题标题
    
    Args:
        request: 包含 topic_direction 的请求体
        
    Returns:
        包含 thread_id 和生成的选题列表
    """
    try:
        # 生成唯一的线程 ID（包含用户ID前缀用于隔离）
        thread_id = f"{current_user.id}_{uuid.uuid4()}"
        
        # 记录工作流启动
        app_logger.workflow_started(
            thread_id=thread_id,
            topic_direction=request.topic_direction
        )
        
        # 获取编译后的图
        graph = await get_graph()
        
        # 配置
        config = {"configurable": {"thread_id": thread_id}}
        
        # 初始输入
        initial_input = {
            **INITIAL_STATE,
            "topic_direction": request.topic_direction,
            "status": "started",
        }
        
        # 运行图直到第一个中断点
        # LangGraph 1.0+ 中 ainvoke 会在遇到 interrupt() 时暂停
        result = await graph.ainvoke(initial_input, config)
        
        # 获取状态快照以获取中断信息
        state_snapshot = await graph.aget_state(config)
        interrupt_info = extract_interrupt_info(state_snapshot)
        state_values = state_snapshot.values if state_snapshot else {}
        
        # interrupt 暂停时 ainvoke 的返回值可能不包含完整状态，优先读取快照。
        generated_topics = state_values.get("generated_topics") or result.get("generated_topics", [])
        current_status = state_values.get("status") or result.get("status", "unknown")
        node_metrics = state_values.get("node_metrics") or result.get("node_metrics", [])

        if not generated_topics and interrupt_info and interrupt_info.get("action_required") == "select_topic":
            generated_topics = interrupt_info.get("options", [])
            current_status = "topics_generated"

        if current_status == "error" or not generated_topics:
            error_message = (
                state_values.get("error")
                or result.get("error")
                or "大模型未返回有效选题，请检查 LLM API Key、模型名或服务额度"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_message
            )
        
        # 记录阶段变化
        app_logger.workflow_stage_changed(
            thread_id=thread_id,
            stage="topics_generated",
            topics_count=len(generated_topics)
        )
        
        return StartWorkflowResponse(
            thread_id=thread_id,
            status=current_status,
            generated_topics=generated_topics,
            message="工作流已启动，请选择一个选题继续",
            interrupt_info=interrupt_info,
            node_metrics=node_metrics
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.workflow_error(
            thread_id=thread_id if 'thread_id' in dir() else "unknown",
            error=str(e),
            stage="start"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动工作流失败: {str(e)}"
        )


@router.get("/state/{thread_id}", response_model=WorkflowStateResponse)
async def get_workflow_state(
    thread_id: str,
    current_user: User = Depends(get_current_user)
) -> WorkflowStateResponse:
    """
    获取工作流当前状态
    
    Args:
        thread_id: 工作流线程ID
        
    Returns:
        当前工作流状态快照
    """
    try:
        # 验证 thread_id 属于当前用户
        if not thread_id.startswith(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此工作流"
            )
        
        # 获取编译后的图
        graph = await get_graph()
        
        # 配置
        config = {"configurable": {"thread_id": thread_id}}
        
        # 获取状态快照
        state_snapshot = await graph.aget_state(config)
        
        if state_snapshot is None or state_snapshot.values is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到工作流: {thread_id}"
            )
        
        # 获取下一个待执行节点
        next_nodes = list(state_snapshot.next) if state_snapshot.next else []
        
        # 判断是否已完成
        is_completed = len(next_nodes) == 0 and not extract_interrupt_info(state_snapshot)
        
        # 获取中断信息
        interrupt_info = extract_interrupt_info(state_snapshot)
        
        # 获取节点指标
        node_metrics = state_snapshot.values.get("node_metrics", [])
        
        return WorkflowStateResponse(
            thread_id=thread_id,
            status=state_snapshot.values.get("status", "unknown"),
            values=dict(state_snapshot.values),
            next_nodes=next_nodes,
            is_completed=is_completed,
            interrupt_info=interrupt_info,
            node_metrics=node_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流状态失败: {str(e)}"
        )


@router.post("/resume/{thread_id}", response_model=ResumeWorkflowResponse)
async def resume_workflow(
    thread_id: str, 
    request: ResumeWorkflowRequest,
    current_user: User = Depends(get_current_user)
) -> ResumeWorkflowResponse:
    """
    恢复工作流运行 (LangGraph 1.0+ Command 模式)
    
    使用 Command 对象向中断的工作流提供用户输入并恢复执行
    
    Args:
        thread_id: 工作流线程ID
        request: 包含操作类型和数据的请求体
        
    Returns:
        恢复后的工作流状态
    """
    try:
        # 验证 thread_id 属于当前用户
        if not thread_id.startswith(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此工作流"
            )
        
        # 获取编译后的图
        graph = await get_graph()
        
        # 配置
        config = {"configurable": {"thread_id": thread_id}}
        
        # 获取当前状态
        current_state = await graph.aget_state(config)
        
        if current_state is None or current_state.values is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到工作流: {thread_id}"
            )
        
        # 根据操作类型构建 resume 数据
        # LangGraph 1.0+ 使用 Command(resume=value) 来恢复中断
        resume_value: Dict[str, Any] = {}
        
        if request.action == "select_topic":
            # 选择选题
            if not request.data or "selected_topic" not in request.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="选择选题需要提供 selected_topic"
                )
            resume_value = {
                "selected_topic": request.data["selected_topic"],
            }
            # 记录选题
            app_logger.topic_selected(
                thread_id=thread_id,
                selected_topic=request.data["selected_topic"]
            )
            
        elif request.action == "approve":
            # 审核通过
            resume_value = {
                "action": "approve",
            }
            # 记录审核通过
            app_logger.draft_approved(thread_id=thread_id)
            
        elif request.action == "reject":
            # 审核驳回
            feedback = request.data.get("feedback", "") if request.data else ""
            resume_value = {
                "action": "reject",
                "feedback": feedback,
            }
            # 记录驳回
            revision_count = current_state.values.get("revision_count", 0)
            app_logger.draft_rejected(
                thread_id=thread_id,
                feedback=feedback,
                revision_count=revision_count
            )
        
        elif request.action == "approve_images":
            # 配图审核通过
            resume_value = {
                "action": "approve_images",
            }

        elif request.action == "generate_missing_images":
            # 补齐未生成的配图
            resume_value = {
                "action": "generate_missing_images",
            }

        elif request.action == "regenerate_image":
            # 局部重生成配图
            if not request.data or "index" not in request.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="重生成配图需要提供 index"
                )
            resume_value = {
                "action": "regenerate_image",
                "index": request.data["index"],
                "feedback": request.data.get("feedback", ""),
            }

        # 使用 Command 恢复工作流
        # LangGraph 1.0+ 中，使用 ainvoke(Command(resume=value), config) 恢复
        resume_command = Command(resume=resume_value)

        # 恢复运行直到下一个中断点或结束
        result = await graph.ainvoke(resume_command, config)
        
        # 获取更新后的状态
        updated_state = await graph.aget_state(config)
        next_nodes = list(updated_state.next) if updated_state.next else []
        interrupt_info = extract_interrupt_info(updated_state)
        is_completed = len(next_nodes) == 0 and not interrupt_info
        
        # 获取节点指标
        node_metrics = updated_state.values.get("node_metrics", [])
        
        # 构建响应
        message = "操作成功"
        final_result = None
        
        if is_completed:
            message = "工作流已完成"
            final_result = {
                "article_content": updated_state.values.get("article_content", ""),
                "visual_points": updated_state.values.get("visual_points", []),
                "image_urls": updated_state.values.get("image_urls", []),
                "image_model": updated_state.values.get("image_model", ""),
                "image_review_status": updated_state.values.get("image_review_status", ""),
                "image_history": updated_state.values.get("image_history", []),
            }
            # 记录工作流完成
            app_logger.workflow_completed(thread_id=thread_id)
        elif interrupt_info:
            action_required = interrupt_info.get("action_required", "")
            if action_required == "review":
                message = "文章草稿已生成，请审核"
                # 记录草稿生成
                article_content = updated_state.values.get("article_content", "")
                app_logger.draft_generated(
                    thread_id=thread_id,
                    word_count=len(article_content)
                )
            elif action_required == "select_topic":
                message = "请选择选题"
            elif action_required == "image_review":
                message = "配图已生成，请审核"
            else:
                message = "等待用户操作"
        
        return ResumeWorkflowResponse(
            thread_id=thread_id,
            status=updated_state.values.get("status", "unknown"),
            message=message,
            next_nodes=next_nodes,
            is_completed=is_completed,
            result=final_result,
            interrupt_info=interrupt_info,
            node_metrics=node_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.workflow_error(
            thread_id=thread_id,
            error=str(e),
            stage="resume"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复工作流失败: {str(e)}"
        )


@router.get("/export/{thread_id}")
async def export_publish_package(
    thread_id: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    """导出标题、文案、标签和配图组成的 ZIP 发布包。"""
    if not thread_id.startswith(f"{current_user.id}_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权导出此工作流",
        )

    try:
        graph = await get_graph()
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = await graph.aget_state(config)
        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到工作流",
            )

        values = state_snapshot.values
        title = (values.get("selected_topic") or values.get("topic_direction") or "未命名内容").strip()
        topic_direction = (values.get("topic_direction") or "").strip()
        article_content = (values.get("article_content") or "").strip()
        image_urls = [url for url in (values.get("image_urls") or []) if url]
        visual_points = values.get("visual_points") or []
        if not article_content:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="文章尚未生成，暂时无法导出发布包",
            )
        if not image_urls:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="配图尚未生成，暂时无法导出发布包",
            )

        tags = _build_publish_tags(title, topic_direction, article_content)
        hashtag_line = " ".join(f"#{tag}" for tag in tags)
        plain_content = _strip_markdown_for_publish(article_content)
        project_root = Path(__file__).resolve().parents[3]
        static_root = (project_root / "static").resolve()
        image_roles = ["封面图", "场景图", "细节图"]
        packaged_images = []

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("发布包/01_标题.txt", _safe_package_text(title))
            archive.writestr("发布包/02_文案.md", _safe_package_text(article_content))
            archive.writestr("发布包/03_发布文案.txt", _safe_package_text(plain_content))
            archive.writestr("发布包/04_标签.txt", _safe_package_text(hashtag_line))

            for index, image_url in enumerate(image_urls):
                clean_url = image_url.split("?", 1)[0]
                if not clean_url.startswith("/static/"):
                    continue
                image_path = (project_root / clean_url.lstrip("/")).resolve()
                if not image_path.is_relative_to(static_root) or not image_path.is_file():
                    continue
                suffix = image_path.suffix.lower()
                if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                    suffix = ".png"
                role = image_roles[index] if index < len(image_roles) else f"配图{index + 1}"
                archive_name = f"发布包/图片/{index + 1:02d}_{role}{suffix}"
                archive.writestr(archive_name, image_path.read_bytes())
                packaged_images.append({
                    "order": index + 1,
                    "role": role,
                    "filename": archive_name,
                    "visual_point": visual_points[index] if index < len(visual_points) else "",
                })

            if not packaged_images:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="没有找到可打包的本地配图",
                )

            checklist = (
                f"标题：{title}\n\n"
                f"标签：{hashtag_line}\n\n"
                f"图片数量：{len(packaged_images)} 张，请按文件名前的序号发布。\n\n"
                "发布前检查：\n"
                "1. 核对文案中的数据、案例与专业结论。\n"
                "2. 确认图片无文字错误、Logo、水印和版权风险。\n"
                "3. 根据目标平台调整标题长度、标签数量与图片裁切。\n"
                "4. 人工确认无误后再发布。\n"
            )
            archive.writestr("发布包/05_发布清单.txt", _safe_package_text(checklist))
            manifest = {
                "thread_id": thread_id,
                "title": title,
                "topic_direction": topic_direction,
                "tags": tags,
                "image_model": values.get("image_model", ""),
                "image_count": len(packaged_images),
                "images": packaged_images,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
            archive.writestr(
                "发布包/manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            )

        short_id = thread_id.rsplit("_", 1)[-1][:8]
        return Response(
            content=buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="publish-package-{short_id}.zip"',
                "Cache-Control": "no-store",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出发布包失败: {str(e)}",
        )


@router.get("/history/{thread_id}")
async def get_workflow_history(
    thread_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取工作流的历史状态记录
    
    Args:
        thread_id: 工作流线程ID
        
    Returns:
        历史状态列表
    """
    try:
        # 验证 thread_id 属于当前用户
        if not thread_id.startswith(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此工作流"
            )
        
        # 获取编译后的图
        graph = await get_graph()
        
        # 配置
        config = {"configurable": {"thread_id": thread_id}}
        
        # 获取历史状态
        history = []
        async for state in graph.aget_state_history(config):
            history.append({
                "config": state.config,
                "values": dict(state.values) if state.values else {},
                "next": list(state.next) if state.next else [],
                "created_at": state.created_at if hasattr(state, "created_at") else None,
            })
        
        return {
            "thread_id": thread_id,
            "history": history[:20],  # 限制返回最近 20 条
            "total": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流历史失败: {str(e)}"
        )


@router.get("/threads", response_model=ThreadListResponse)
async def get_all_threads(
    current_user: User = Depends(get_current_user)
) -> ThreadListResponse:
    """
    获取所有工作流线程列表
    
    Returns:
        线程列表，包含每个线程的基本信息
    """
    try:
        threads = []
        
        # 从 PostgreSQL 数据库查询
        async with await psycopg.AsyncConnection.connect(
            settings.postgres_uri,
            autocommit=True
        ) as conn:
            async with conn.cursor() as cur:
                # 查询当前用户的 thread_id（根据用户ID前缀过滤）
                user_id_prefix = f"{current_user.id}_%"
                await cur.execute("""
                    SELECT DISTINCT thread_id 
                    FROM checkpoints 
                    WHERE thread_id LIKE %s
                    ORDER BY thread_id
                """, (user_id_prefix,))
                rows = await cur.fetchall()
                
                graph = await get_graph()
                
                for row in rows:
                    thread_id = row[0]
                    config = {"configurable": {"thread_id": thread_id}}
                    try:
                        state_snapshot = await graph.aget_state(config)
                        if state_snapshot and state_snapshot.values:
                            values = state_snapshot.values
                            next_nodes = list(state_snapshot.next) if state_snapshot.next else []
                            interrupt_info = extract_interrupt_info(state_snapshot)
                            is_completed = len(next_nodes) == 0 and not interrupt_info
                            
                            # 获取创建时间
                            created_at = None
                            if hasattr(state_snapshot, 'created_at') and state_snapshot.created_at:
                                created_at = state_snapshot.created_at
                            
                            threads.append(ThreadInfo(
                                thread_id=thread_id,
                                topic_direction=values.get("topic_direction", ""),
                                selected_topic=values.get("selected_topic", ""),
                                status=values.get("status", "unknown"),
                                is_completed=is_completed,
                                created_at=created_at
                            ))
                    except Exception:
                        continue
        
        return ThreadListResponse(
            threads=threads,
            total=len(threads)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取线程列表失败: {str(e)}"
        )


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    删除指定的工作流线程
    
    Args:
        thread_id: 工作流线程ID
        
    Returns:
        删除结果
    """
    try:
        # 验证 thread_id 属于当前用户
        if not thread_id.startswith(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此工作流"
            )
        
        # 从 PostgreSQL 数据库删除
        async with await psycopg.AsyncConnection.connect(
            settings.postgres_uri,
            autocommit=True
        ) as conn:
            async with conn.cursor() as cur:
                # 删除相关记录
                await cur.execute(
                    "DELETE FROM checkpoint_writes WHERE thread_id = %s",
                    (thread_id,)
                )
                await cur.execute(
                    "DELETE FROM checkpoint_blobs WHERE thread_id = %s",
                    (thread_id,)
                )
                await cur.execute(
                    "DELETE FROM checkpoints WHERE thread_id = %s",
                    (thread_id,)
                )
                
                return {"success": True, "message": f"线程 {thread_id} 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除线程失败: {str(e)}"
        )


# ============== SSE 流式输出请求模型 ==============
# 注意：流式输出仅用于文章生成场景（select_topic 和 reject 操作）
# 选题阶段和审核通过阶段不需要流式，请使用普通接口

class StreamResumeWorkflowRequest(BaseModel):
    """
    流式恢复工作流请求
    
    支持需要实时进度的操作：
    - select_topic: 选择选题后生成文章（需要流式）
    - reject: 驳回后重新生成文章（需要流式）
    - approve: 审核通过后提取视觉要点并生成配图
    """
    action: WorkflowAction = Field(
        ..., 
        description="操作类型：select_topic(选择选题后生成文章)、approve(审核通过生成配图)、reject(驳回后重新生成文章)、approve_images(通过配图)、regenerate_image(局部重生成配图)、generate_missing_images(补齐缺失配图)"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="操作数据，select_topic时需要selected_topic，reject时可提供feedback，regenerate_image时需要index/feedback"
    )


# ============== SSE 流式输出 API (使用官方 graph.astream) ==============

def format_sse_event(event_type: str, data: Any) -> str:
    """
    将事件格式化为SSE格式
    
    Args:
        event_type: 事件类型
        data: 事件数据
        
    Returns:
        SSE格式字符串
    """
    payload = {
        "type": event_type,
        "data": data
    }
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


async def stream_graph_updates(
    graph, 
    input_data: Any, 
    config: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    使用 LangGraph astream_events 流式输出文章生成过程
    
    专门用于文章生成场景，提供 token 级别的流式输出
    
    Args:
        graph: 编译后的图
        input_data: 输入数据 (Command 对象)
        config: 配置 (包含 thread_id)
        
    Yields:
        SSE格式的事件字符串
    """
    try:
        # 发送开始事件
        yield format_sse_event("start", {})
        
        # 用于收集 token 统计
        token_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
        workflow_nodes = {
            "topic_selection",
            "plan_topics",
            "human_select_topic",
            "write_draft",
            "human_review",
            "extract_visuals",
            "generate_images",
            "human_image_review",
        }

        active_llm_models: set[str] = set()
        active_task_names: set[str] = set()

        # 使用 astream 获取任务、custom 进度和 messages token 输出
        async for mode, payload in graph.astream(
            input_data,
            config,
            stream_mode=["updates", "custom", "messages", "tasks"],
        ):
            if mode == "tasks":
                if isinstance(payload, dict):
                    task_name = payload.get("name", "")
                    if task_name in workflow_nodes and "input" in payload and "result" not in payload:
                        active_task_names.add(task_name)
                        yield format_sse_event("node_start", {
                            "node": task_name,
                            "input": payload.get("input", {}),
                        })
                    elif task_name in workflow_nodes and "result" in payload:
                        active_task_names.discard(task_name)
                        output = payload.get("result", {})
                        yield format_sse_event("node_end", {
                            "node": task_name,
                            "output": output if isinstance(output, dict) else {},
                        })

            elif mode == "custom":
                if isinstance(payload, dict):
                    event_type = payload.get("type")
                    if event_type:
                        yield format_sse_event(event_type, payload)

            elif mode == "messages":
                if isinstance(payload, tuple) and len(payload) >= 1:
                    chunk = payload[0]
                    metadata = payload[1] if len(payload) > 1 and isinstance(payload[1], dict) else {}
                    if metadata and metadata.get("langgraph_node") and metadata["langgraph_node"] in workflow_nodes:
                        model_name = metadata.get("ls_model_name") or metadata.get("model_name") or metadata.get("langgraph_node")
                        if metadata["langgraph_node"] not in active_llm_models:
                            active_llm_models.add(metadata["langgraph_node"])
                            yield format_sse_event("llm_start", {
                                "model": model_name
                            })

                    if hasattr(chunk, "content") and chunk.content:
                        yield format_sse_event("llm_token", {
                            "content": chunk.content
                        })

                    if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                        usage_info = {
                            "input_tokens": chunk.usage_metadata.get("input_tokens", 0),
                            "output_tokens": chunk.usage_metadata.get("output_tokens", 0),
                            "total_tokens": chunk.usage_metadata.get("total_tokens", 0),
                        }
                        token_stats.update(usage_info)

            elif mode == "updates":
                if isinstance(payload, dict):
                    for node_name, output in payload.items():
                        if node_name in workflow_nodes and isinstance(output, dict):
                            yield format_sse_event("node_end", {
                                "node": node_name,
                                "output": output,
                            })
        
        # 获取最终状态
        final_state = await graph.aget_state(config)
        interrupt_info = extract_interrupt_info(final_state)
        next_nodes = list(final_state.next) if final_state.next else []
        is_completed = len(next_nodes) == 0 and not interrupt_info
        
        # 发送完成事件
        yield format_sse_event("done", {
            "status": final_state.values.get("status", "unknown") if final_state.values else "unknown",
            "next_nodes": next_nodes,
            "is_completed": is_completed,
            "interrupt_info": interrupt_info,
            "values": dict(final_state.values) if final_state.values else {}
        })
        
    except Exception as e:
        # 发送错误事件
        yield format_sse_event("error", {"message": str(e)})


@router.post("/stream/start")
async def stream_start_workflow(
    request: StartWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    流式启动工作流 - 用于选题阶段

    返回节点开始/结束事件、LLM 事件和最终状态。
    """
    thread_id = f"{current_user.id}_{uuid.uuid4()}"

    async def generate():
        try:
            graph = await get_graph()
            config = {"configurable": {"thread_id": thread_id}}
            initial_input = {
                **INITIAL_STATE,
                "topic_direction": request.topic_direction,
                "status": "started",
            }

            yield format_sse_event("init", {"thread_id": thread_id})
            async for event in stream_graph_updates(graph, initial_input, config):
                yield event
        except Exception as e:
            yield format_sse_event("error", {"message": str(e)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/stream/resume/{thread_id}")
async def stream_resume_workflow(
    thread_id: str, 
    request: StreamResumeWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    流式恢复工作流 - 用于文章生成和配图生成场景
    
    使用 Server-Sent Events (SSE) 实时返回 LLM 生成的文章内容（token 级别流式输出）
    
    支持的操作：
    - select_topic: 选择选题后，流式生成文章
    - reject: 驳回审核后，流式重新生成文章
    - approve: 审核通过后，流式返回提取视觉要点和生成配图进度
    
    事件类型说明：
    - resume: 恢复开始
    - node_start: 节点开始
    - node_end: 节点结束
    - llm_start: LLM 开始生成
    - llm_token: LLM 输出的每个 token（文章内容逐字输出）
    - llm_end: LLM 生成完成，包含 token 统计
    - done: 工作流阶段完成
    - error: 错误信息
    """
    # 验证 thread_id 属于当前用户
    if not thread_id.startswith(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此工作流"
        )
    
    async def generate():
        try:
            # 获取编译后的图
            graph = await get_graph()
            
            # 配置
            config = {"configurable": {"thread_id": thread_id}}
            
            # 获取当前状态
            current_state = await graph.aget_state(config)
            
            if current_state is None or current_state.values is None:
                yield format_sse_event("error", {"message": f"未找到工作流: {thread_id}"})
                return
            
            # 根据操作类型构建 resume 数据
            resume_value: Dict[str, Any] = {}
            
            if request.action == "select_topic":
                if not request.data or "selected_topic" not in request.data:
                    yield format_sse_event("error", {"message": "选择选题需要提供 selected_topic"})
                    return
                resume_value = {
                    "selected_topic": request.data["selected_topic"],
                }

            elif request.action == "approve":
                resume_value = {
                    "action": "approve",
                }

            elif request.action == "reject":
                feedback = request.data.get("feedback", "") if request.data else ""
                resume_value = {
                    "action": "reject",
                    "feedback": feedback,
                }

            elif request.action == "approve_images":
                resume_value = {
                    "action": "approve_images",
                }

            elif request.action == "generate_missing_images":
                resume_value = {
                    "action": "generate_missing_images",
                }

            elif request.action == "regenerate_image":
                if not request.data or "index" not in request.data:
                    yield format_sse_event("error", {"message": "重生成配图需要提供 index"})
                    return
                resume_value = {
                    "action": "regenerate_image",
                    "index": request.data["index"],
                    "feedback": request.data.get("feedback", ""),
                }
            
            # 使用 Command 恢复工作流
            resume_command = Command(resume=resume_value)
            
            # 发送恢复信息
            yield format_sse_event("resume", {
                "thread_id": thread_id,
                "action": request.action
            })
            
            # 流式输出文章生成过程
            async for event in stream_graph_updates(graph, resume_command, config):
                yield event
                
        except Exception as e:
            yield format_sse_event("error", {"message": str(e)})
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
