from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.order.async_service import OrderAsyncService
from app.domains.payment.adapters import PaymentAdapter
from app.domains.payment.models import PaymentChannel, PaymentOrder, PaymentNotifyLog


class PaymentCallbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_callback(self, adapter: PaymentAdapter, request) -> str:
        body_bytes = await request.body()
        raw_text = body_bytes.decode("utf-8") if body_bytes else ""
        trade_no = adapter.extract_order_no(raw_text) or ""

        channel_cfg: Dict[str, Any] | None = None
        channel_code = ""
        if trade_no:
            row = await self.db.execute(select(PaymentOrder).where(PaymentOrder.order_no == trade_no))
            po = row.scalar_one_or_none()
            if po:
                channel_row = await self.db.execute(select(PaymentChannel).where(PaymentChannel.channel_code == po.channel_code))
                channel = channel_row.scalar_one_or_none()
                if channel:
                    channel_cfg = {"merchant_id": channel.merchant_id, "app_secret": channel.app_secret}
                    channel_code = channel.channel_code

        if channel_cfg is None:
            merc_id = adapter.extract_merc_id(raw_text)
            if merc_id:
                channel_row = await self.db.execute(select(PaymentChannel).where(PaymentChannel.merchant_id == merc_id))
                channel = channel_row.scalar_one_or_none()
                if channel:
                    channel_cfg = {"merchant_id": channel.merchant_id, "app_secret": channel.app_secret}
                    channel_code = channel.channel_code

        if channel_cfg is None:
            return "fail"

        normalized = adapter.verify_and_parse_callback_from_raw(raw_text, channel_cfg)
        log = PaymentNotifyLog(
            order_no=normalized.order_no,
            platform_order_no=normalized.platform_order_no,
            channel_code=channel_code or "",
            notify_type="payment",
            notify_data=normalized.raw,
            notify_sign=normalized.sign,
            sign_verify=1 if normalized.extra.get("verified") else 0,
            process_status="pending",
            notify_time=datetime.now(),
            create_time=datetime.now(),
        )
        self.db.add(log)
        await self.db.commit()

        row = await self.db.execute(select(PaymentOrder).where(PaymentOrder.order_no == normalized.order_no))
        po = row.scalar_one_or_none()
        if not po:
            return adapter.success_response_text()

        if normalized.status == "paid":
            if po.status != "paid":
                po.status = "paid"
                po.actual_amount = normalized.actual_amount
                po.platform_order_no = normalized.platform_order_no
                po.pay_time = normalized.pay_time or datetime.now()
                po.notify_time = datetime.now()
                await self.db.commit()
                order_svc = OrderAsyncService(self.db)
                await order_svc.mark_paid(normalized.order_no, pay_method=po.pay_type)
        elif normalized.status == "failed":
            if po.status not in ("paid", "failed"):
                po.status = "failed"
                po.notify_time = datetime.now()
                await self.db.commit()

        return adapter.success_response_text()

