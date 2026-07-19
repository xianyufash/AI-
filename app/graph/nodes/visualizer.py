"""
视觉内容生成节点
负责从文章中提取配图要点并生成图片
"""
import asyncio
from typing import Dict, Any
from datetime import datetime
from langgraph.config import get_stream_writer
from app.graph.state import AgentState
from app.services import get_llm_service, get_image_service
from app.graph.metrics import MetricsContext, LLMUsage, merge_metrics


async def extract_visuals_node(state: AgentState) -> Dict[str, Any]:
    """
    提取视觉要点节点
    
    从文章内容中提取适合配图的要点
    
    Args:
        state: 当前工作流状态
        
    Returns:
        更新后的状态字段
    """
    article_content = state.get("article_content", "")
    selected_topic = state.get("selected_topic", "")
    topic_direction = state.get("topic_direction", "")
    existing_metrics = state.get("node_metrics", [])
    
    if not article_content:
        return {
            "visual_points": [],
            "status": "error",
            "error": "文章内容为空，无法提取视觉要点",
        }
    
    with MetricsContext("extract_visuals") as tracker:
        try:
            # 获取 LLM 服务
            llm_service = get_llm_service()
            visual_points, usage_info = await llm_service.extract_visual_points(
                article_content,
                selected_topic=selected_topic,
                topic_direction=topic_direction,
            )
            
            # 记录 LLM 使用信息
            tracker.set_llm_usage(LLMUsage(
                input_tokens=usage_info.input_tokens,
                output_tokens=usage_info.output_tokens,
                total_tokens=usage_info.total_tokens,
                model=usage_info.model
            ))
            
            result = {
                "visual_points": visual_points,
                "status": "visuals_extracted",
                "error": "",
            }
            
        except Exception as e:
            result = {
                "visual_points": [],
                "status": "error",
                "error": f"提取视觉要点失败: {str(e)}",
            }
    
    # 在 with 块结束后（tracker.stop() 已被调用），再获取指标
    result["node_metrics"] = merge_metrics(existing_metrics, tracker.to_dict())
    return result


