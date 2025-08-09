"""
订单模块数据库模型
与 sql/order-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, DECIMAL
from sqlalchemy.sql import func

from app.database.connection import Base


class Order(Base):
    """订单主表"""
    __tablename__ = "t_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="订单ID")
    order_no = Column(String(50), nullable=False, unique=True, comment="订单号")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    user_nickname = Column(String(100), comment="用户昵称（冗余）")

    goods_id = Column(BigInteger, nullable=False, comment="商品ID")
    goods_name = Column(String(200), comment="商品名称（冗余）")
    goods_type = Column(String(20), nullable=False, comment="商品类型：coin、goods、subscription、content")
    goods_cover = Column(String(500), comment="商品封面（冗余）")
    goods_category_name = Column(String(100), comment="商品分类名称（冗余）")

    coin_amount = Column(BigInteger, comment="金币数量")
    content_id = Column(BigInteger, comment="内容ID")
    content_title = Column(String(200), comment="内容标题")
    subscription_duration = Column(Integer, comment="订阅时长（天）")
    subscription_type = Column(String(50), comment="订阅类型")

    quantity = Column(Integer, nullable=False, default=1, comment="购买数量")

    payment_mode = Column(String(20), nullable=False, comment="支付模式：cash、coin")
    cash_amount = Column(DECIMAL(10, 2), nullable=False, default=0.00, comment="现金金额")
    coin_cost = Column(BigInteger, nullable=False, default=0, comment="消耗金币数")
    total_amount = Column(DECIMAL(10, 2), nullable=False, default=0.00, comment="订单总金额")
    discount_amount = Column(DECIMAL(10, 2), nullable=False, default=0.00, comment="优惠金额")
    final_amount = Column(DECIMAL(10, 2), nullable=False, default=0.00, comment="实付金额")

    status = Column(String(20), nullable=False, default="pending", comment="订单状态")
    pay_status = Column(String(20), nullable=False, default="unpaid", comment="支付状态")
    pay_method = Column(String(20), comment="支付方式")
    pay_time = Column(DateTime, comment="支付时间")

    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")