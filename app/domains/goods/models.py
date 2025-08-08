"""
商品模块数据库模型
与 sql/goods-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Boolean, DECIMAL
from sqlalchemy.sql import func

from app.database.connection import Base


class Goods(Base):
    """商品主表"""
    __tablename__ = "t_goods"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="商品ID")
    name = Column(String(200), nullable=False, comment="商品名称")
    description = Column(Text, comment="商品描述")
    category_id = Column(BigInteger, nullable=False, comment="分类ID")
    category_name = Column(String(100), comment="分类名称（冗余）")
    
    goods_type = Column(String(20), nullable=False, comment="商品类型：coin-金币、goods-商品、subscription-订阅、content-内容")
    price = Column(DECIMAL(10, 2), nullable=False, default=0.00, comment="现金价格（内容类型为0）")
    original_price = Column(DECIMAL(10, 2), comment="原价")
    coin_price = Column(BigInteger, nullable=False, default=0, comment="金币价格（内容类型专用，其他类型为0）")
    coin_amount = Column(BigInteger, comment="金币数量（仅金币类商品：购买后获得的金币数）")
    
    content_id = Column(BigInteger, comment="关联内容ID（仅内容类型有效）")
    content_title = Column(String(200), comment="内容标题（冗余，仅内容类型）")
    subscription_duration = Column(Integer, comment="订阅时长（天数，仅订阅类型有效）")
    subscription_type = Column(String(50), comment="订阅类型（VIP、PREMIUM等，仅订阅类型有效）")
    
    stock = Column(Integer, nullable=False, default=-1, comment="库存数量（-1表示无限库存，适用于虚拟商品）")
    cover_url = Column(String(500), comment="商品封面图")
    images = Column(Text, comment="商品图片，JSON数组格式")

    seller_id = Column(BigInteger, nullable=False, comment="商家ID")
    seller_name = Column(String(100), nullable=False, comment="商家名称（冗余）")

    status = Column(String(20), nullable=False, default="active", comment="状态：active、inactive、sold_out")
    sales_count = Column(BigInteger, nullable=False, default=0, comment="销量（冗余统计）")
    view_count = Column(BigInteger, nullable=False, default=0, comment="查看数（冗余统计）")

    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 