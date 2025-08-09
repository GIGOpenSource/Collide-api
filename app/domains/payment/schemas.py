"""支付 Pydantic 模型"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    """创建支付单请求（安全版）
    不信任前端金额，仅传 orderId 与 userId，金额由后端根据订单计算。
    """
    order_id: int = Field(..., description="订单ID")
    user_id: int = Field(..., description="用户ID")
    channel_code: str = Field(..., description="支付渠道代码")
    pay_type: str = Field(..., description="支付类型：alipay、wechat 等")
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