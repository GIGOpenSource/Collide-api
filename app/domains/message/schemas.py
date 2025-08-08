"""
消息模块 Pydantic 模型
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """创建消息请求"""
    receiver_id: int = Field(..., description="接收者ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field("text", description="消息类型：text、image、file、system")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="扩展数据")
    reply_to_id: Optional[int] = Field(None, description="回复的消息ID")
    is_pinned: bool = Field(False, description="是否置顶")


class MessageUpdate(BaseModel):
    """更新消息请求"""
    content: Optional[str] = Field(None, description="消息内容")
    status: Optional[str] = Field(None, description="消息状态：sent、delivered、read、deleted")
    is_pinned: Optional[bool] = Field(None, description="是否置顶")


class MessageInfo(BaseModel):
    """消息信息"""
    id: int = Field(..., description="消息ID")
    sender_id: int = Field(..., description="发送者ID")
    receiver_id: int = Field(..., description="接收者ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(..., description="消息类型")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="扩展数据")
    status: str = Field(..., description="消息状态")
    read_time: Optional[datetime] = Field(None, description="已读时间")
    reply_to_id: Optional[int] = Field(None, description="回复的消息ID")
    is_pinned: bool = Field(..., description="是否置顶")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class MessageSessionInfo(BaseModel):
    """会话信息"""
    id: int = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    other_user_id: int = Field(..., description="对方用户ID")
    last_message_id: Optional[int] = Field(None, description="最后一条消息ID")
    last_message_time: Optional[datetime] = Field(None, description="最后消息时间")
    unread_count: int = Field(..., description="未读消息数")
    is_archived: bool = Field(..., description="是否归档")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class MessageSettingInfo(BaseModel):
    """消息设置信息"""
    id: int = Field(..., description="设置ID")
    user_id: int = Field(..., description="用户ID")
    allow_stranger_msg: bool = Field(..., description="是否允许陌生人发消息")
    auto_read_receipt: bool = Field(..., description="是否自动发送已读回执")
    message_notification: bool = Field(..., description="是否开启消息通知")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class MessageSettingUpdate(BaseModel):
    """更新消息设置请求"""
    allow_stranger_msg: Optional[bool] = Field(None, description="是否允许陌生人发消息")
    auto_read_receipt: Optional[bool] = Field(None, description="是否自动发送已读回执")
    message_notification: Optional[bool] = Field(None, description="是否开启消息通知")


class MessageQuery(BaseModel):
    """消息查询参数"""
    other_user_id: Optional[int] = Field(None, description="对方用户ID")
    message_type: Optional[str] = Field(None, description="消息类型")
    status: Optional[str] = Field(None, description="消息状态")
    is_pinned: Optional[bool] = Field(None, description="是否置顶") 