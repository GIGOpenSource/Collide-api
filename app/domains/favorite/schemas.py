"""
收藏模块 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FavoriteToggleRequest(BaseModel):
    """收藏/取消收藏请求"""
    favorite_type: str = Field(..., description="收藏类型：CONTENT、GOODS")
    target_id: int = Field(..., description="收藏目标ID")


class FavoriteInfo(BaseModel):
    """收藏信息"""
    id: int = Field(..., description="收藏ID")
    favorite_type: str = Field(..., description="收藏类型")
    target_id: int = Field(..., description="收藏目标ID")
    user_id: int = Field(..., description="用户ID")
    target_title: Optional[str] = Field(None, description="收藏对象标题")
    target_cover: Optional[str] = Field(None, description="收藏对象封面")
    target_author_id: Optional[int] = Field(None, description="收藏对象作者ID")
    user_nickname: Optional[str] = Field(None, description="用户昵称")
    status: str = Field(..., description="状态：active、cancelled")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class FavoriteQuery(BaseModel):
    """收藏查询参数"""
    user_id: Optional[int] = Field(None, description="用户ID")
    favorite_type: Optional[str] = Field(None, description="收藏类型：CONTENT、GOODS")
    status: Optional[str] = Field(None, description="状态：active、cancelled") 