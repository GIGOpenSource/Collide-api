"""
内容模块 Pydantic 数据模型
用于 API 请求和响应的数据验证
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, field_serializer


# ================ 枚举类型 ================

class ContentType(str):
    """内容类型枚举"""
    NOVEL = "NOVEL"
    COMIC = "COMIC"
    VIDEO = "VIDEO"
    ARTICLE = "ARTICLE"
    AUDIO = "AUDIO"


class ContentStatus(str):
    """内容状态枚举"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    OFFLINE = "OFFLINE"


class ReviewStatus(str):
    """审核状态枚举"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChapterStatus(str):
    """章节状态枚举"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class PaymentType(str):
    """付费类型枚举"""
    FREE = "FREE"
    COIN_PAY = "COIN_PAY"
    VIP_FREE = "VIP_FREE"
    TIME_LIMITED = "TIME_LIMITED"


class PurchaseStatus(str):
    """购买状态枚举"""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"


# ================ 基础数据模型 ================

class ContentBase(BaseModel):
    """内容基础模型"""
    title: str = Field(..., max_length=200, description="内容标题")
    description: Optional[str] = Field(None, description="内容描述")
    content_type: Literal["NOVEL", "COMIC", "LONG_VIDEO", "SHORT_VIDEO", "ARTICLE", "AUDIO"] = Field(
        ..., description="内容类型：NOVEL、COMIC、LONG_VIDEO、SHORT_VIDEO、ARTICLE、AUDIO"
    )
    content_data: Optional[str] = Field(None, max_length=500, description="内容数据URL")
    content_data_time: Optional[str] = Field(None, max_length=500, description="内容数据时长（秒）")
    cover_url: Optional[str] = Field(None, max_length=500, description="封面图片URL")
    tags: Optional[str] = Field(None, description="标签，逗号分隔或JSON格式")
    category_id: Optional[int] = Field(None, description="分类ID")
    category_name: Optional[str] = Field(None, max_length=100, description="分类名称")

    @field_validator("content_type", mode="before")
    @classmethod
    def _normalize_content_type(cls, v):
        if isinstance(v, str):
            upper_v = v.upper()
            if upper_v == "VIDEO":
                return "LONG_VIDEO"
            return upper_v
        return v


class ContentCreate(ContentBase):
    """创建内容请求模型"""
    # 作者信息会从当前用户上下文获取，不需要在请求中提供
    pass


class ContentUpdate(BaseModel):
    """更新内容请求模型"""
    title: Optional[str] = Field(None, max_length=200, description="内容标题")
    description: Optional[str] = Field(None, description="内容描述")
    content_data: Optional[str] = Field(None, max_length=500, description="内容数据URL")
    content_data_time: Optional[str] = Field(None, max_length=500, description="内容数据时长（秒）")
    cover_url: Optional[str] = Field(None, max_length=500, description="封面图片URL")
    tags: Optional[str] = Field(None, description="标签")
    category_id: Optional[int] = Field(None, description="分类ID")
    category_name: Optional[str] = Field(None, max_length=100, description="分类名称")
    # status: Optional[str] = Field(None, description="状态") # 状态应由专门接口控制，如发布、下线


class ContentInfo(ContentBase):
    """内容信息响应模型"""
    id: int = Field(..., description="内容ID")
    author_id: int = Field(..., description="作者用户ID")
    author_nickname: Optional[str] = Field(None, description="作者昵称")
    author_avatar: Optional[str] = Field(None, description="作者头像URL")
    status: str = Field(..., description="状态")
    review_status: str = Field(..., description="审核状态")
    
    # 统计字段
    view_count: int = Field(default=0, description="查看数")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    favorite_count: int = Field(default=0, description="收藏数")
    score_count: int = Field(default=0, description="评分数")
    score_total: int = Field(default=0, description="总评分")
    
    # 时间字段
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    # 计算属性
    average_score: Optional[float] = Field(None, description="平均评分")
    
    model_config = {"from_attributes": True}
    
    @field_serializer('publish_time', 'create_time', 'update_time')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """序列化时间字段为指定格式"""
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def __init__(self, **data):
        super().__init__(**data)
        # 计算平均评分
        if self.score_count > 0:
            self.average_score = round(self.score_total / self.score_count, 1)


# ================ 章节相关模型 ================

class ChapterBase(BaseModel):
    """章节基础模型"""
    chapter_num: int = Field(..., description="章节号")
    title: str = Field(..., max_length=200, description="章节标题")
    content: Optional[str] = Field(None, description="章节内容")
    word_count: int = Field(default=0, description="字数")


class ChapterCreate(ChapterBase):
    """创建章节请求模型"""
    content_id: int = Field(..., description="内容ID")


