from typing import Optional

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.order.models import Order
from app.domains.order.schemas import OrderInfo, OrderQuery


class OrderQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order(self, order_id: int, user_id: int) -> OrderInfo:
        row = await self.db.execute(select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)))
        order = row.scalar_one_or_none()
        if not order:
            raise BusinessException(code=404, message="订单不存在")
        return OrderInfo.model_validate(order)

    async def list_orders(self, user_id: int, q: OrderQuery, p: PaginationParams) -> PaginationResult[OrderInfo]:
        filters = [Order.user_id == user_id]
        if q.status:
            filters.append(Order.status == q.status)
        if q.pay_status:
            filters.append(Order.pay_status == q.pay_status)
        if q.goods_type:
            filters.append(Order.goods_type == q.goods_type)

        base_stmt = select(Order).where(and_(*filters)).order_by(Order.id.desc())
        count_stmt = select(func.count()).select_from(select(Order.id).where(and_(*filters)).subquery())

        total = (await self.db.execute(count_stmt)).scalar_one()
        items_stmt = base_stmt.offset((p.page - 1) * p.page_size).limit(p.page_size)
        rows = await self.db.execute(items_stmt)
        orders = rows.scalars().all()
        items = [OrderInfo.model_validate(o) for o in orders]
        return PaginationResult(items=items, total=total, page=p.page, page_size=p.page_size)

