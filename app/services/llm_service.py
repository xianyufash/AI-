"""
LLM 服务模块
使用阿里百炼 OpenAI 兼容 API 进行 LLM 调用
支持流式输出和结构化输出
"""
import os
import re
from typing import List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessageChunk
from pydantic import BaseModel, Field

load_dotenv()


def _get_pii_callback():
    """获取 PII 脱敏回调（延迟导入避免循环依赖）"""
    try:
        from app.core.callbacks import pii_callback
        return pii_callback
    except ImportError:
        return None


# ============== Pydantic 模型 ==============

class TopicItem(BaseModel):
    """单个选题项"""
    title: str = Field(..., description="选题标题")


class TopicsResponse(BaseModel):
    """选题响应结构"""
    topics: List[TopicItem] = Field(..., description="生成的选题列表")


@dataclass
class LLMUsageInfo:
    """LLM 调用的 token 使用信息"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


@dataclass
class StreamResult:
    """流式输出结果"""
    content: str = ""
    usage: LLMUsageInfo = field(default_factory=LLMUsageInfo)


class LLMService:
    """LLM 服务类 - 使用阿里百炼 OpenAI 兼容 API"""
    
    # ============== Prompt 模板 ==============
    
    TOPIC_SYSTEM_PROMPT = """你是小红书10w+爆款标题专家，精通平台流量密码。

根据主题方向生成5个超有吸引力的爆款选题标题。

【爆款标题公式】
1. 数字+痛点："3个方法让我..." "5分钟搞定..."
2. 悬念反转："原来xx这么简单" "后悔没早知道"
3. 情绪共鸣："救命！" "绝了！" "真的会谢"
4. 身份代入："打工人必看" "新手小白"
5. 对比冲击："花了3000学的vs我自己琢磨的"

【标题要求】
- 15字以内，一眼抓住注意力
- 口语化、接地气，像朋友聊天
- 用感叹号、问号增加情绪张力
- 可用 emoji 点缀（如🔥💡✨）"""

    ARTICLE_SYSTEM_PROMPT = """你是小红书爆款文章创作者。

文章要求：
- 开头抓人：用故事/问题/数据引入
- 干货满满：提供可操作的价值
- 语言活泼：口语化，适当用emoji
- 结构清晰：分段合理，善用小标题
- 800-1200字
- 结尾互动：提问引导评论

直接输出Markdown格式文章。"""

    VISUAL_SYSTEM_PROMPT = """你是小红书配图导演，负责把文章内容转成可直接用于 AI 生图的画面 brief。

请先完整理解选题、正文观点、目标读者、具体案例、方法步骤和情绪，再生成3个互相配合、但主体和构图明显不同的配图描述。

格式要求：
- 严格输出4行，依次为：系列设定、封面图、场景图、细节图
- 系列设定必须包含：统一主色、统一材质/摄影或插画语言、统一光线；人物不是系列统一的必要条件，只有正文确实需要人物时才描述人物卡
- 每行必须以对应标签开头，不编号，不加解释
- 每一张图都必须绑定正文中的不同段落，不能三张都只解释标题
- 每一行都必须包含：正文依据、核心含义、不可替代元素、画面转译、构图、色彩、质感/风格、情绪氛围
- “正文依据”必须逐字摘录正文中真实存在的8至30字短句，仅用于程序定位对应段落，不会画在图片里
- “核心含义”用一句话说明这张图到底在解释正文的哪个观点、案例、步骤或结果
- “不可替代元素”必须列出3个来自对应正文段落、可以被画出来的具体人物/物件/动作/空间关系；删掉其中任何一个都会让图片失去这篇文章的独特含义
- 不可替代元素禁止使用“科技感、AI光效、办公桌、电脑、咖啡、抽象节点、卡片”这类通用词单独充数；如正文确实需要，必须补充其独特内容、排列方式或人物动作
- 封面图（人物/故事主视觉）：把文章最核心的冲突、变化或结论转成强视觉画面，负责吸引点击；允许出现完整人物，但禁止普通的“人物坐在桌前看电脑”构图
- 场景图（方法/流程配套图）：优先选择正文中段的具体案例、步骤或工作流程，让读者一眼看懂“事情如何发生”；优先俯拍、手部动作、实体物件或空间流程，尽量不出现完整人物，禁止再次画人物坐在办公桌前
- 细节图（成果/证据配套图）：优先选择正文中的结果、前后变化、关键物件或容易忽略的细节；以物件特写、前后对照、结果陈列或局部动作作为主体，不出现完整人物，不能只是封面或场景图的近景复制
- 三张图的主视觉主体必须分别属于“人物/故事、方法/流程、成果/细节”三种类型；禁止三张图都以同一人物为最大主体，禁止三张图都出现电脑桌，禁止只改变机位或背景
- 三张图至少使用两种明显不同的镜头语言（如人物中景、俯拍流程、物件特写、前后对照），且至少一张不出现人物
- 三张图必须像同一组作品：只统一主色调、材质、光线和插画/摄影语言，不要为了系列感强行重复人物、桌面、电脑或同一空间
- 风格必须匹配文案：教程干货偏清爽专业，成长职场偏真实温暖，生活分享偏自然松弛，观点类偏有隐喻和记忆点
- 避免套用通用咖啡、书本、电脑桌，除非正文确实需要
- 画面必须让没看正文的人也能看出这个具体案例或方法，而不只是看出“有人在工作”“这是AI主题”
- 优先使用正文真正提到的人、物、地点、动作和关系；不得凭空添加课程、商品、品牌、收益数字或文章没有承诺的效果
- 禁止画面出现可读文字、logo、水印、二维码、品牌视觉、敏感政治暴力内容
- brief 中禁止出现“屏幕显示某软件/标题/表格/文字”之类描述，不得写具体软件或平台名称；电子设备只能背对镜头、侧放、熄屏或严重虚化
- 如果是AI/编程/工具类文章，用人物移动实体卡片、连接抽象节点、整理无字便签、推动可视化流程等视觉隐喻，不要依赖电脑屏幕，不要真实软件截图、表格界面或可读界面文字

