"""图像生成服务 — 使用 nano-banana-2 API 生成别墅效果图"""
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    """封装 nano-banana-2 图像生成 API（兼容 OpenAI DALL-E 格式）"""

    def __init__(self):
        self.api_key = settings.IMAGE_API_KEY
        self.api_base = settings.IMAGE_API_BASE
        self.model = settings.IMAGE_MODEL

    async def generate_image(
        self,
        prompt: str,
        image_size: str = "1K",
        n: int = 1,
    ) -> list[str]:
        """
        文生图：根据文字描述生成效果图。
        
        Args:
            prompt: 图像描述（英文效果更好）
            image_size: 分辨率 1K / 2K / 4K
            n: 生成图片数量
            
        Returns:
            图片 URL 列表
        """
        url = f"{self.api_base}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
            "image_size": image_size,
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                urls = []
                for item in data.get("data", []):
                    if item.get("url"):
                        urls.append(item["url"])
                
                logger.info(f"生成了 {len(urls)} 张效果图")
                return urls

        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            return []

    def build_villa_prompt(self, requirement: dict) -> str:
        """
        根据结构化需求自动生成图像 Prompt。
        
        Args:
            requirement: 结构化需求字典
            
        Returns:
            英文图像描述 Prompt
        """
        # 风格映射（中文 → 英文描述）
        style_map = {
            "现代简约": "modern minimalist",
            "现代": "modern",
            "中式": "traditional Chinese",
            "新中式": "new Chinese style",
            "欧式": "European classical",
            "地中海": "Mediterranean",
            "日式": "Japanese zen",
            "美式": "American country",
            "北欧": "Scandinavian",
        }

        style = requirement.get("style", "modern")
        style_en = style_map.get(style, style)
        floors = requirement.get("floors", 2)
        has_garden = requirement.get("has_garden", True)
        has_garage = requirement.get("has_garage", False)

        # 组装 Prompt
        parts = [
            f"A beautiful {style_en} villa",
            f"with {floors} floors",
            "white walls and large windows",
        ]
        
        if has_garden:
            parts.append("surrounded by a lush green garden with landscaping")
        if has_garage:
            parts.append("with an attached garage")

        parts.extend([
            "architectural rendering",
            "photorealistic",
            "golden hour lighting",
            "aerial perspective view",
            "high quality",
            "4K resolution",
        ])

        return ", ".join(parts)


# 创建全局图像服务实例
image_service = ImageService()
