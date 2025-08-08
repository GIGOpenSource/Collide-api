"""
评论模块数据库模型
与 sql/comment-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Comment(Base):
    """评论主表"""
    __tablename__ = "t_comment"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="评论ID")
    comment_type = Column(String(20), nullable=False, comment="评论类型：CONTENT、DYNAMIC")
    target_id = Column(BigInteger, nullable=False, comment="目标对象ID")
    parent_comment_id = Column(BigInteger, nullable=False, default=0, comment="父评论ID，0表示根评论")
    content = Column(Text, nullable=False, comment="评论内容")

    user_id = Column(BigInteger, nullable=False, comment="评论用户ID")
    user_nickname = Column(String(100), comment="用户昵称（冗余）")
    user_avatar = Column(String(500), comment="用户头像（冗余）")

    reply_to_user_id = Column(BigInteger, comment="回复目标用户ID")
    reply_to_user_nickname = Column(String(100), comment="回复目标用户昵称（冗余）")
    reply_to_user_avatar = Column(String(500), comment="回复目标用户头像（冗余）")

    status = Column(String(20), nullable=False, default="NORMAL", comment="状态：NORMAL、HIDDEN、DELETED")
    like_count = Column(Integer, nullable=False, default=0, comment="点赞数")
    reply_count = Column(Integer, nullable=False, default=0, comment="回复数")

    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")

