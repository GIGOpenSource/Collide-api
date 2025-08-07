"""
用户模块数据库模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL

from app.database.connection import Base


class User(Base):
    """用户表"""
    __tablename__ = 't_user'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='用户ID')
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=True, comment='邮箱')
    phone = Column(String(20), unique=True, nullable=True, comment='手机号')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    nickname = Column(String(50), comment='昵称')
    avatar = Column(String(500), comment='头像URL')
    gender = Column(SmallInteger, default=0, comment='性别：0未知，1男，2女')
    birthday = Column(DateTime, comment='生日')
    bio = Column(String(500), comment='个人简介')
    status = Column(String(20), nullable=False, default='active', comment='状态：active、inactive、banned')
    role = Column(String(20), nullable=False, default='user', comment='角色：admin、user')
    login_count = Column(BigInteger, nullable=False, default=0, comment='登录次数')
    last_login_time = Column(DateTime, comment='最后登录时间')
    last_login_ip = Column(String(45), comment='最后登录IP')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')


class UserWallet(Base):
    """用户钱包表"""
    __tablename__ = 't_user_wallet'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='钱包ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    balance = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='余额')
    frozen_amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='冻结金额')
    coin_balance = Column(BigInteger, nullable=False, default=0, comment='金币余额')
    total_recharge = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='总充值金额')
    total_consume = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='总消费金额')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')


class UserBlock(Base):
    """用户封禁表"""
    __tablename__ = 't_user_block'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='封禁ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    block_type = Column(String(20), nullable=False, comment='封禁类型：login、comment、post、all')
    reason = Column(String(500), comment='封禁原因')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间，NULL表示永久封禁')
    operator_id = Column(BigInteger, comment='操作员ID')
    operator_name = Column(String(50), comment='操作员名称')
    status = Column(String(20), nullable=False, default='active', comment='状态：active、cancelled')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')