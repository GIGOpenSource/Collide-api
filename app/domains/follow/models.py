"""
关注模块数据库模型
与 sql/follow-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Follow(Base):
    """关注关系表"""
    __tablename__ = "t_follow"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="关注ID")
    follower_id = Column(BigInteger, nullable=False, comment="关注者用户ID")
    followee_id = Column(BigInteger, nullable=False, comment="被关注者用户ID")

    follower_nickname = Column(String(100), comment="关注者昵称（冗余）")
    follower_avatar = Column(String(500), comment="关注者头像（冗余）")

    followee_nickname = Column(String(100), comment="被关注者昵称（冗余）")
    followee_avatar = Column(String(500), comment="被关注者头像（冗余）")

    status = Column(String(20), nullable=False, default="active", comment="状态：active、cancelled")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 