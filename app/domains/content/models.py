"""
内容模块数据库模型
基于 content-simple.sql 设计
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL

from app.database.connection import Base


class Content(Base):
    """内容主表"""
    __tablename__ = 't_content'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='内容ID')
    title = Column(String(200), nullable=False, comment='内容标题')
    description = Column(Text, comment='内容描述')
    content_type = Column(String(50), nullable=False, comment='内容类型：NOVEL、COMIC、LONG_VIDEO、SHORT_VIDEO、ARTICLE、AUDIO')
    content_data = Column(String(500), comment='内容数据URL')
    cover_url = Column(String(500), comment='封面图片URL')
    tags = Column(Text, comment='标签，逗号分隔或JSON格式')
    
    # 作者信息（冗余字段，避免连表）
    author_id = Column(BigInteger, nullable=False, comment='作者用户ID')
    author_nickname = Column(String(50), comment='作者昵称（冗余）')
    author_avatar = Column(String(500), comment='作者头像URL（冗余）')
    
    # 分类信息（冗余字段，避免连表）
    category_id = Column(BigInteger, comment='分类ID')
    category_name = Column(String(100), comment='分类名称（冗余）')
    
    # 状态相关字段
    status = Column(String(50), nullable=False, default='DRAFT', comment='状态：DRAFT、PUBLISHED、OFFLINE')
    review_status = Column(String(50), nullable=False, default='PENDING', comment='审核状态：PENDING、APPROVED、REJECTED')
    
    # 统计字段（冗余存储，避免聚合查询）
    view_count = Column(BigInteger, nullable=False, default=0, comment='查看数')
    like_count = Column(BigInteger, nullable=False, default=0, comment='点赞数')
    comment_count = Column(BigInteger, nullable=False, default=0, comment='评论数')
    share_count = Column(BigInteger, nullable=False, default=0, comment='分享数')
    favorite_count = Column(BigInteger, nullable=False, default=0, comment='收藏数')
    score_count = Column(BigInteger, nullable=False, default=0, comment='评分数')
    score_total = Column(BigInteger, nullable=False, default=0, comment='总评分')
    
    # 时间字段
    publish_time = Column(DateTime, comment='发布时间')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')


class ContentChapter(Base):
    """内容章节表"""
    __tablename__ = 't_content_chapter'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='章节ID')
    content_id = Column(BigInteger, nullable=False, comment='内容ID')
    chapter_num = Column(Integer, nullable=False, comment='章节号')
    title = Column(String(200), nullable=False, comment='章节标题')
    content = Column(Text, comment='章节内容')  # SQL中是LONGTEXT，但SQLAlchemy中Text已经足够
    word_count = Column(Integer, nullable=False, default=0, comment='字数')
    status = Column(String(20), nullable=False, default='DRAFT', comment='状态：DRAFT、PUBLISHED')
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')


class UserContentPurchase(Base):
    """用户内容购买记录表"""
    __tablename__ = 't_user_content_purchase'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='购买记录ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    content_id = Column(BigInteger, nullable=False, comment='内容ID')
    
    # 内容信息冗余（避免连表查询）
    content_title = Column(String(200), comment='内容标题（冗余）')
    content_type = Column(String(50), comment='内容类型（冗余）')
    content_cover_url = Column(String(500), comment='内容封面（冗余）')
    
    # 作者信息（保留author_id用于业务逻辑）
    author_id = Column(BigInteger, comment='作者ID')
    author_nickname = Column(String(50), comment='作者昵称（冗余）')
    
    # 购买相关信息
    order_id = Column(BigInteger, comment='关联订单ID')
    order_no = Column(String(50), comment='订单号（冗余）')
    coin_amount = Column(BigInteger, nullable=False, comment='支付金币数量')
    original_price = Column(BigInteger, comment='原价金币')
    discount_amount = Column(BigInteger, default=0, comment='优惠金币数量')
    
    # 购买状态
    status = Column(String(20), nullable=False, default='ACTIVE', comment='状态：ACTIVE、EXPIRED、REFUNDED')
    purchase_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='购买时间')
    expire_time = Column(DateTime, comment='过期时间（为空表示永久有效）')
    
    # 访问统计
    access_count = Column(Integer, nullable=False, default=0, comment='访问次数')
    last_access_time = Column(DateTime, comment='最后访问时间')
    
    # 时间字段
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')


class ContentPayment(Base):
    """内容付费配置表"""
    __tablename__ = 't_content_payment'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='配置ID')
    content_id = Column(BigInteger, nullable=False, comment='内容ID')
    
    # 付费类型配置
    payment_type = Column(String(20), nullable=False, default='FREE', comment='付费类型：FREE、COIN_PAY、VIP_FREE、TIME_LIMITED')
    coin_price = Column(BigInteger, nullable=False, default=0, comment='金币价格')
    original_price = Column(BigInteger, comment='原价（用于折扣显示）')
    
    # 权限配置
    vip_free = Column(SmallInteger, nullable=False, default=0, comment='会员免费：0否，1是')
    vip_only = Column(SmallInteger, nullable=False, default=0, comment='是否只有VIP才能购买：0否，1是')
    trial_enabled = Column(SmallInteger, nullable=False, default=0, comment='是否支持试读：0否，1是')
    trial_content = Column(Text, comment='试读内容')
    trial_word_count = Column(Integer, nullable=False, default=0, comment='试读字数')
    
    # 时效配置
    is_permanent = Column(SmallInteger, nullable=False, default=1, comment='是否永久有效：0否，1是')
    valid_days = Column(Integer, comment='有效天数（非永久时使用）')
    
    # 销售统计
    total_sales = Column(BigInteger, nullable=False, default=0, comment='总销量')
    total_revenue = Column(BigInteger, nullable=False, default=0, comment='总收入（金币）')
    
    # 状态配置
    status = Column(String(20), nullable=False, default='ACTIVE', comment='状态：ACTIVE、INACTIVE')
    
    # 时间字段
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')
