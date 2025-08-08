"""
社交动态模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DynamicBase(BaseModel):
    """动态基础模型"""
    content: str = Field(..., description="动态内容")
    dynamic_type: str = Field(default="text", description="动态类型：text、image、video、share")
    images: Optional[str] = Field(None, description="图片列表，JSON字符串")
    video_url: Optional[str] = Field(None, description="视频URL")
    share_target_type: Optional[str] = Field(None, description="分享目标类型：content、goods")
    share_target_id: Optional[int] = Field(None, description="分享目标ID")
    share_target_title: Optional[str] = Field(None, description="分享目标标题")


class DynamicCreate(DynamicBase):
    """创建动态请求"""
    pass


class DynamicUpdate(BaseModel):
    """更新动态请求"""
    content: Optional[str] = Field(None, description="动态内容")
    dynamic_type: Optional[str] = Field(None, description="动态类型")
    images: Optional[str] = Field(None, description="图片列表，JSON字符串")
    video_url: Optional[str] = Field(None, description="视频URL")
    status: Optional[str] = Field(None, description="状态：normal、hidden、deleted")


class DynamicInfo(DynamicBase):
    """动态信息响应"""
    id: int = Field(..., description="动态ID")
    user_id: int = Field(..., description="发布用户ID")
    user_nickname: Optional[str] = Field(None, description="用户昵称")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    status: str = Field(default="normal", description="状态")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class DynamicQuery(BaseModel):
    """动态查询参数"""
    keyword: Optional[str] = Field(None, description="关键词（内容模糊搜索）")
    dynamic_type: Optional[str] = Field(None, description="动态类型")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    status: Optional[str] = Field(None, description="状态过滤")

