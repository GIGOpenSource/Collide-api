"""
点赞模块 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LikeToggleRequest(BaseModel):
    """点赞/取消点赞请求"""
    like_type: str = Field(..., description="点赞类型：CONTENT、COMMENT、DYNAMIC")
    target_id: int = Field(..., description="目标对象ID")


class LikeInfo(BaseModel):
    """点赞信息"""
    id: int = Field(..., description="点赞ID")
    like_type: str = Field(..., description="点赞类型")
    target_id: int = Field(..., description="目标对象ID")
    user_id: int = Field(..., description="用户ID")
    status: str = Field(..., description="状态：active、cancelled")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class LikeQuery(BaseModel):
    """我的点赞查询参数"""
    like_type: Optional[str] = Field(None, description="点赞类型：CONTENT、COMMENT、DYNAMIC")


class LikeUserInfo(BaseModel):
    """点赞用户信息"""
    user_id: int = Field(..., description="用户ID")
    user_nickname: str = Field(..., description="用户昵称")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    like_time: datetime = Field(..., description="点赞时间")

    model_config = {"from_attributes": True}

