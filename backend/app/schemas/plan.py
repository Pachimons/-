"""设计方案的请求和响应模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GeneratePlanRequest(BaseModel):
    """生成方案的请求"""
    requirement_id: Optional[str] = Field(None, description="指定需求版本 ID，为空则用最新版本")


class GenerateImageRequest(BaseModel):
    """生成效果图的请求"""
    prompt: Optional[str] = Field(None, description="自定义图像 Prompt，为空则自动生成")
    image_size: str = Field("1K", description="图像尺寸：1K / 2K / 4K")


class PlanResponse(BaseModel):
    """方案的响应"""
    id: str
    conversation_id: str
    requirement_id: Optional[str] = None
    description: str = ""
    floor_plan_data: dict = {}
    rendering_urls: list[str] = []
    ai_suggestions: str = ""
    status: str = "generating"
    created_at: datetime

    model_config = {"from_attributes": True}