输出示意（只说明结构，不可照抄内容）：
系列设定：固定人物卡……；统一主色……；统一材质与风格……；统一光线……
封面图：主体类型“人物/故事主视觉”；正文依据“……”；核心含义“……”；不可替代元素[……、……、……]；画面转译……；构图……；色彩、质感与情绪……
场景图：主体类型“方法/流程配套图”；正文依据“……”；核心含义“……”；不可替代元素[……、……、……]；画面转译……；构图……；色彩、质感与情绪……
细节图：主体类型“成果/证据配套图”；正文依据“……”；核心含义“……”；不可替代元素[……、……、……]；画面转译……；构图……；色彩、质感与情绪……

直接输出四行，不要输出其他内容。"""

    VISUAL_BRIEF_REPLACEMENTS = [
        (r"(?:电脑|手机|平板)?屏幕(?:上)?显示[^；。\n]*", "电子设备背对镜头，相关信息用无字实体卡片和抽象节点表达"),
        (r"(?:电脑|手机|平板)?屏幕(?:界面)?虚化", "背对镜头的电子设备呈纯色虚化光面"),
        (r"(?:电脑|手机|平板)屏幕", "背对镜头的电子设备"),
        (r"屏幕", "背对镜头的纯色设备光面"),
        (r"(?:真实)?软件界面", "抽象无字卡片与节点"),
        (r"界面|页面", "无字实体工具卡"),
        (r"(?:手机)?(?:突然)?弹出(?:一条)?消息", "设备亮起无字彩色提示光"),
        (r"\bprompt\b|提示词", "无字任务卡组合"),
        (r"截图", "抽象无字视觉卡片"),
        (r"质检表", "质检卡片阵列"),
        (r"小红书", "内容社区"),
        (r"ChatGPT|Claude|通义千问|Qwen|豆包|DeepSeek", "智能助手"),
        (r"抖音", "短视频平台"),
        (r"Notion(?:界面|看板)?", "无字协作看板"),
        (r"新抖|蝉妈妈", "数据分析工具"),
        (r"\b[A-Za-z][A-Za-z0-9.-]{2,}\b", "智能工具"),
    ]

    def __init__(self, enable_pii_anonymize: bool = True):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        # 模型配置
        self.model = os.getenv("LLM_MODEL", "qwen-plus")
        self.model_fast = os.getenv("LLM_MODEL_FAST", "qwen-turbo")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.temperature_fast = float(os.getenv("LLM_TEMPERATURE_FAST", "0.7"))
        self.temperature_extract = float(os.getenv("LLM_TEMPERATURE_EXTRACT", "0.4"))
        
        self.enable_pii_anonymize = enable_pii_anonymize
        self._llm = None
        self._llm_fast = None
        self._llm_extract = None
        
        print(f"[LLM] 模型配置: 标准={self.model}, 快速={self.model_fast}")
    
    def _get_callbacks(self) -> List:
        """获取回调列表"""
        if self.enable_pii_anonymize:
            pii_callback = _get_pii_callback()
            if pii_callback:
                return [pii_callback]
        return []
    
    def _create_llm(self, model: str, temperature: float) -> ChatOpenAI:
        """创建 LLM 客户端"""
        callbacks = self._get_callbacks()
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=self.api_key,
            base_url=self.base_url,
            callbacks=callbacks if callbacks else None,
        )

    @staticmethod
    def _build_visual_article_context(article_content: str, max_chars: int = 3600) -> str:
        """保留正文开头、中段和结尾，避免视觉提取只看到导语。"""
        content = article_content.strip()
        content = re.sub(r"```[\s\S]*?```", "\n[代码示例]\n", content)
        content = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", content)
        content = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", content)
        content = re.sub(r"(?m)^\s*>\s?", "", content)
        content = re.sub(r"[*_~`]", "", content)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()
        if len(content) <= max_chars:
            return content

        head_len = int(max_chars * 0.4)
        middle_len = int(max_chars * 0.3)
        tail_len = max_chars - head_len - middle_len
        middle_start = max(head_len, (len(content) - middle_len) // 2)
        return (
            f"【正文开头】\n{content[:head_len]}\n\n"
            f"【正文中段】\n{content[middle_start:middle_start + middle_len]}\n\n"
            f"【正文结尾】\n{content[-tail_len:]}"
        )

    @classmethod
    def _sanitize_visual_brief(cls, brief: str) -> str:
        """确定性清理容易诱发品牌、文字和软件界面的画面描述。"""
        cleaned = brief.strip()
        for pattern, replacement in cls.VISUAL_BRIEF_REPLACEMENTS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", cleaned).strip()
    
    @property
    def llm(self) -> ChatOpenAI:
        """标准 LLM（文章写作）"""
        if self._llm is None:
            self._llm = self._create_llm(self.model, self.temperature)
        return self._llm
    
    @property
    def llm_fast(self) -> ChatOpenAI:
        """快速 LLM（选题生成）"""
        if self._llm_fast is None:
            self._llm_fast = self._create_llm(self.model_fast, self.temperature_fast)
        return self._llm_fast
    
    @property
    def llm_extract(self) -> ChatOpenAI:
        """提取用 LLM（低 temperature）"""
        if self._llm_extract is None:
            self._llm_extract = self._create_llm(self.model_fast, self.temperature_extract)
        return self._llm_extract
    
    def _extract_usage_info(self, response, model: str = "") -> LLMUsageInfo:
        """从 LLM 响应中提取 token 使用信息"""
        usage = LLMUsageInfo(model=model or self.model)
        
        if hasattr(response, 'response_metadata'):
            token_usage = response.response_metadata.get('token_usage', {})
            usage.input_tokens = token_usage.get('prompt_tokens', 0)
            usage.output_tokens = token_usage.get('completion_tokens', 0)
            usage.total_tokens = token_usage.get('total_tokens', 0)
        
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage.input_tokens = response.usage_metadata.get('input_tokens', usage.input_tokens)
            usage.output_tokens = response.usage_metadata.get('output_tokens', usage.output_tokens)
            usage.total_tokens = response.usage_metadata.get('total_tokens', usage.total_tokens)
        
        return usage
    
    def _update_usage_from_chunk(self, chunk: AIMessageChunk, usage: LLMUsageInfo) -> None:
        """从流式 chunk 更新 token 统计"""
        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
            usage.input_tokens = chunk.usage_metadata.get('input_tokens', usage.input_tokens)
            usage.output_tokens = chunk.usage_metadata.get('output_tokens', usage.output_tokens)
            usage.total_tokens = chunk.usage_metadata.get('total_tokens', usage.total_tokens)
        
        if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
            token_usage = chunk.response_metadata.get('token_usage', {})
            if token_usage:
                usage.input_tokens = token_usage.get('prompt_tokens', usage.input_tokens)
                usage.output_tokens = token_usage.get('completion_tokens', usage.output_tokens)
                usage.total_tokens = token_usage.get('total_tokens', usage.total_tokens)

    # ============== 核心方法 ==============

    async def plan_topics(self, topic_direction: str) -> Tuple[TopicsResponse, LLMUsageInfo]:
        """根据主题方向生成候选选题（结构化输出）"""
        messages = [
            SystemMessage(content=self.TOPIC_SYSTEM_PROMPT),
            HumanMessage(content=f"主题：{topic_direction or '技术分享'}")
        ]
        
        usage = LLMUsageInfo(model=self.model_fast)
        
        try:
            structured_llm = self.llm_fast.with_structured_output(TopicsResponse, include_raw=True)
            result = await structured_llm.ainvoke(messages)
            
            raw_response = result.get('raw')
            parsed_response = result.get('parsed')
            
            if raw_response:
                usage = self._extract_usage_info(raw_response, self.model_fast)
                
        except Exception as e:
            print(f"[LLM] 结构化输出失败，使用备用方案: {e}")
            return await self._plan_topics_fallback(topic_direction)
        
        return parsed_response or TopicsResponse(topics=[]), usage
    
    async def _plan_topics_fallback(self, topic_direction: str) -> Tuple[TopicsResponse, LLMUsageInfo]:
        """备用方案：手动解析 JSON"""
        import json
        
        system_prompt = self.TOPIC_SYSTEM_PROMPT + '\n\nJSON格式输出：{"topics":[{"title":"标题1"},...,{"title":"标题5"}]}'
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"主题：{topic_direction or '技术分享'}")
        ]
        
        response = await self.llm_fast.ainvoke(messages)
        usage = self._extract_usage_info(response, self.model_fast)
        
        try:
            content = response.content.strip()
            # 提取 JSON 部分
            if "```" in content:
                content = re.sub(r'^.*?```(?:json)?\s*', '', content, flags=re.DOTALL)
                content = re.sub(r'\s*```.*$', '', content, flags=re.DOTALL)
            
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start != -1 and json_end != -1:
                content = content[json_start:json_end + 1]
            
            data = json.loads(content)
            return TopicsResponse(**data), usage
        except Exception as e:
            print(f"[LLM] JSON 解析失败: {e}")
            return TopicsResponse(topics=[]), usage
    
    async def write_draft(
        self,
        topic: str,
        feedback: str = "",
        revision_count: int = 0
    ) -> Tuple[str, LLMUsageInfo]:
        """生成文章草稿（非流式）"""
        user_prompt = self._build_article_prompt(topic, feedback, revision_count)
        
        messages = [
            SystemMessage(content=self.ARTICLE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        usage = self._extract_usage_info(response)
        
        return response.content, usage

    async def stream_write_draft_with_usage(
        self,
        topic: str,
        feedback: str = "",
        revision_count: int = 0,
        on_chunk: Optional[Callable[[str], Any]] = None
    ) -> StreamResult:
        """流式生成文章草稿（带 token 统计）"""
        user_prompt = self._build_article_prompt(topic, feedback, revision_count)
        
        messages = [
            SystemMessage(content=self.ARTICLE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        full_content = ""
        usage = LLMUsageInfo(model=self.model)
        
        async for chunk in self.llm.astream(messages):
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    full_content += chunk.content
                    if on_chunk:
                        on_chunk(chunk.content)
                self._update_usage_from_chunk(chunk, usage)
        
        # 估算 token（如果 API 未返回）
        if usage.total_tokens == 0:
            usage.input_tokens = len(self.ARTICLE_SYSTEM_PROMPT + user_prompt) // 2
            usage.output_tokens = len(full_content) // 2
            usage.total_tokens = usage.input_tokens + usage.output_tokens
        
        return StreamResult(content=full_content, usage=usage)
    
    async def extract_visual_points(
        self,
        article_content: str,
        selected_topic: str = "",
        topic_direction: str = "",
    ) -> Tuple[List[str], LLMUsageInfo]:
        """从文章中提取配图要点"""
        article_context = self._build_visual_article_context(article_content)
        
        messages = [
            SystemMessage(content=self.VISUAL_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"主题方向：{topic_direction or '未提供'}\n"
                f"选题标题：{selected_topic or '未提供'}\n\n"
                f"文章内容：\n{article_context}"
            ))
        ]
        
        response = await self.llm_extract.ainvoke(messages)
        usage = self._extract_usage_info(response, self.model_fast)
        
        # 解析响应，清理编号前缀，并把同一系列设定注入每个画面 brief。
        series_setting = ""
        points = []
        for line in response.content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('-'):
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned.startswith("系列设定："):
                    series_setting = self._sanitize_visual_brief(cleaned.split("：", 1)[1])
                elif cleaned.startswith(("封面图：", "场景图：", "细节图：")):
                    points.append(self._sanitize_visual_brief(cleaned))

        if not series_setting:
            series_setting = (
                "统一主色、材质、光线与艺术语言；三张图不强制重复人物、桌面或空间；"
                "所有电子屏幕背对镜头、熄屏或纯色虚化"
            )

        enriched_points = []
        for point in points[:3]:
            label, content = point.split("：", 1)
            enriched_points.append(f"{label}：系列设定“{series_setting}”；{content}")
        
        return enriched_points, usage
    
    def _build_article_prompt(self, topic: str, feedback: str, revision_count: int) -> str:
        """构建文章生成的用户提示"""
        if feedback and revision_count > 0:
            return f"选题：{topic}\n\n第{revision_count}次修订，修改意见：{feedback}\n\n请针对性修改。"
        return f"选题：{topic}"


# 单例实例
llm_service = LLMService()
