"""
互动模块 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InteractionInfo(BaseModel):
    """互动信息"""
    id: int = Field(..., description="互动ID")
    interaction_type: str = Field(..., description="互动类型：COMMENT、LIKE、FOLLOW")
    target_id: int = Field(..., description="目标对象ID")
    user_id: int = Field(..., description="用户ID")
    target_title: Optional[str] = Field(None, description="目标对象标题")
    target_author_id: Optional[int] = Field(None, description="目标对象作者ID")
    user_nickname: Optional[str] = Field(None, description="用户昵称")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    status: str = Field(..., description="状态：active、cancelled")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class InteractionQuery(BaseModel):
    """互动查询参数"""
    interaction_type: Optional[str] = Field(None, description="互动类型：COMMENT、LIKE、FOLLOW")
    target_id: Optional[int] = Field(None, description="目标对象ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    status: Optional[str] = Field(None, description="状态：active、cancelled")


class InteractionUserInfo(BaseModel):
    """互动用户信息"""
    user_id: int = Field(..., description="用户ID")
    user_nickname: str = Field(..., description="用户昵称")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    interaction_time: datetime = Field(..., description="互动时间")

    model_config = {"from_attributes": True} 