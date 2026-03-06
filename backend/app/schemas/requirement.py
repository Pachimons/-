"""结构化需求的请求和响应模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RequirementResponse(BaseModel):
    """结构化需求的响应"""
    id: str
    conversation_id: str
    land_area: Optional[float] = None
    land_location: Optional[str] = None
    floors: Optional[int] = None
    style: Optional[str] = None
    total_rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    has_elderly_room: Optional[bool] = None
    has_garage: Optional[bool] = None
    has_garden: Optional[bool] = None
    budget: Optional[float] = None
    special_notes: Optional[str] = None
    completeness: float = 0.0
    version: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequirementExtracted(BaseModel):
    """AI 从对话中提取的结构化需求（Gemini response_schema）"""
    land_area: Optional[float] = Field(None, description="土地面积（平方米）")
    land_location: Optional[str] = Field(None, description="土地所在地（省市区）")
    floors: Optional[int] = Field(None, description="楼层数")
    style: Optional[str] = Field(None, description="建筑风格")
    total_rooms: Optional[int] = Field(None, description="总房间数")
    bedrooms: Optional[int] = Field(None, description="卧室数")
    bathrooms: Optional[int] = Field(None, description="卫生间数")
    has_elderly_room: Optional[bool] = Field(None, description="是否需要老人房")
    has_garage: Optional[bool] = Field(None, description="是否需要车库")
    has_garden: Optional[bool] = Field(None, description="是否需要花园")
    budget: Optional[float] = Field(None, description="预算（元）")
    special_notes: Optional[str] = Field(None, description="特殊备注")
    completeness: float = Field(0.0, description="需求完整度（0~1）")
