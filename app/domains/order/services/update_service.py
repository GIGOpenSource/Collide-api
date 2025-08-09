from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.order.models import Order


class OrderUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def cancel_order(self, order_id: int, user_id: int) -> bool:
        row = await self.db.execute(select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)))
        order = row.scalar_one_or_none()
        if not order:
            raise BusinessException(code=404, message="订单不存在")
        if order.status in ("paid", "shipped", "completed"):
            raise BusinessException(code=400, message="订单当前状态不可取消")
        order.status = "cancelled"
        await self.db.commit()
        return True

    async def mark_paid(self, order_no: str, pay_method: Optional[str] = None) -> bool:
        row = await self.db.execute(select(Order).where(Order.order_no == order_no))
        order = row.scalar_one_or_none()
        if not order:
            raise BusinessException(code=404, message="订单不存在")
        if order.pay_status == "paid":
            return True
        order.pay_status = "paid"
        order.status = "paid"
        order.pay_method = pay_method
        order.pay_time = datetime.now()
        await self.db.commit()
        return True

