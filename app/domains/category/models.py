"""
分类模块数据库模型
与 sql/category-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Category(Base):
    """分类主表"""
    __tablename__ = "t_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(100), nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    parent_id = Column(BigInteger, nullable=False, default=0, comment="父分类ID，0表示顶级分类")
    icon_url = Column(String(500), comment="分类图标URL")
    sort = Column(Integer, nullable=False, default=0, comment="排序值")
    content_count = Column(BigInteger, nullable=False, default=0, comment="内容数量（冗余统计）")
    status = Column(String(20), nullable=False, default="active", comment="状态：active、inactive")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间",
    )

