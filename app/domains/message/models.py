"""
消息模块数据库模型
与 sql/message-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Boolean, JSON, Integer
from sqlalchemy.sql import func

from app.database.connection import Base


class Message(Base):
    """私信消息主表"""
    __tablename__ = "t_message"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="消息ID")
    sender_id = Column(BigInteger, nullable=False, comment="发送者ID")
    receiver_id = Column(BigInteger, nullable=False, comment="接收者ID")
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(20), nullable=False, default="text", comment="消息类型：text、image、file、system")
    extra_data = Column(JSON, comment="扩展数据（图片URL、文件信息等）")
    status = Column(String(20), nullable=False, default="sent", comment="消息状态：sent、delivered、read、deleted")
    read_time = Column(DateTime, comment="已读时间")
    reply_to_id = Column(BigInteger, comment="回复的消息ID（引用消息）")
    is_pinned = Column(Boolean, nullable=False, default=False, comment="是否置顶（留言板功能）")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class MessageSession(Base):
    """用户会话统计表"""
    __tablename__ = "t_message_session"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="会话ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    other_user_id = Column(BigInteger, nullable=False, comment="对方用户ID")
    last_message_id = Column(BigInteger, comment="最后一条消息ID")
    last_message_time = Column(DateTime, comment="最后消息时间")
    unread_count = Column(Integer, nullable=False, default=0, comment="未读消息数")
    is_archived = Column(Boolean, nullable=False, default=False, comment="是否归档")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class MessageSetting(Base):
    """用户消息设置表"""
    __tablename__ = "t_message_setting"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="设置ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    allow_stranger_msg = Column(Boolean, nullable=False, default=True, comment="是否允许陌生人发消息")
    auto_read_receipt = Column(Boolean, nullable=False, default=True, comment="是否自动发送已读回执")
    message_notification = Column(Boolean, nullable=False, default=True, comment="是否开启消息通知")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 