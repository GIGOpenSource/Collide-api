"""
标签模块数据库模型
与 sql/tag-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, DECIMAL
from sqlalchemy.sql import func

from app.database.connection import Base


class Tag(Base):
    """标签主表"""
    __tablename__ = "t_tag"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="标签ID")
    name = Column(String(100), nullable=False, comment="标签名称")
    description = Column(Text, comment="标签描述")
    tag_type = Column(String(20), nullable=False, default="content", comment="标签类型：content、interest、system")
    category_id = Column(BigInteger, comment="所属分类ID")
    usage_count = Column(BigInteger, nullable=False, default=0, comment="使用次数")
    status = Column(String(20), nullable=False, default="active", comment="状态：active、inactive")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class UserInterestTag(Base):
    """用户兴趣标签关联表"""
    __tablename__ = "t_user_interest_tag"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    tag_id = Column(BigInteger, nullable=False, comment="标签ID")
    interest_score = Column(DECIMAL(5, 2), nullable=False, default=0.00, comment="兴趣分数（0-100）")
    status = Column(String(20), nullable=False, default="active", comment="状态：active、inactive")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")


class ContentTag(Base):
    """内容标签关联表"""
    __tablename__ = "t_content_tag"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    content_id = Column(BigInteger, nullable=False, comment="内容ID")
    tag_id = Column(BigInteger, nullable=False, comment="标签ID")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间") 