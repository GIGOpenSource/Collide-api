"""
收藏模块数据库模型
与 sql/favorite-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Favorite(Base):
    """收藏主表"""
    __tablename__ = "t_favorite"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="收藏ID")
    favorite_type = Column(String(20), nullable=False, comment="收藏类型：CONTENT、GOODS")
    target_id = Column(BigInteger, nullable=False, comment="收藏目标ID")
    user_id = Column(BigInteger, nullable=False, comment="收藏用户ID")

    target_title = Column(String(200), comment="收藏对象标题（冗余）")
    target_cover = Column(String(500), comment="收藏对象封面（冗余）")
    target_author_id = Column(BigInteger, comment="收藏对象作者ID（冗余）")

    user_nickname = Column(String(100), comment="用户昵称（冗余）")

    status = Column(String(20), nullable=False, default="active", comment="状态：active、cancelled")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 