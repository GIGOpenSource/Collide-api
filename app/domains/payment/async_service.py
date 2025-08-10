"""支付异步服务
多平台适配：预下单、回调处理、状态查询
为保持清晰，将预下单与回调逻辑拆分到 services/ 下。
"""
from datetime import datetime
from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.payment.models import PaymentOrder
from app.domains.payment.schemas import PaymentCreate, PaymentNotify, PaymentInfo
from app.common.exceptions import BusinessException
from app.domains.payment.adapters import PaymentAdapter
from app.domains.payment.services.init_service import PaymentInitService
from app.domains.payment.services.callback_service import PaymentCallbackService
from app.domains.payment.services.purchase_processor import PaymentPurchaseProcessor
from app.domains.order.async_service import OrderAsyncService

logger = logging.getLogger(__name__)


class PaymentAsyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, user_id: int, req: PaymentCreate, request=None):
        return await PaymentInitService(self.db).create_payment(user_id, req, request)

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
            
            # 处理商品购买成功后的业务逻辑
            try:
                purchase_processor = PaymentPurchaseProcessor(self.db)
                result = await purchase_processor.process_payment_success(notify.order_no)
                if result.get("error"):
                    logger.error(f"处理商品购买逻辑失败: {result['error']}")
                else:
                    logger.info(f"商品购买处理成功: {result}")
            except Exception as e:
                logger.error(f"处理商品购买逻辑异常: {str(e)}", exc_info=True)
            
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

    async def handle_provider_callback(self, adapter: PaymentAdapter, request) -> str:
        return await PaymentCallbackService(self.db).handle_callback(adapter, request)