async def generate_images_node(state: AgentState) -> Dict[str, Any]:
    """
    生成配图节点
    
    根据视觉要点生成配图（部分失败时仍会返回成功的图片）
    
    Args:
        state: 当前工作流状态
        
    Returns:
        更新后的状态字段
    """
    visual_points = state.get("visual_points", [])
    article_context = state.get("article_content", "")
    topic = state.get("selected_topic") or state.get("topic_direction", "")
    image_urls = list(state.get("image_urls", []))
    image_history = list(state.get("image_history", []))
    regeneration_request = state.get("image_regeneration_request", {}) or {}
    regeneration_count = int(state.get("image_regeneration_count", 0) or 0)
    existing_metrics = state.get("node_metrics", [])
    stream_writer = get_stream_writer()

    def emit_image_progress(payload: Dict[str, Any]) -> None:
        stream_writer({
            "type": "image_progress",
            **payload,
        })
    
    if not visual_points:
        emit_image_progress({
            "event": "image_skipped",
            "completed": 0,
            "total": 0,
            "message": "视觉要点为空，跳过配图生成",
        })
        return {
            "image_urls": image_urls,
            "image_model": "",
            "status": "images_generated",
            "error": "视觉要点为空，跳过配图生成",
            "image_review_status": "pending",
            "image_review_feedback": "",
            "image_regeneration_request": {},
            "image_regeneration_count": regeneration_count,
            "image_history": image_history,
        }
    
    with MetricsContext("generate_images") as tracker:
        try:
            # 获取图片服务
            image_service = get_image_service()
            series_context = "\n".join(
                f"第{index + 1}张：{point}"
                for index, point in enumerate(visual_points[:getattr(image_service, "max_images", len(visual_points))])
            )
            target_index = regeneration_request.get("index")
            fill_missing = regeneration_request.get("mode") == "fill_missing"
            target_feedback = (regeneration_request.get("feedback") or "").strip()

            if fill_missing:
                target_total = min(len(visual_points), getattr(image_service, "max_images", len(visual_points)))
                while len(image_urls) < target_total:
                    image_urls.append("")
                missing_indexes = [
                    index
                    for index in range(target_total)
                    if not image_urls[index]
                ]

                async def generate_missing_one(index: int) -> tuple[int, str | None]:
                    point = visual_points[index]
                    emit_image_progress({
                        "event": "image_start",
                        "index": index,
                        "total": target_total,
                        "visual_point": point,
                        "message": f"正在补齐第 {index + 1} 张配图",
                    })
                    url = await image_service.generate_single_image(
                        point,
                        article_context=article_context,
                        topic=topic,
                        image_role=(point.split("：", 1)[0] if "：" in point else f"第{index + 1}张配图"),
                        series_context=series_context,
                    )
                    emit_image_progress({
                        "event": "image_done" if url else "image_failed",
                        "index": index,
                        "total": target_total,
                        "url": url,
                        "visual_point": point,
                    })
                    return index, url

                if missing_indexes:
                    results = await asyncio.gather(
                        *(generate_missing_one(index) for index in missing_indexes)
                    )
                    for index, url in results:
                        if url:
                            image_urls[index] = url

                completed_count = len([url for url in image_urls[:target_total] if url])
                if completed_count < target_total:
                    error_msg = f"部分配图补齐失败 ({completed_count}/{target_total} 成功)"
                else:
                    error_msg = ""
                status = "images_generated"

            elif isinstance(target_index, int) and 0 <= target_index < len(visual_points):
                prompt = visual_points[target_index]
                if target_feedback:
                    prompt = f"{prompt}\n\n配图反馈：{target_feedback}"

                emit_image_progress({
                    "event": "image_start",
                    "index": target_index,
                    "total": 1,
                    "visual_point": visual_points[target_index],
                    "message": "正在按文案风格重新生成配图",
                })
                new_url = await image_service.generate_single_image(
                    prompt,
                    article_context=article_context,
                    topic=topic,
                    image_role=(
                        visual_points[target_index].split("：", 1)[0]
                        if "：" in visual_points[target_index]
                        else f"第{target_index + 1}张配图"
                    ),
                    series_context=series_context,
                )
                emit_image_progress({
                    "event": "image_done" if new_url else "image_failed",
                    "index": target_index,
                    "total": 1,
                    "url": new_url,
                    "visual_point": visual_points[target_index],
                })
                if new_url:
                    while len(image_urls) < len(visual_points):
                        image_urls.append("")
                    image_urls[target_index] = new_url
                    image_history.append({
                        "index": target_index,
                        "url": new_url,
                        "feedback": target_feedback,
                        "regenerated_at": datetime.now().isoformat(timespec="seconds"),
                        "regeneration_count": regeneration_count + 1,
                    })
                    error_msg = ""
                    status = "images_regenerated"
                    regeneration_count += 1
                else:
                    error_msg = f"第 {target_index + 1} 张配图重生成失败"
                    status = "images_generated"
            else:
                target_total = min(len(visual_points), getattr(image_service, "max_images", len(visual_points)))
                image_urls = await image_service.generate_images(
                    visual_points,
                    on_progress=emit_image_progress,
                    article_context=article_context,
                    topic=topic,
                )

                # 即使部分图片生成失败，也标记为完成
                if len(image_urls) < target_total:
                    error_msg = f"部分配图生成失败 ({len(image_urls)}/{target_total} 成功)"
                else:
                    error_msg = ""
                status = "images_generated"

            emit_image_progress({
                "event": "image_batch_done",
                "completed": len([url for url in image_urls if url]),
                "total": min(len(visual_points), getattr(image_service, "max_images", len(visual_points))),
                "image_urls": image_urls,
            })
            
            result = {
                "image_urls": image_urls,
                "image_model": image_service.model,
                "status": status,
                "error": error_msg,
                "image_review_status": "pending",
                "image_review_feedback": "",
                "image_regeneration_request": {},
                "image_regeneration_count": regeneration_count,
                "image_history": image_history,
            }
            
        except Exception as e:
            # 即使全部失败，也标记为完成（不阻塞工作流）
            result = {
                "image_urls": image_urls,
                "image_model": getattr(get_image_service(), "model", ""),
                "status": "images_generated",
                "error": f"配图生成失败: {str(e)[:100]}",
                "image_review_status": "pending",
                "image_review_feedback": "",
                "image_regeneration_request": regeneration_request,
                "image_regeneration_count": regeneration_count,
                "image_history": image_history,
            }
    
    # 在 with 块结束后（tracker.stop() 已被调用），再获取指标
    result["node_metrics"] = merge_metrics(existing_metrics, tracker.to_dict())
    return result
