"""
广告模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer


class AdCreate(BaseModel):
    """创建广告请求"""
    ad_name: str = Field(..., description="广告名称")
    ad_title: str = Field(..., description="广告标题")
    ad_description: Optional[str] = Field(None, description="广告描述")
    ad_type: str = Field(..., description="广告类型：banner、sidebar、popup、feed、game")
    image_url: str = Field(..., description="广告图片URL")
    click_url: str = Field(..., description="点击跳转链接")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    target_type: str = Field("_blank", description="链接打开方式：_blank、_self")
    
    # 游戏广告专用字段
    game_intro: Optional[str] = Field(None, description="游戏简介")
    game_detail: Optional[str] = Field(None, description="游戏详情（支持富文本）")
    game_company: Optional[str] = Field(None, description="游戏公司名字")
    game_type: Optional[str] = Field(None, description="游戏类型（如：RPG、MOBA、卡牌等，多个类型用逗号分隔）")
    game_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="游戏评分（0.0-5.0）")
    game_size: Optional[str] = Field(None, description="游戏大小（如：1.2GB）")
    game_version: Optional[str] = Field(None, description="游戏版本号")
    game_platform: Optional[str] = Field(None, description="游戏平台（如：iOS、Android、PC，多个平台用逗号分隔）")
    game_tags: Optional[str] = Field(None, description="游戏标签（多个标签用逗号分隔）")
    
    # 下载相关字段
    is_free_download: bool = Field(True, description="是否支持普通用户免费下载")
    is_vip_download: bool = Field(False, description="是否支持VIP免费下载")
    is_coin_download: bool = Field(False, description="是否支持金币购买下载")
    coin_price: int = Field(0, ge=0, description="金币价格（当支持金币购买时）")
    original_coin_price: int = Field(0, ge=0, description="原价金币（用于折扣显示）")
    download_url: Optional[str] = Field(None, description="下载链接")
    download_platform: Optional[str] = Field(None, description="下载平台（如：App Store、Google Play、官网等，多个平台用逗号分隔）")
    download_size: Optional[str] = Field(None, description="下载包大小（如：1.2GB）")
    download_version: Optional[str] = Field(None, description="下载版本号")
    download_requirements: Optional[str] = Field(None, description="下载要求（如：系统版本、内存要求等）")
    
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序权重")


class AdUpdate(BaseModel):
    """更新广告请求"""
    ad_name: Optional[str] = Field(None, description="广告名称")
    ad_title: Optional[str] = Field(None, description="广告标题")
    ad_description: Optional[str] = Field(None, description="广告描述")
    ad_type: Optional[str] = Field(None, description="广告类型")
    image_url: Optional[str] = Field(None, description="广告图片URL")
    click_url: Optional[str] = Field(None, description="点击跳转链接")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    target_type: Optional[str] = Field(None, description="链接打开方式")
    
    # 游戏广告专用字段
    game_intro: Optional[str] = Field(None, description="游戏简介")
    game_detail: Optional[str] = Field(None, description="游戏详情（支持富文本）")
    game_company: Optional[str] = Field(None, description="游戏公司名字")
    game_type: Optional[str] = Field(None, description="游戏类型（如：RPG、MOBA、卡牌等，多个类型用逗号分隔）")
    game_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="游戏评分（0.0-5.0）")
    game_size: Optional[str] = Field(None, description="游戏大小（如：1.2GB）")
    game_version: Optional[str] = Field(None, description="游戏版本号")
    game_platform: Optional[str] = Field(None, description="游戏平台（如：iOS、Android、PC，多个平台用逗号分隔）")
    game_tags: Optional[str] = Field(None, description="游戏标签（多个标签用逗号分隔）")
    
    # 下载相关字段
    is_free_download: Optional[bool] = Field(None, description="是否支持普通用户免费下载")
    is_vip_download: Optional[bool] = Field(None, description="是否支持VIP免费下载")
    is_coin_download: Optional[bool] = Field(None, description="是否支持金币购买下载")
    coin_price: Optional[int] = Field(None, ge=0, description="金币价格（当支持金币购买时）")
    original_coin_price: Optional[int] = Field(None, ge=0, description="原价金币（用于折扣显示）")
    download_url: Optional[str] = Field(None, description="下载链接")
    download_platform: Optional[str] = Field(None, description="下载平台（如：App Store、Google Play、官网等，多个平台用逗号分隔）")
    download_size: Optional[str] = Field(None, description="下载包大小（如：1.2GB）")
    download_version: Optional[str] = Field(None, description="下载版本号")
    download_requirements: Optional[str] = Field(None, description="下载要求（如：系统版本、内存要求等）")
    
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序权重")


class AdInfo(BaseModel):
    """广告信息"""
    id: int = Field(..., description="广告ID")
    ad_name: str = Field(..., description="广告名称")
    ad_title: str = Field(..., description="广告标题")
    ad_description: Optional[str] = Field(None, description="广告描述")
    ad_type: str = Field(..., description="广告类型")
    image_url: str = Field(..., description="广告图片URL")
    click_url: str = Field(..., description="点击跳转链接")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    target_type: str = Field(..., description="链接打开方式")
    
    # 游戏广告专用字段
    game_intro: Optional[str] = Field(None, description="游戏简介")
    game_detail: Optional[str] = Field(None, description="游戏详情（支持富文本）")
    game_company: Optional[str] = Field(None, description="游戏公司名字")
    game_type: Optional[str] = Field(None, description="游戏类型（如：RPG、MOBA、卡牌等，多个类型用逗号分隔）")
    game_rating: Optional[Decimal] = Field(None, description="游戏评分（0.0-5.0）")
    game_size: Optional[str] = Field(None, description="游戏大小（如：1.2GB）")
    game_version: Optional[str] = Field(None, description="游戏版本号")
    game_platform: Optional[str] = Field(None, description="游戏平台（如：iOS、Android、PC，多个平台用逗号分隔）")
    game_tags: Optional[str] = Field(None, description="游戏标签（多个标签用逗号分隔）")
    game_download_count: int = Field(default=0, description="游戏下载次数")
    game_rating_count: int = Field(default=0, description="游戏评分人数")
    
    # 下载相关字段
    is_free_download: bool = Field(default=True, description="是否支持普通用户免费下载")
    is_vip_download: bool = Field(default=False, description="是否支持VIP免费下载")
    is_coin_download: bool = Field(default=False, description="是否支持金币购买下载")
    coin_price: int = Field(default=0, description="金币价格（当支持金币购买时）")
    original_coin_price: int = Field(default=0, description="原价金币（用于折扣显示）")
    download_url: Optional[str] = Field(None, description="下载链接")
    download_platform: Optional[str] = Field(None, description="下载平台（如：App Store、Google Play、官网等，多个平台用逗号分隔）")
    download_size: Optional[str] = Field(None, description="下载包大小（如：1.2GB）")
    download_version: Optional[str] = Field(None, description="下载版本号")
    download_requirements: Optional[str] = Field(None, description="下载要求（如：系统版本、内存要求等）")
    
    is_active: bool = Field(..., description="是否启用")
    sort_order: int = Field(..., description="排序权重")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}
    
    @field_serializer('create_time', 'update_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class AdQuery(BaseModel):
    """广告查询参数"""
    ad_type: Optional[str] = Field(None, description="广告类型")
    is_active: Optional[bool] = Field(None, description="是否启用")
    keyword: Optional[str] = Field(None, description="关键词搜索") 
    # 扩展多条件
    ad_types: Optional[List[str]] = Field(None, description="广告类型集合，OR 关系")
    ad_name: Optional[str] = Field(None, description="广告名称，模糊匹配")
    ad_title: Optional[str] = Field(None, description="广告标题，模糊匹配")
    target_type: Optional[str] = Field(None, description="链接打开方式筛选：_blank/_self")
    start_time: Optional[datetime] = Field(None, description="创建时间起")
    end_time: Optional[datetime] = Field(None, description="创建时间止")
    min_sort: Optional[int] = Field(None, description="最小排序权重")
    max_sort: Optional[int] = Field(None, description="最大排序权重")
    
    # 游戏广告查询参数
    game_company: Optional[str] = Field(None, description="游戏公司名字，模糊匹配")
    game_type: Optional[str] = Field(None, description="游戏类型，模糊匹配")
    game_platform: Optional[str] = Field(None, description="游戏平台，模糊匹配")
    min_game_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="最小游戏评分")
    max_game_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="最大游戏评分")
    min_game_download_count: Optional[int] = Field(None, ge=0, description="最小游戏下载次数")
    max_game_download_count: Optional[int] = Field(None, ge=0, description="最大游戏下载次数")
    
    # 下载相关查询参数
    is_free_download: Optional[bool] = Field(None, description="是否支持普通用户免费下载")
    is_vip_download: Optional[bool] = Field(None, description="是否支持VIP免费下载")
    is_coin_download: Optional[bool] = Field(None, description="是否支持金币购买下载")
    min_coin_price: Optional[int] = Field(None, ge=0, description="最小金币价格")
    max_coin_price: Optional[int] = Field(None, ge=0, description="最大金币价格")
    download_platform: Optional[str] = Field(None, description="下载平台，模糊匹配")


# ================ 游戏图片相关模型 ================

class GameImageCreate(BaseModel):
    """创建游戏图片请求"""
    image_url: str = Field(..., description="图片URL")
    image_type: str = Field(..., description="图片类型：cover（封面）、banner（横幅）、screenshot（截图）、icon（图标）")
    image_title: Optional[str] = Field(None, description="图片标题")
    image_description: Optional[str] = Field(None, description="图片描述")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    sort_order: int = Field(0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")


class GameImageCreateWithAdId(BaseModel):
    """创建游戏图片请求（包含广告ID）"""
    ad_id: int = Field(..., description="关联的广告ID")
    image_url: str = Field(..., description="图片URL")
    image_type: str = Field(..., description="图片类型：cover（封面）、banner（横幅）、screenshot（截图）、icon（图标）")
    image_title: Optional[str] = Field(None, description="图片标题")
    image_description: Optional[str] = Field(None, description="图片描述")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    sort_order: int = Field(0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")


class GameImageUpdate(BaseModel):
    """更新游戏图片请求"""
    image_url: Optional[str] = Field(None, description="图片URL")
    image_type: Optional[str] = Field(None, description="图片类型")
    image_title: Optional[str] = Field(None, description="图片标题")
    image_description: Optional[str] = Field(None, description="图片描述")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    sort_order: Optional[int] = Field(None, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否启用")


class GameImageInfo(BaseModel):
    """游戏图片信息"""
    id: int = Field(..., description="图片ID")
    ad_id: int = Field(..., description="关联的广告ID")
    image_url: str = Field(..., description="图片URL")
    image_type: str = Field(None, description="图片类型")
    image_title: Optional[str] = Field(None, description="图片标题")
    image_description: Optional[str] = Field(None, description="图片描述")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    sort_order: int = Field(..., description="排序权重")
    is_active: bool = Field(..., description="是否启用")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}
    
    @field_serializer('create_time', 'update_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class GameAdInfo(AdInfo):
    """游戏广告信息（包含图片数组）"""
    game_images: List[GameImageInfo] = Field(default_factory=list, description="游戏图片列表")


class GameImageBatchCreate(BaseModel):
    """批量创建游戏图片请求"""
    ad_id: int = Field(..., description="关联的广告ID")
    images: List[GameImageCreate] = Field(..., description="图片列表")