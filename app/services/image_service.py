"""
图片生成服务模块
使用火山方舟图片生成 API 生成小红书风格配图
"""
import os
import asyncio
import base64
import io
import re
import logging
import uuid
import random
import httpx
from pathlib import Path
from typing import Any, Callable, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv()

logger = logging.getLogger(__name__)


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class ImageService:
    """图片生成服务类"""

    XHS_STYLE_PROMPT = """你是竖版社交媒体内容配图导演，请根据文案生成一张与文章内容和气质高度一致的系列配图。

【最高优先级硬性限制】
纯画面，无任何可读文字、字母、数字、品牌名、平台标志、Logo、水印、二维码、软件界面或标题排版。所有电子屏幕必须背对镜头、侧放、熄屏、纯色或严重虚化，不能成为画面视觉中心。

【本张在系列中的角色】
{image_role}

【本张主体与镜头硬约束】
{role_directive}

【选题】
{topic}

【只与本张直接相关的正文片段】
{article_context}

【三张图共同视觉基因】
{series_context}

【当前画面 brief（最高优先级）】
{content}

【生成要求】
- 先逐项落实当前 brief 的“不可替代元素”，再处理风格、光线和美感；三个元素必须都能在画面中明确找到
- 当前画面 brief 的正文依据、核心含义、人物/主体、动作、场景和因果关系优先级最高，必须具体呈现，不能只画泛泛的氛围图
- 画面若可以无差别用于另一篇普通职场或AI文章，即视为失败；必须表现这段正文独有的案例、操作或前后变化
- 正文上下文与系列规划只用于理解含义、人物设定和视觉连续性；不得把标题、提示词或正文直接排版到画面上
- 系列感只通过主色调、材质、光线和艺术语言保持；人物、桌面、电脑和同一空间不得作为三张图的固定重复元素
- 必须服从“本张主体与镜头硬约束”；即使当前 brief 带有旧版固定人物卡，也不能因此重复另外两张的人物办公构图
- 三张图必须分别承担人物/故事主视觉、方法/流程解释、成果/证据展示；本张只完成自己的角色，不挪用其他两张的主体类型
- 优先描绘文案真实提到的对象、动作、场景和变化，不得擅自添加品牌、课程、商品、收益数字或正文没有的结论
- 先看文案气质，再决定风格，不套通用模板
- 教程/干货：清爽、专业、结构感强，像内容封面而不是随机生活照
- AI/编程/工具：优先表现正文独有的输入材料、处理动作和输出结果；只有正文确实描述流程时才使用实体卡片和节点，并让卡片的分组、筛选、转换或校验动作与该段方法一一对应；不画正面电脑或手机屏幕，不画真实软件截图、表格界面或可读文字
- 生活/情绪：贴近真实场景，温暖自然，有人物动作和生活细节
- 观点/反差：更强的视觉中心和象征元素
- 严格禁止任何汉字、英文、数字、标题、标签、按钮文字、菜单文字、代码、表格单元格文字、logo、水印、二维码
- 如需表达信息，请只使用无意义短线、圆点、色块、图标和抽象形状
- 构图要适合3:4竖版社交媒体配图，主体明确，留白合理
- 直接生成纯画面，不要在图片中加入说明文字

【再次确认】no text, no letters, no numbers, no logo, no watermark, no brand identity, no readable screen, no UI screenshot。"""

    ROLE_DIRECTIVES = {
        "封面图": (
            "人物/故事主视觉。可以出现完整人物，但核心必须是正文的冲突、变化或结论；"
            "使用有张力的中近景、前后反差或动态构图。禁止普通的‘人物坐在桌前看电脑’，"
            "禁止把电脑桌当成最大视觉主体。"
        ),
        "场景图": (
            "方法/流程配套图。优先使用俯拍流程、手部操作、实体物件的分组/移动/连接，"
            "或能看清动作顺序的空间场景；尽量不出现完整人物。禁止人物坐在办公桌前，"
            "禁止复用封面的人物中景构图，画面要直接解释事情如何发生。"
        ),
        "细节图": (
            "成果/证据配套图。不得出现完整人物，以正文独有的结果物件、前后对照、"
            "完成状态、关键局部或细节特写为主体；使用微距、俯拍陈列或左右对照构图。"
            "禁止办公桌人物场景，禁止只是前两张的裁切或换角度版本。"
        ),
    }

    FALLBACK_PROMPTS = [
        "小红书风格，明亮温暖的生活场景，咖啡和书本，柔和自然光，3:4竖版构图",
        "小红书风格，创意工作台，文具和绿植，ins风格，3:4竖版构图",
        "小红书风格，清新简约的扁平插画，渐变色背景，3:4竖版构图",
    ]

    TEXT_TRIGGER_REPLACEMENTS = [
        (r"电脑屏幕(?:上)?显示[^；。\n]*", "人物与实体任务卡和抽象流程节点互动，电子屏幕背对镜头"),
        (r"(?:手机|平板|屏幕)(?:上)?显示[^；。\n]*", "设备屏幕熄灭并背对镜头，信息改用抽象节点表达"),
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
        (r"Notion", "无字协作看板"),
        (r"新抖|蝉妈妈", "数据分析工具"),
        (r"\b[A-Za-z][A-Za-z0-9.-]{2,}\b", "智能工具"),
        (r"\bPython\b", "脚本自动化视觉符号"),
        (r"\bExcel\b", "抽象数据网格"),
        (r"\bWord\b", "抽象文档图标"),
        (r"\bPowerPoint\b", "抽象演示文稿图标"),
        (r"\bPPT\b", "抽象演示文稿图标"),
        (r"\bMarkdown\b", "抽象文档结构"),
        (r"\bAPI\b", "抽象接口节点"),
        (r"\bAI\b", "智能算法光效"),
        (r"代码", "抽象逻辑线条"),
        (r"表格", "抽象数据网格"),
        (r"邮件", "信封图标"),
        (r"标题", "视觉中心"),
        (r"封面文字", "视觉中心"),
    ]

    def __init__(self):
        self.api_key = os.getenv("IMAGE_API_KEY", "")
        self.base_url = os.getenv("IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = os.getenv("IMAGE_MODEL", "doubao-seedream-4-5-251128")
        self.size = os.getenv("IMAGE_SIZE", "1664x2240")
        self.response_format = os.getenv("IMAGE_RESPONSE_FORMAT", "b64_json")
        self.watermark = _get_bool_env("IMAGE_WATERMARK", False)
        self.local_fallback_enabled = _get_bool_env("IMAGE_LOCAL_FALLBACK", True)
        self.max_images = max(_get_int_env("IMAGE_MAX_IMAGES", 3), 1)
        self.request_timeout = max(_get_int_env("IMAGE_REQUEST_TIMEOUT", 45), 10)
        self.retry_on_failure = _get_bool_env("IMAGE_RETRY_ON_FAILURE", False)
        
        self.image_dir = Path("static/images/generated")
        self.image_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            raise ValueError("IMAGE_API_KEY 未配置")

    def _build_api_url(self) -> str:
        base_url = self.base_url.rstrip("/")
        if base_url.endswith("/images/generations"):
            return base_url
        return f"{base_url}/images/generations"

    def _save_image_bytes(self, image_bytes: bytes, prefix: str = "xhs") -> str:
        """保存图片字节到本地"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}.png"
        
        file_path = self.image_dir / filename
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        return f"/static/images/generated/{filename}"

    def _save_base64_image(self, image_base64: str) -> str:
        """保存 base64 图片到本地"""
        if "," in image_base64 and image_base64.startswith("data:"):
            image_base64 = image_base64.split(",", 1)[1]
        return self._save_image_bytes(base64.b64decode(image_base64))

    async def _download_and_save_image(self, image_url: str) -> Optional[str]:
        """下载图片 URL 并保存到本地"""
        try:
            async with httpx.AsyncClient(timeout=float(self.request_timeout)) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return self._save_image_bytes(response.content)
        except Exception as e:
            print(f"[ImageService] 图片下载失败: {e}")
            return None

    def _find_font(self) -> Optional[str]:
        """查找可用字体，优先支持中文。"""
        candidates = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        for font_path in candidates:
            if Path(font_path).exists():
                return font_path
        return None

    def _build_style_prompt(
        self,
        prompt: str,
        article_context: str = "",
        topic: str = "",
        image_role: str = "",
        series_context: str = "",
    ) -> str:
        # 每张图只接收与自身 brief 最相关的正文片段，避免全文主题稀释具体画面。
        compact_role = " ".join((image_role or "").split())[:80] or "系列配图"
        # 系列设定由下方的“共同视觉基因”单独提供，当前画面不再携带固定人物卡。
        prompt = re.sub(
            r"系列设定[“\"][^”\"]+[”\"]；?",
            "系列视觉基因见下方；",
            prompt or "",
        )
        prompt = self._reduce_text_triggers(prompt)
        compact_context = self._reduce_text_triggers(
            self._build_relevant_article_context(article_context, prompt)
        )
        compact_topic = self._reduce_text_triggers(" ".join((topic or "").split())[:160])
        compact_series = self._build_series_style_context(series_context)

        return self.XHS_STYLE_PROMPT.format(
            content=prompt,
            article_context=compact_context or "未提供",
            topic=compact_topic or "未提供",
            image_role=compact_role,
            role_directive=self._get_role_directive(compact_role),
            series_context=compact_series or "未提供，请以当前画面 brief 为准",
        )

    def _get_role_directive(self, image_role: str) -> str:
        for role_name, directive in self.ROLE_DIRECTIVES.items():
            if role_name in image_role:
                return directive
        return (
            "根据正文选择明确主体，但不得使用泛化的桌前办公构图；"
            "必须与系列其他图片在主体、镜头和信息用途上明显不同。"
        )

    def _build_series_style_context(self, series_context: str) -> str:
        """仅保留跨图视觉风格，避免把其他图片的主体和构图带入当前提示词。"""
        matches = re.findall(r"系列设定[“\"]([^”\"]+)[”\"]", series_context or "")
        style = matches[0] if matches else ""
        # 兼容已生成的旧版 brief：人物卡不再作为跨图硬约束。
        style = re.sub(r"(?:固定)?人物(?:卡|设定|外观)?[^；。]*[；。]?", "", style)
        style = re.sub(r"(?:人数|年龄感|性别|发型|服装)[^；。]*[；。]?", "", style)
        style = self._reduce_text_triggers(" ".join(style.split())[:700])
        visual_dna = style or "统一主色、材质、光线和插画或摄影语言"
        return (
            f"共同视觉DNA：{visual_dna}。"
            "只统一风格，不统一人物与场景。角色分工固定为："
            "封面图=人物/故事主视觉；场景图=方法/流程解释；"
            "细节图=成果/证据展示。至少一张不出现人物。"
        )

    def _reduce_text_triggers(self, text: str) -> str:
        cleaned = text or ""
        for pattern, replacement in self.TEXT_TRIGGER_REPLACEMENTS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned

    @staticmethod
    def _clean_article_text(article_context: str) -> str:
        context = re.sub(r"```[\s\S]*?```", "\n[代码示例]\n", article_context or "")
        context = re.sub(r"(?m)^\s*>.*$", "", context)
        context = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", context)
        context = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", context)
        context = re.sub(r"[*_~`]", "", context)
        context = re.sub(r"[ \t]+", " ", context)
        return re.sub(r"\n{3,}", "\n\n", context).strip()

    @staticmethod
    def _semantic_ngrams(text: str) -> set[str]:
        normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()
        if len(normalized) < 2:
            return {normalized} if normalized else set()
        return {normalized[index:index + 2] for index in range(len(normalized) - 1)}

    def _build_relevant_article_context(
        self,
        article_context: str,
        visual_brief: str,
        max_length: int = 700,
    ) -> str:
        """按正文依据和不可替代元素，选择当前图片真正对应的句子。"""
        cleaned_article = self._clean_article_text(article_context)
        if not cleaned_article:
            return ""

        sanitized_article = self._reduce_text_triggers(cleaned_article)
        candidates = [
            sentence.strip()
            for sentence in re.split(r"(?<=[。！？!?；])|\n+", sanitized_article)
            if sentence.strip()
        ]
        if not candidates:
            return self._build_article_context(sanitized_article, max_length=max_length)

        cues = []
        for field, closing in (("正文依据", "”"), ("核心含义", "”"), ("不可替代元素", "]")):
            opener = "“" if closing == "”" else "["
            match = re.search(rf"{field}[：:]?{re.escape(opener)}([^”\]]+){re.escape(closing)}", visual_brief)
            if match:
                cues.append(match.group(1))
        if not cues:
            return self._build_article_context(sanitized_article, max_length=max_length)

        cue_text = "；".join(cues)
        cue_ngrams = self._semantic_ngrams(cue_text)
        evidence = cues[0].strip()
        scored = []
        for index, sentence in enumerate(candidates):
            sentence_ngrams = self._semantic_ngrams(sentence)
            overlap = len(cue_ngrams & sentence_ngrams)
            exact_bonus = 1000 if evidence and evidence in sentence else 0
            scored.append((exact_bonus + overlap, index))

        best_index = max(scored)[1]
        selected_indexes = {
            index
            for index in (best_index - 1, best_index, best_index + 1)
            if 0 <= index < len(candidates)
        }
        # 再补一个与不可替代元素匹配度最高、但不相邻的句子。
        for score, index in sorted(scored, reverse=True):
            if score > 0 and index not in selected_indexes:
                selected_indexes.add(index)
                break

        selected = " ".join(candidates[index] for index in sorted(selected_indexes))
        if len(selected) > max_length:
            selected = selected[:max_length]
        return selected

    def _build_article_context(self, article_context: str, max_length: int = 1800) -> str:
        """保留正文前中后三段，避免只根据导语生成图片。"""
        context = re.sub(r"\s+", " ", self._clean_article_text(article_context)).strip()
        if len(context) <= max_length:
            return context

        head_len = int(max_length * 0.4)
        middle_len = int(max_length * 0.3)
        tail_len = max_length - head_len - middle_len
        middle_start = max(head_len, (len(context) - middle_len) // 2)
        return (
            f"开头：{context[:head_len]}；"
            f"中段：{context[middle_start:middle_start + middle_len]}；"
            f"结尾：{context[-tail_len:]}"
        )

    async def _call_volcengine_api(self, prompt: str) -> Optional[str]:
        """调用火山方舟图片生成 API"""
        url = self._build_api_url()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": self.size,
            "response_format": self.response_format,
            "stream": False,
            "watermark": self.watermark,
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=float(self.request_timeout)) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                for item in result.get("data", []):
                    if item.get("b64_json"):
                        return self._save_base64_image(item["b64_json"])

                    if item.get("url"):
                        image_path = await self._download_and_save_image(item["url"])
                        return image_path or item["url"]
                
                print(f"[ImageService] API 响应中未找到图片数据")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "[ImageService] HTTP 错误: %s %s",
                e.response.status_code,
                e.response.text[:2000],
            )
            return None
        except Exception as e:
            logger.exception("[ImageService] 请求异常: %s", e)
            return None

    def _make_local_image(self, prompt: str) -> Optional[str]:
        if not self.local_fallback_enabled:
            return None

        try:
            image = Image.new("RGB", (864, 1152), "#f3f5f7")
            draw = ImageDraw.Draw(image)
            top_color = (244, 247, 252)
            bottom_color = (223, 231, 242)
            for y in range(image.height):
                ratio = y / max(image.height - 1, 1)
                r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
                g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
                b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
                draw.line((0, y, image.width, y), fill=(r, g, b))

            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.ellipse((80, 120, 360, 400), fill=(64, 88, 161, 90))
            overlay_draw.ellipse((480, 160, 820, 500), fill=(225, 138, 88, 80))
            overlay_draw.rounded_rectangle((70, 740, 794, 1030), radius=36, fill=(255, 255, 255, 245))
            image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(image)

            font_path = self._find_font()
            if font_path:
                title_font = ImageFont.truetype(font_path, 56)
                body_font = ImageFont.truetype(font_path, 28)
            else:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()

            draw.text((92, 790), "AI 内容工作台", font=title_font, fill=(15, 23, 42))
            draw.text((92, 868), prompt[:44].replace("\n", " "), font=body_font, fill=(71, 85, 105))
            draw.text((92, 960), "Local fallback cover", font=body_font, fill=(99, 115, 129))

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return self._save_image_bytes(buffer.getvalue())
        except Exception as e:
            logger.exception("[ImageService] 本地兜底图片生成失败: %s", e)
            return None

    async def generate_single_image(
        self,
        prompt: str,
        optimize_for_xhs: bool = True,
        article_context: str = "",
        topic: str = "",
        image_role: str = "",
        series_context: str = "",
    ) -> Optional[str]:
        """生成单张图片（失败时使用备用提示词重试一次）"""
        current_prompt = self._build_style_prompt(
            prompt,
            article_context=article_context,
            topic=topic,
            image_role=image_role,
            series_context=series_context,
        ) if optimize_for_xhs else prompt
        
        logger.info("[ImageService] 生成图片: %s...", prompt[:50])
        
        # 首次尝试
        image_path = await self._call_volcengine_api(current_prompt)
        if image_path:
            logger.info("[ImageService] 图片生成成功: %s", image_path)
            return image_path
        local_path = self._make_local_image(current_prompt)
        if local_path:
            logger.warning("[ImageService] 使用本地兜底图片: %s", local_path)
            return local_path
        
        if not self.retry_on_failure:
            logger.warning("[ImageService] 图片生成失败，已跳过备用提示词重试")
            return None

        # 使用备用提示词重试
        logger.info("[ImageService] 首次失败，使用备用提示词重试...")
        await asyncio.sleep(1)
        
        fallback_prompt = random.choice(self.FALLBACK_PROMPTS)
        image_path = await self._call_volcengine_api(fallback_prompt)
        if image_path:
            logger.info("[ImageService] 备用提示词成功: %s", image_path)
            return image_path
        local_path = self._make_local_image(fallback_prompt)
        if local_path:
            logger.warning("[ImageService] 使用本地兜底图片: %s", local_path)
            return local_path
        
        logger.error("[ImageService] 图片生成失败，跳过")
        return None

    async def generate_images(
        self,
        visual_points: List[str],
        optimize_for_xhs: bool = True,
        on_progress: Optional[Callable[[dict[str, Any]], None]] = None,
        article_context: str = "",
        topic: str = "",
    ) -> List[str]:
        """批量生成配图（并行）"""
        if not visual_points:
            return []

        target_points = visual_points[:self.max_images]
        series_context = "\n".join(
            f"第{index + 1}张：{point}" for index, point in enumerate(target_points)
        )

        async def generate_one(index: int, point: str) -> Optional[str]:
            if on_progress:
                on_progress({
                    "event": "image_start",
                    "index": index,
                    "total": len(target_points),
                    "visual_point": point,
                    "message": f"正在按文案风格生成第 {index + 1} 张配图",
                })

            image_path = await self.generate_single_image(
                prompt=point,
                optimize_for_xhs=optimize_for_xhs,
                article_context=article_context,
                topic=topic,
                image_role=(point.split("：", 1)[0] if "：" in point else f"第{index + 1}张配图"),
                series_context=series_context,
            )

            if on_progress:
                on_progress({
                    "event": "image_done" if image_path else "image_failed",
                    "index": index,
                    "total": len(target_points),
                    "url": image_path,
                    "visual_point": point,
                })

            return image_path

        tasks = [generate_one(index, point) for index, point in enumerate(target_points)]
        results = await asyncio.gather(*tasks)

        image_paths = [path for path in results if path is not None]
        logger.info("[ImageService] 成功生成 %s/%s 张图片", len(image_paths), len(target_points))
        return image_paths


# 单例实例
image_service = ImageService()