class ChapterUpdate(BaseModel):
    """更新章节请求模型"""
    title: Optional[str] = Field(None, max_length=200, description="章节标题")
    content: Optional[str] = Field(None, description="章节内容")
    word_count: Optional[int] = Field(None, description="字数")
    status: Optional[str] = Field(None, description="状态")


class ChapterInfo(ChapterBase):
    """章节信息响应模型"""
    id: int = Field(..., description="章节ID")
    content_id: int = Field(..., description="内容ID")
    status: str = Field(..., description="状态")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    model_config = {"from_attributes": True}
    
    @field_serializer('create_time', 'update_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class ChapterListItem(BaseModel):
    """章节列表项模型（不包含内容）"""
    id: int = Field(..., description="章节ID")
    chapter_num: int = Field(..., description="章节号")
    title: str = Field(..., description="章节标题")
    word_count: int = Field(..., description="字数")
    status: str = Field(..., description="状态")
    create_time: datetime = Field(..., description="创建时间")
    
    model_config = {"from_attributes": True}
    
    @field_serializer('create_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# ================ 付费配置相关模型 ================

class ContentPaymentBase(BaseModel):
    """内容付费配置基础模型"""
    payment_type: str = Field(default="FREE", description="付费类型")
    coin_price: int = Field(default=0, description="金币价格")
    original_price: Optional[int] = Field(None, description="原价")
    vip_free: int = Field(default=0, description="会员免费：0否，1是")
    vip_only: int = Field(default=0, description="是否只有VIP才能购买：0否，1是")
    trial_enabled: int = Field(default=0, description="是否支持试读：0否，1是")
    trial_content: Optional[str] = Field(None, description="试读内容")
    trial_word_count: int = Field(default=0, description="试读字数")
    is_permanent: int = Field(default=1, description="是否永久有效：0否，1是")
    valid_days: Optional[int] = Field(None, description="有效天数")


class ContentPaymentCreate(ContentPaymentBase):
    """创建付费配置请求模型"""
    content_id: int = Field(..., description="内容ID")


class ContentPaymentUpdate(BaseModel):
    """更新付费配置请求模型"""
    payment_type: Optional[str] = Field(None, description="付费类型")
    coin_price: Optional[int] = Field(None, description="金币价格")
    original_price: Optional[int] = Field(None, description="原价")
    vip_free: Optional[int] = Field(None, description="会员免费")
    vip_only: Optional[int] = Field(None, description="是否只有VIP才能购买")
    trial_enabled: Optional[int] = Field(None, description="是否支持试读")
    trial_content: Optional[str] = Field(None, description="试读内容")
    trial_word_count: Optional[int] = Field(None, description="试读字数")
    is_permanent: Optional[int] = Field(None, description="是否永久有效")
    valid_days: Optional[int] = Field(None, description="有效天数")
    status: Optional[str] = Field(None, description="状态")


class ContentPaymentInfo(ContentPaymentBase):
    """付费配置信息响应模型"""
    id: int = Field(..., description="配置ID")
    content_id: int = Field(..., description="内容ID")
    total_sales: int = Field(default=0, description="总销量")
    total_revenue: int = Field(default=0, description="总收入")
    status: str = Field(..., description="状态")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    model_config = {"from_attributes": True}
    
    @field_serializer('create_time', 'update_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# ================ 购买记录相关模型 ================

class UserContentPurchaseBase(BaseModel):
    """用户内容购买记录基础模型"""
    content_id: int = Field(..., description="内容ID")
    coin_amount: int = Field(..., description="支付金币数量")
    original_price: Optional[int] = Field(None, description="原价金币")
    discount_amount: int = Field(default=0, description="优惠金币数量")


class UserContentPurchaseCreate(UserContentPurchaseBase):
    """创建购买记录请求模型"""
    order_id: Optional[int] = Field(None, description="关联订单ID")
    order_no: Optional[str] = Field(None, description="订单号")


class UserContentPurchaseInfo(UserContentPurchaseBase):
    """购买记录信息响应模型"""
    id: int = Field(..., description="购买记录ID")
    user_id: int = Field(..., description="用户ID")
    content_title: Optional[str] = Field(None, description="内容标题")
    content_type: Optional[str] = Field(None, description="内容类型")
    content_cover_url: Optional[str] = Field(None, description="内容封面")
    author_id: Optional[int] = Field(None, description="作者ID")
    author_nickname: Optional[str] = Field(None, description="作者昵称")
    order_id: Optional[int] = Field(None, description="关联订单ID")
    order_no: Optional[str] = Field(None, description="订单号")
    status: str = Field(..., description="状态")
    purchase_time: datetime = Field(..., description="购买时间")
    expire_time: Optional[datetime] = Field(None, description="过期时间")
    access_count: int = Field(default=0, description="访问次数")
    last_access_time: Optional[datetime] = Field(None, description="最后访问时间")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(None, description="更新时间")
    
    model_config = {"from_attributes": True}
    
    @field_serializer('purchase_time', 'expire_time', 'last_access_time', 'create_time', 'update_time')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """序列化时间字段为指定格式"""
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# ================ 查询参数模型 ================

class ContentQueryParams(BaseModel):
    """内容查询参数"""
    content_type: Optional[Literal["NOVEL", "COMIC", "LONG_VIDEO", "SHORT_VIDEO", "ARTICLE", "AUDIO"]] = Field(
        None, description="内容类型：NOVEL、COMIC、LONG_VIDEO、SHORT_VIDEO、ARTICLE、AUDIO"
    )
    category_id: Optional[int] = Field(None, description="分类ID")
    author_id: Optional[int] = Field(None, description="作者ID")
    # status: Optional[str] = Field(None, description="状态")
    # review_status: Optional[str] = Field(None, description="审核状态")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    
    # 统计数据筛选条件
    min_view_count: Optional[int] = Field(None, ge=0, description="最小浏览量")
    max_view_count: Optional[int] = Field(None, ge=0, description="最大浏览量")
    min_like_count: Optional[int] = Field(None, ge=0, description="最小点赞数")
    max_like_count: Optional[int] = Field(None, ge=0, description="最大点赞数")
    min_favorite_count: Optional[int] = Field(None, ge=0, description="最小收藏数")
    max_favorite_count: Optional[int] = Field(None, ge=0, description="最大收藏数")
    min_comment_count: Optional[int] = Field(None, ge=0, description="最小评论数")
    max_comment_count: Optional[int] = Field(None, ge=0, description="最大评论数")
    min_score: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    max_score: Optional[float] = Field(None, ge=0, le=5, description="最高评分")
    
    # 时间筛选条件
    publish_date_start: Optional[str] = Field(None, description="发布开始日期 (YYYY-MM-DD)")
    publish_date_end: Optional[str] = Field(None, description="发布结束日期 (YYYY-MM-DD)")
    create_date_start: Optional[str] = Field(None, description="创建开始日期 (YYYY-MM-DD)")
    create_date_end: Optional[str] = Field(None, description="创建结束日期 (YYYY-MM-DD)")
    
    # 付费筛选条件
    is_free: Optional[bool] = Field(None, description="是否免费内容")
    is_vip_free: Optional[bool] = Field(None, description="是否会员免费")
    
    # 标签筛选
    tags: Optional[str] = Field(None, description="标签筛选，多个标签用逗号分隔")
    
    sort_by: str = Field(default="create_time", description="排序字段：create_time, update_time, publish_time, view_count, like_count, favorite_count, comment_count, score")
    sort_order: str = Field(default="desc", description="排序方向：asc, desc")
    
    @field_validator("content_type", mode="before")
    @classmethod
    def _normalize_query_content_type(cls, v):
        if isinstance(v, str):
            upper_v = v.upper()
            if upper_v == "VIDEO":
                return "LONG_VIDEO"
            return upper_v
        return v


# ================ 其他请求模型 ================

class PublishContentRequest(BaseModel):
    """发布内容请求模型"""
    publish_time: Optional[datetime] = Field(None, description="发布时间，为空表示立即发布")


class ContentStatsUpdate(BaseModel):
    """内容统计更新模型"""
    increment_type: str = Field(..., description="增量类型：view、like、comment、share、favorite")
    increment_value: int = Field(default=1, description="增量值")


class ScoreContentRequest(BaseModel):
    """内容评分请求模型"""
    score: int = Field(..., ge=1, le=5, description="评分：1-5分")


# ================ 审核状态相关模型 ================

class ContentReviewStatusInfo(BaseModel):
    """内容审核状态信息"""
    content_id: int = Field(..., description="内容ID")
    title: str = Field(..., description="内容标题")
    content_type: str = Field(..., description="内容类型")
    status: str = Field(..., description="内容状态：DRAFT、PUBLISHED、OFFLINE")
    review_status: str = Field(..., description="审核状态：PENDING、APPROVED、REJECTED")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    model_config = {"from_attributes": True}
    
    @field_serializer('create_time', 'update_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class ContentReviewStatusQuery(BaseModel):
    """内容审核状态查询参数"""
    content_ids: List[int] = Field(..., description="内容ID列表，最多支持100个")
    
    @field_validator("content_ids")
    @classmethod
    def validate_content_ids(cls, v):
        if len(v) > 100:
            raise ValueError("一次最多查询100个内容的审核状态")
        return v
