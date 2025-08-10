"""
社交动态模块数据库模型
与 sql/social-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Boolean
from sqlalchemy.sql import func

from app.database.connection import Base


class SocialDynamic(Base):
    """社交动态主表"""
    __tablename__ = "t_social_dynamic"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="动态ID")
    content = Column(Text, nullable=False, comment="动态内容")
    dynamic_type = Column(String(20), nullable=False, default="text", comment="动态类型：text、image、video、share")
    images = Column(Text, comment="图片列表，JSON格式")
    video_url = Column(String(500), comment="视频URL")

    # 用户冗余信息
    user_id = Column(BigInteger, nullable=False, comment="发布用户ID")
    user_nickname = Column(String(100), comment="用户昵称（冗余）")
    user_avatar = Column(String(500), comment="用户头像（冗余）")

    # 分享相关
    share_target_type = Column(String(20), comment="分享目标类型：content、goods")
    share_target_id = Column(BigInteger, comment="分享目标ID")
    share_target_title = Column(String(200), comment="分享目标标题（冗余）")

    # 统计
    like_count = Column(BigInteger, nullable=False, default=0, comment="点赞数")
    comment_count = Column(BigInteger, nullable=False, default=0, comment="评论数")
    share_count = Column(BigInteger, nullable=False, default=0, comment="分享数")

    status = Column(String(20), nullable=False, default="normal", comment="状态：normal、hidden、deleted")
    review_status = Column(String(20), nullable=False, default="PENDING", comment="审核状态：PENDING、APPROVED、REJECTED")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class SocialPaidDynamic(Base):
    """付费动态表"""
    __tablename__ = "t_social_paid_dynamic"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="付费动态ID")
    dynamic_id = Column(BigInteger, nullable=False, comment="关联的动态ID")
    price = Column(Integer, nullable=False, default=0, comment="价格（金币）")
    purchase_count = Column(BigInteger, nullable=False, default=0, comment="购买次数")
    total_income = Column(BigInteger, nullable=False, default=0, comment="总收入（金币）")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class SocialDynamicPurchase(Base):
    """动态购买记录表"""
    __tablename__ = "t_social_dynamic_purchase"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="购买记录ID")
    dynamic_id = Column(BigInteger, nullable=False, comment="动态ID")
    buyer_id = Column(BigInteger, nullable=False, comment="购买者用户ID")
    price = Column(Integer, nullable=False, comment="购买价格（金币）")
    purchase_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="购买时间")

