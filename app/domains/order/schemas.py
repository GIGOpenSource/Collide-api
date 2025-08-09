"""订单 Pydantic 模型"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """创建订单请求"""
    goods_id: int = Field(..., description="商品ID")
    goods_type: str = Field(..., description="商品类型：coin、goods、subscription、content")
    quantity: int = Field(1, ge=1, le=9999, description="购买数量")
    payment_mode: str = Field(..., description="支付模式：cash、coin")


class OrderInfo(BaseModel):
    """订单信息"""
    id: int
    order_no: str
    user_id: int
    user_nickname: Optional[str]
    goods_id: int
    goods_name: Optional[str]
    goods_type: str
    goods_cover: Optional[str]
    goods_category_name: Optional[str]
    coin_amount: Optional[int]
    content_id: Optional[int]
    content_title: Optional[str]
    subscription_duration: Optional[int]
    subscription_type: Optional[str]
    quantity: int
    payment_mode: str
    cash_amount: float
    coin_cost: int
    total_amount: float
    discount_amount: float
    final_amount: float
    status: str
    pay_status: str
    pay_method: Optional[str]
    pay_time: Optional[datetime]
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class OrderQuery(BaseModel):
    """订单查询参数"""
    status: Optional[str] = Field(None, description="订单状态")
    pay_status: Optional[str] = Field(None, description="支付状态")
    goods_type: Optional[str] = Field(None, description="商品类型")