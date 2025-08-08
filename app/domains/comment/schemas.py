"""
评论模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    """评论基础模型"""
    comment_type: str = Field(..., description="评论类型：CONTENT、DYNAMIC")
    target_id: int = Field(..., description="目标对象ID")
    parent_comment_id: int = Field(default=0, ge=0, description="父评论ID，0表示根评论")
    content: str = Field(..., description="评论内容")


class CommentCreate(CommentBase):
    """创建评论请求"""
    reply_to_user_id: Optional[int] = Field(None, description="回复目标用户ID")
    reply_to_user_nickname: Optional[str] = Field(None, description="回复目标用户昵称")
    reply_to_user_avatar: Optional[str] = Field(None, description="回复目标用户头像")


class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: Optional[str] = Field(None, description="评论内容")
    status: Optional[str] = Field(None, description="状态：NORMAL、HIDDEN、DELETED")


class CommentInfo(CommentBase):
    """评论信息响应"""
    id: int = Field(..., description="评论ID")
    user_id: int = Field(..., description="评论用户ID")
    user_nickname: Optional[str] = Field(None, description="用户昵称")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    reply_to_user_id: Optional[int] = Field(None, description="回复目标用户ID")
    reply_to_user_nickname: Optional[str] = Field(None, description="回复目标用户昵称")
    reply_to_user_avatar: Optional[str] = Field(None, description="回复目标用户头像")
    status: str = Field(default="NORMAL", description="状态")
    like_count: int = Field(default=0, description="点赞数")
    reply_count: int = Field(default=0, description="回复数")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class CommentTreeInfo(CommentInfo):
    """树状评论信息"""
    children: List['CommentTreeInfo'] = Field(default_factory=list, description="子评论列表")
    level: int = Field(default=0, description="评论层级，0为根评论")
    has_more_replies: bool = Field(default=False, description="是否有更多回复")


class CommentQuery(BaseModel):
    """评论查询参数"""
    comment_type: Optional[str] = Field(None, description="评论类型过滤")
    target_id: Optional[int] = Field(None, description="目标对象过滤")
    user_id: Optional[int] = Field(None, description="用户过滤")
    parent_comment_id: Optional[int] = Field(None, description="父评论ID过滤")
    status: Optional[str] = Field(None, description="状态过滤")


# 解决循环引用
CommentTreeInfo.model_rebuild()

