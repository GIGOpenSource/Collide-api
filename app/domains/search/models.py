"""
搜索模块数据库模型
与 sql/search-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from sqlalchemy.types import DECIMAL
from sqlalchemy.sql import func

from app.database.connection import Base


class SearchHistory(Base):
    """搜索历史表"""
    __tablename__ = "t_search_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="搜索历史ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    keyword = Column(String(200), nullable=False, comment="搜索关键词")
    search_type = Column(String(20), nullable=False, default="content", comment="搜索类型：content、goods、user")
    result_count = Column(Integer, nullable=False, default=0, comment="搜索结果数量")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")


class HotSearch(Base):
    """热门搜索表"""
    __tablename__ = "t_hot_search"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="热搜ID")
    keyword = Column(String(200), nullable=False, comment="搜索关键词")
    search_count = Column(BigInteger, nullable=False, default=0, comment="搜索次数")
    trend_score = Column(DECIMAL(10, 2), nullable=False, default=0.00, comment="趋势分数")
    status = Column(String(20), nullable=False, default="active", comment="状态：active、inactive")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 