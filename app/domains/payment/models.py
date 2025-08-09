"""
支付模块数据库模型
与 sql/payment-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, DECIMAL
from sqlalchemy.dialects.mysql import JSON as MYSQL_JSON
from sqlalchemy.sql import func

from app.database.connection import Base


class PaymentChannel(Base):
    __tablename__ = "t_payment_channel"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_code = Column(String(50), nullable=False, unique=True)
    channel_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    channel_type = Column(String(20), nullable=False)
    merchant_id = Column(String(50), nullable=False)
    app_secret = Column(String(200), nullable=False)
    api_gateway = Column(String(200), nullable=False)
    timeout = Column(Integer, default=30000)
    retry_times = Column(Integer, default=3)
    status = Column(String(20), default="active")
    priority = Column(Integer, default=100)
    daily_limit = Column(DECIMAL(15, 2), default=0)
    single_limit = Column(DECIMAL(10, 2), default=0)
    fee_type = Column(String(20), default="percentage")
    fee_rate = Column(DECIMAL(8, 4), default=0.0060)
    min_fee = Column(DECIMAL(8, 2), default=0.01)
    max_fee = Column(DECIMAL(8, 2), default=50.00)
    create_time = Column(DateTime, server_default=func.current_timestamp())
    update_time = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PaymentOrder(Base):
    __tablename__ = "t_payment_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), nullable=False, unique=True)
    platform_order_no = Column(String(64))
    user_id = Column(BigInteger, nullable=False)
    user_nickname = Column(String(100))
    channel_code = Column(String(50), nullable=False)
    channel_name = Column(String(100))
    pay_type = Column(String(50), nullable=False)
    pay_mode = Column(String(20))
    amount = Column(DECIMAL(12, 2), nullable=False)
    actual_amount = Column(DECIMAL(12, 2))
    fee_amount = Column(DECIMAL(8, 2), default=0.00)
    currency = Column(String(10), default="CNY")
    status = Column(String(20), default="pending")
    pay_url = Column(Text)
    pay_time = Column(DateTime)
    expire_time = Column(DateTime)
    notify_time = Column(DateTime)
    player_id = Column(String(32))
    player_ip = Column(String(32))
    device_id = Column(String(32))
    device_type = Column(String(32))
    player_name = Column(String(32))
    player_tel = Column(String(32))
    player_pay_act = Column(String(32))
    notify_url = Column(String(200))
    return_url = Column(String(200))
    payload = Column(String(100))
    extend_params = Column(MYSQL_JSON)
    request_sign = Column(String(64))
    response_sign = Column(String(64))
    request_time = Column(BigInteger)
    create_time = Column(DateTime, server_default=func.current_timestamp())
    update_time = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PaymentNotifyLog(Base):
    __tablename__ = "t_payment_notify_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), nullable=False)
    platform_order_no = Column(String(64))
    channel_code = Column(String(50), nullable=False)
    notify_type = Column(String(20), nullable=False)
    notify_data = Column(Text, nullable=False)
    notify_sign = Column(String(64))
    sign_verify = Column(Integer, default=0)
    process_status = Column(String(20), default="pending")
    process_result = Column(Text)
    retry_times = Column(Integer, default=0)
    response_code = Column(String(10))
    response_data = Column(Text)
    notify_time = Column(DateTime, nullable=False)
    process_time = Column(DateTime)
    create_time = Column(DateTime, server_default=func.current_timestamp())


class PaymentStatistics(Base):
    __tablename__ = "t_payment_statistics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, nullable=False)
    channel_code = Column(String(50), nullable=False)
    pay_type = Column(String(50), nullable=False)
    total_orders = Column(Integer, default=0)
    success_orders = Column(Integer, default=0)
    failed_orders = Column(Integer, default=0)
    total_amount = Column(DECIMAL(15, 2), default=0.00)
    success_amount = Column(DECIMAL(15, 2), default=0.00)
    total_fee = Column(DECIMAL(10, 2), default=0.00)
    success_rate = Column(DECIMAL(5, 4), default=0.0000)
    avg_amount = Column(DECIMAL(10, 2), default=0.00)
    create_time = Column(DateTime, server_default=func.current_timestamp())
    update_time = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())