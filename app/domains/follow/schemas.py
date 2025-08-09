"""
关注模块 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FollowToggleRequest(BaseModel):
    """关注/取消关注请求"""
    followee_id: int = Field(..., description="被关注者用户ID")


class FollowInfo(BaseModel):
    """关注信息"""
    id: int = Field(..., description="关注ID")
    follower_id: int = Field(..., description="关注者用户ID")
    followee_id: int = Field(..., description="被关注者用户ID")
    follower_nickname: Optional[str] = Field(None, description="关注者昵称")
    follower_avatar: Optional[str] = Field(None, description="关注者头像")
    followee_nickname: Optional[str] = Field(None, description="被关注者昵称")
    followee_avatar: Optional[str] = Field(None, description="被关注者头像")
    status: str = Field(..., description="状态：active、cancelled")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class FollowQuery(BaseModel):
    """关注查询参数"""
    user_id: Optional[int] = Field(None, description="用户ID")
    follow_type: Optional[str] = Field(None, description="关注类型")
    status: Optional[str] = Field(None, description="状态")


class FollowStatus(BaseModel):
    """关注状态详情"""
    following: bool = Field(..., description="我是否关注了TA")
    followed_by: bool = Field(..., description="TA是否关注了我")
    mutual: bool = Field(..., description="是否互相关注")


class FollowStats(BaseModel):
    """关注统计"""
    following_count: int = Field(..., description="关注数")
    follower_count: int = Field(..., description="粉丝数") 