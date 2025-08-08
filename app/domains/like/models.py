"""
点赞模块数据库模型
与 sql/like-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Like(Base):
    """点赞主表"""
    __tablename__ = "t_like"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="点赞ID")
    like_type = Column(String(20), nullable=False, comment="点赞类型：CONTENT、COMMENT、DYNAMIC")
    target_id = Column(BigInteger, nullable=False, comment="目标对象ID")
    user_id = Column(BigInteger, nullable=False, comment="点赞用户ID")

    target_title = Column(String(200), comment="目标对象标题（冗余）")
    target_author_id = Column(BigInteger, comment="目标对象作者ID（冗余）")

    user_nickname = Column(String(100), comment="用户昵称（冗余）")
    user_avatar = Column(String(500), comment="用户头像（冗余）")

    status = Column(String(20), nullable=False, default="active", comment="状态：active、cancelled")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")

