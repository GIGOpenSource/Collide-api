"""
广告模块数据库模型
与 sql/ads-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, Boolean
from sqlalchemy.sql import func

from app.database.connection import Base


class Ad(Base):
    """广告表"""
    __tablename__ = "t_ad"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="广告ID")
    ad_name = Column(String(200), nullable=False, comment="广告名称")
    ad_title = Column(String(300), nullable=False, comment="广告标题")
    ad_description = Column(String(500), comment="广告描述")
    
    ad_type = Column(String(50), nullable=False, comment="广告类型：banner、sidebar、popup、feed")
    
    image_url = Column(String(1000), nullable=False, comment="广告图片URL")
    click_url = Column(String(1000), nullable=False, comment="点击跳转链接")
    
    alt_text = Column(String(200), comment="图片替代文本")
    target_type = Column(String(30), nullable=False, default="_blank", comment="链接打开方式：_blank、_self")
    
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用（1启用，0禁用）")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重（数值越大优先级越高）")
    
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 