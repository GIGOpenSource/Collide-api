"""订单异步服务
提供下单、查询、列表、取消、支付状态更新等能力
"""
import random
import string
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.order.schemas import OrderCreate, OrderInfo, OrderQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.order.services.create_service import OrderCreateService
from app.domains.order.services.query_service import OrderQueryService
from app.domains.order.services.update_service import OrderUpdateService


class OrderAsyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_order_no(self) -> str:
        # 使用雪花ID生成全局唯一订单号
        from app.common.snowflake import generate_snowflake_id
        return str(generate_snowflake_id())

    async def _ensure_unique_order_no(self) -> str:
        # 尝试多次生成唯一订单号
        for _ in range(5):
            order_no = await self._generate_order_no()
            exists = await self.db.execute(select(Order.id).where(Order.order_no == order_no))
            if exists.scalar_one_or_none() is None:
                return order_no
        raise BusinessException(code=400, message="订单号生成失败，请重试")

    async def create_order(self, user_id: int, user_nickname: Optional[str], req: OrderCreate) -> OrderInfo:
        return await OrderCreateService(self.db).create_order(user_id, user_nickname, req)

    async def get_order(self, order_id: int, user_id: int) -> OrderInfo:
        return await OrderQueryService(self.db).get_order(order_id, user_id)

    async def list_orders(self, user_id: int, q: OrderQuery, p: PaginationParams) -> PaginationResult[OrderInfo]:
        return await OrderQueryService(self.db).list_orders(user_id, q, p)

    async def cancel_order(self, order_id: int, user_id: int) -> bool:
        return await OrderUpdateService(self.db).cancel_order(order_id, user_id)

    async def mark_paid(self, order_no: str, pay_method: Optional[str] = None) -> bool:
        return await OrderUpdateService(self.db).mark_paid(order_no, pay_method)