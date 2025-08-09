"""支付 Pydantic 模型"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    """创建支付单请求"""
    order_no: str = Field(..., description="商户订单号")
    channel_code: str = Field(..., description="支付渠道代码")
    pay_type: str = Field(..., description="支付类型：alipay、wechat 等")
    amount: float = Field(..., ge=0, description="支付金额")
    notify_url: Optional[str] = None
    return_url: Optional[str] = None


class PaymentInitResponse(BaseModel):
    """预支付返回"""
    order_no: str
    pay_url: Optional[str]
    status: str


class PaymentNotify(BaseModel):
    """支付回调请求体（聚合大白鲨字段）"""
    order_no: str
    platform_order_no: Optional[str] = None
    status: str
    amount: Optional[float] = None
    sign: Optional[str] = None
    raw: Optional[str] = None


class PaymentInfo(BaseModel):
    id: int
    order_no: str
    platform_order_no: Optional[str]
    user_id: int
    channel_code: str
    pay_type: str
    amount: float
    status: str
    pay_url: Optional[str]
    pay_time: Optional[datetime]
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True