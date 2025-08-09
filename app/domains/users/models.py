"""
用户模块数据库模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime, SmallInteger, Integer
from sqlalchemy import Date, Text
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
    nickname = Column(String(100), nullable=False, comment='昵称')
    avatar = Column(String(500), comment='头像URL')
    gender = Column(String(10), default='unknown', comment='性别：male、female、unknown')
    birthday = Column(Date, comment='生日')
    bio = Column(Text, comment='个人简介')
    location = Column(String(100), comment='所在地')
    status = Column(String(20), nullable=False, default='active', comment='状态：active、inactive、suspended')
    role = Column(String(20), nullable=False, default='user', comment='角色：user、blogger、admin、vip')
    
    # 统计字段
    follower_count = Column(BigInteger, nullable=False, default=0, comment='粉丝数')
    following_count = Column(BigInteger, nullable=False, default=0, comment='关注数')
    content_count = Column(BigInteger, nullable=False, default=0, comment='内容数')
    like_count = Column(BigInteger, nullable=False, default=0, comment='获得点赞数')
    
    # VIP相关
    vip_expire_time = Column(DateTime, comment='VIP过期时间')
    
    # 登录相关
    last_login_time = Column(DateTime, comment='最后登录时间')
    login_count = Column(BigInteger, nullable=False, default=0, comment='登录次数')
    
    # 邀请相关
    invite_code = Column(String(20), unique=True, comment='邀请码')
    inviter_id = Column(BigInteger, comment='邀请人ID')
    invited_count = Column(BigInteger, nullable=False, default=0, comment='邀请人数')
    
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
    coin_total_earned = Column(BigInteger, nullable=False, default=0, comment='累计获得金币')
    coin_total_spent = Column(BigInteger, nullable=False, default=0, comment='累计消费金币')
    total_income = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='总收入')
    total_expense = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='总支出')
    status = Column(String(20), nullable=False, default='active', comment='钱包状态')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')


class UserBlock(Base):
    """用户拉黑表"""
    __tablename__ = 't_user_block'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='拉黑ID')
    user_id = Column(BigInteger, nullable=False, comment='拉黑者用户ID')
    blocked_user_id = Column(BigInteger, nullable=False, comment='被拉黑用户ID')
    user_username = Column(String(50), nullable=False, comment='拉黑者用户名')
    blocked_username = Column(String(50), nullable=False, comment='被拉黑用户名')
    status = Column(String(20), nullable=False, default='active', comment='拉黑状态')
    reason = Column(String(200), comment='拉黑原因')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')