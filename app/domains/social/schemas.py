"""
社交动态模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DynamicBase(BaseModel):
    """动态基础模型"""
    content: str = Field(..., description="动态内容")
    dynamic_type: str = Field(default="text", description="动态类型：text、image、video、share")
    images: Optional[str] = Field(None, description="图片列表，JSON字符串")
    video_url: Optional[str] = Field(None, description="视频URL")
    share_target_type: Optional[str] = Field(None, description="分享目标类型：content、goods")
    share_target_id: Optional[int] = Field(None, description="分享目标ID")
    share_target_title: Optional[str] = Field(None, description="分享目标标题")


class DynamicCreate(DynamicBase):
    """创建动态请求"""
    pass


class DynamicUpdate(BaseModel):
    """更新动态请求"""
    content: Optional[str] = Field(None, description="动态内容")
    dynamic_type: Optional[str] = Field(None, description="动态类型")
    images: Optional[str] = Field(None, description="图片列表，JSON字符串")
    video_url: Optional[str] = Field(None, description="视频URL")
    status: Optional[str] = Field(None, description="状态：normal、hidden、deleted")


class DynamicInfo(DynamicBase):
    """动态信息响应"""
    id: int = Field(..., description="动态ID")
    user_id: int = Field(..., description="发布用户ID")
    user_nickname: Optional[str] = Field(None, description="用户昵称")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    status: str = Field(default="normal", description="状态")
    review_status: str = Field(default="PENDING", description="审核状态：PENDING、APPROVED、REJECTED")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class DynamicReviewStatusInfo(BaseModel):
    """动态审核状态信息"""
    dynamic_id: int = Field(..., description="动态ID")
    content: str = Field(..., description="动态内容")
    dynamic_type: str = Field(..., description="动态类型")
    status: str = Field(..., description="动态状态：normal、hidden、deleted")
    review_status: str = Field(..., description="审核状态：PENDING、APPROVED、REJECTED")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    
    model_config = {"from_attributes": True}


class DynamicReviewStatusQuery(BaseModel):
    """动态审核状态查询参数"""
    dynamic_ids: List[int] = Field(..., description="动态ID列表，最多支持100个")
    
    @field_validator("dynamic_ids")
    @classmethod
    def validate_dynamic_ids(cls, v):
        if len(v) > 100:
            raise ValueError("一次最多查询100个动态的审核状态")
        return v


class DynamicReviewRequest(BaseModel):
    """动态审核请求"""
    dynamic_id: int = Field(..., description="动态ID")
    review_status: str = Field(..., description="审核状态：APPROVED、REJECTED")
    review_comment: Optional[str] = Field(None, description="审核备注")
    
    @field_validator("review_status")
    @classmethod
    def validate_review_status(cls, v):
        if v not in ["APPROVED", "REJECTED"]:
            raise ValueError("审核状态必须是 APPROVED 或 REJECTED")
        return v


class DynamicQuery(BaseModel):
    """动态查询参数"""
    keyword: Optional[str] = Field(None, description="关键词（内容模糊搜索）")
    dynamic_type: Optional[str] = Field(None, description="动态类型")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    status: Optional[str] = Field(None, description="状态过滤")


# ==================== 付费动态相关模型 ====================

class PaidDynamicCreate(BaseModel):
    """创建付费动态请求"""
    dynamic_id: int = Field(..., description="动态ID")
    price: int = Field(..., ge=1, le=10000, description="价格（金币）")
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v < 1:
            raise ValueError("价格必须大于0")
        if v > 10000:
            raise ValueError("价格不能超过10000金币")
        return v


class PaidDynamicInfo(BaseModel):
    """付费动态信息"""
    id: int = Field(description="付费动态ID")
    dynamic_id: int = Field(description="动态ID")
    price: int = Field(description="价格（金币）")
    purchase_count: int = Field(description="购买次数")
    total_income: int = Field(description="总收入（金币）")
    is_active: bool = Field(description="是否激活")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}


class DynamicPurchaseRequest(BaseModel):
    """购买动态请求"""
    dynamic_id: int = Field(..., description="动态ID")


class DynamicPurchaseInfo(BaseModel):
    """动态购买信息"""
    id: int = Field(description="购买记录ID")
    dynamic_id: int = Field(description="动态ID")
    buyer_id: int = Field(description="购买者用户ID")
    price: int = Field(description="购买价格（金币）")
    purchase_time: datetime = Field(description="购买时间")
    
    model_config = {"from_attributes": True}


class DynamicWithPaidInfo(DynamicInfo):
    """带付费信息的动态"""
    is_paid: bool = Field(default=False, description="是否为付费动态")
    price: Optional[int] = Field(None, description="价格（金币）")
    is_purchased: bool = Field(default=False, description="当前用户是否已购买")
    purchase_count: Optional[int] = Field(None, description="购买次数")

