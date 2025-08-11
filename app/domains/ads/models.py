"""
广告模块数据库模型
与 sql/ads-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Ad(Base):
    """广告表"""
    __tablename__ = "t_ad"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="广告ID")
    ad_name = Column(String(200), nullable=False, comment="广告名称")
    ad_title = Column(String(300), nullable=False, comment="广告标题")
    ad_description = Column(String(500), comment="广告描述")
    
    ad_type = Column(String(50), nullable=False, comment="广告类型：banner、sidebar、popup、feed、game")
    
    image_url = Column(String(1000), nullable=False, comment="广告图片URL")
    click_url = Column(String(1000), nullable=False, comment="点击跳转链接")
    
    alt_text = Column(String(200), comment="图片替代文本")
    target_type = Column(String(30), nullable=False, default="_blank", comment="链接打开方式：_blank、_self")
    
    # 游戏广告专用字段
    game_intro = Column(Text, comment="游戏简介")
    game_detail = Column(Text, comment="游戏详情（支持富文本）")
    game_company = Column(String(200), comment="游戏公司名字")
    game_type = Column(String(100), comment="游戏类型（如：RPG、MOBA、卡牌等，多个类型用逗号分隔）")
    game_rating = Column(Numeric(2, 1), comment="游戏评分（0.0-5.0）")
    game_size = Column(String(50), comment="游戏大小（如：1.2GB）")
    game_version = Column(String(50), comment="游戏版本号")
    game_platform = Column(String(100), comment="游戏平台（如：iOS、Android、PC，多个平台用逗号分隔）")
    game_tags = Column(String(500), comment="游戏标签（多个标签用逗号分隔）")
    game_download_count = Column(BigInteger, default=0, comment="游戏下载次数")
    game_rating_count = Column(BigInteger, default=0, comment="游戏评分人数")
    
    # 下载相关字段
    is_free_download = Column(Boolean, nullable=False, default=True, comment="是否支持普通用户免费下载")
    is_vip_download = Column(Boolean, nullable=False, default=False, comment="是否支持VIP免费下载")
    is_coin_download = Column(Boolean, nullable=False, default=False, comment="是否支持金币购买下载")
    coin_price = Column(BigInteger, default=0, comment="金币价格（当支持金币购买时）")
    original_coin_price = Column(BigInteger, default=0, comment="原价金币（用于折扣显示）")
    download_url = Column(String(1000), comment="下载链接")
    download_platform = Column(String(100), comment="下载平台（如：App Store、Google Play、官网等，多个平台用逗号分隔）")
    download_size = Column(String(50), comment="下载包大小（如：1.2GB）")
    download_version = Column(String(50), comment="下载版本号")
    download_requirements = Column(Text, comment="下载要求（如：系统版本、内存要求等）")
    
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用（1启用，0禁用）")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重（数值越大优先级越高）")
    
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    # 关联关系
    game_images = relationship("GameImage", back_populates="ad", cascade="all, delete-orphan")


class GameImage(Base):
    """游戏图片表"""
    __tablename__ = "t_game_image"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="图片ID")
    ad_id = Column(BigInteger, ForeignKey("t_ad.id"), nullable=False, comment="关联的广告ID")
    image_url = Column(String(1000), nullable=False, comment="图片URL")
    image_type = Column(String(50), comment="图片类型：cover（封面）、banner（横幅）、screenshot（截图）、icon（图标）")
    image_title = Column(String(200), comment="图片标题")
    image_description = Column(String(500), comment="图片描述")
    alt_text = Column(String(200), comment="图片替代文本")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重（数值越大优先级越高）")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用（1启用，0禁用）")
    
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    # 关联关系
    ad = relationship("Ad", back_populates="game_images") 