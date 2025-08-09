"""支付异步服务
对接简化版支付流程：预下单、回调处理、状态查询
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.payment.models import PaymentOrder, PaymentNotifyLog
from app.domains.payment.schemas import PaymentCreate, PaymentInitResponse, PaymentNotify, PaymentInfo
from app.domains.order.async_service import OrderAsyncService
from app.domains.order.models import Order
from app.common.exceptions import BusinessException


class PaymentAsyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, user_id: int, req: PaymentCreate) -> PaymentInitResponse:
        # 校验订单
        order_row = await self.db.execute(select(Order).where(Order.order_no == req.order_no))
        order = order_row.scalar_one_or_none()
        if not order:
            raise BusinessException(code=404, message="订单不存在")
        if order.user_id != user_id:
            raise BusinessException(code=403, message="无权支付该订单")
        if order.pay_status == "paid":
            return PaymentInitResponse(order_no=order.order_no, pay_url=None, status="paid")
        if float(order.final_amount) != float(req.amount):
            raise BusinessException(code=400, message="支付金额不匹配")

        # 创建/更新支付单
        row = await self.db.execute(select(PaymentOrder).where(PaymentOrder.order_no == req.order_no))
        po = row.scalar_one_or_none()
        if not po:
            po = PaymentOrder(
                order_no=req.order_no,
                user_id=user_id,
                channel_code=req.channel_code,
                pay_type=req.pay_type,
                amount=req.amount,
                status="pending",
                pay_url="https://pay.example.com/mock/" + req.order_no,
                expire_time=datetime.now() + timedelta(minutes=30),
                notify_url=req.notify_url,
                return_url=req.return_url,
                request_time=int(datetime.now().timestamp() * 1000),
                create_time=datetime.now(),
                update_time=datetime.now(),
            )
            self.db.add(po)
        else:
            po.channel_code = req.channel_code
            po.pay_type = req.pay_type
            po.amount = req.amount
            po.status = "pending"
            po.pay_url = "https://pay.example.com/mock/" + req.order_no
            po.expire_time = datetime.now() + timedelta(minutes=30)
            po.update_time = datetime.now()

        await self.db.commit()
        return PaymentInitResponse(order_no=req.order_no, pay_url=po.pay_url, status=po.status)

    async def handle_notify(self, notify: PaymentNotify) -> bool:
        # 记录回调
        log = PaymentNotifyLog(
            order_no=notify.order_no,
            platform_order_no=notify.platform_order_no,
            channel_code="shark_pay",
            notify_type="payment",
            notify_data=notify.raw or "",
            notify_sign=notify.sign,
            sign_verify=1,
            process_status="pending",
            notify_time=datetime.now(),
            create_time=datetime.now()
        )
        self.db.add(log)
        await self.db.commit()

        # 更新支付单 & 订单
        row = await self.db.execute(select(PaymentOrder).where(PaymentOrder.order_no == notify.order_no))
        po = row.scalar_one_or_none()
        if not po:
            raise BusinessException(code=404, message="支付单不存在")

        if notify.status == "paid":
            po.status = "paid"
            po.pay_time = datetime.now()
            await self.db.commit()
            # 标记订单已支付
            order_svc = OrderAsyncService(self.db)
            await order_svc.mark_paid(notify.order_no, pay_method=po.pay_type)
            return True
        elif notify.status == "failed":
            po.status = "failed"
            await self.db.commit()
            return True
        else:
            return False

    async def get_payment(self, order_no: str, user_id: int) -> PaymentInfo:
        row = await self.db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
        po = row.scalar_one_or_none()
        if not po:
            raise BusinessException(code=404, message="支付单不存在")
        if po.user_id != user_id:
            raise BusinessException(code=403, message="无权查看该支付单")
        return PaymentInfo.model_validate(po)