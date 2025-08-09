"""订单异步服务
提供下单、查询、列表、取消、支付状态更新等能力
"""
import random
import string
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.domains.order.models import Order
from app.domains.order.schemas import OrderCreate, OrderInfo, OrderQuery
from app.domains.goods.models import Goods
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException


class OrderAsyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_order_no(self) -> str:
        prefix = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"O{prefix}{suffix}"

    async def _ensure_unique_order_no(self) -> str:
        # 尝试多次生成唯一订单号
        for _ in range(5):
            order_no = await self._generate_order_no()
            exists = await self.db.execute(select(Order.id).where(Order.order_no == order_no))
            if exists.scalar_one_or_none() is None:
                return order_no
        raise BusinessException(code=400, message="订单号生成失败，请重试")

    async def create_order(self, user_id: int, user_nickname: Optional[str], req: OrderCreate) -> OrderInfo:
        # 获取商品
        goods_row = await self.db.execute(select(Goods).where(Goods.id == req.goods_id))
        goods: Optional[Goods] = goods_row.scalar_one_or_none()
        if not goods:
            raise BusinessException(code=404, message="商品不存在")

        if goods.goods_type != req.goods_type:
            raise BusinessException(code=400, message="商品类型不匹配")

        if req.payment_mode not in ("cash", "coin"):
            raise BusinessException(code=400, message="支付模式不合法")

        # 金额计算（简化版，未含优惠券/折扣策略）
        quantity = max(1, req.quantity)
        price = float(goods.price or 0)
        total_amount = round(price * quantity, 2)
        discount_amount = 0.0
        final_amount = round(total_amount - discount_amount, 2)

        cash_amount = 0.0
        coin_cost = 0
        if req.payment_mode == "cash":
            cash_amount = final_amount
        else:  # coin 模式
            # 使用金币价格（如为内容/商品类，使用 coin_price；金币类不支持 coin 支付）
            if goods.goods_type == "coin":
                raise BusinessException(code=400, message="金币类商品不支持金币支付")
            coin_price = int(goods.coin_price or 0)
            if coin_price <= 0:
                raise BusinessException(code=400, message="该商品不支持金币支付")
            coin_cost = coin_price * quantity

        order_no = await self._ensure_unique_order_no()

        order = Order(
            order_no=order_no,
            user_id=user_id,
            user_nickname=user_nickname,
            goods_id=goods.id,
            goods_name=goods.name,
            goods_type=goods.goods_type,
            goods_cover=getattr(goods, "cover_url", None),
            goods_category_name=goods.category_name,
            coin_amount=goods.coin_amount if goods.goods_type == "coin" else None,
            content_id=goods.content_id if goods.goods_type == "content" else None,
            content_title=goods.content_title if goods.goods_type == "content" else None,
            subscription_duration=goods.subscription_duration if goods.goods_type == "subscription" else None,
            subscription_type=goods.subscription_type if goods.goods_type == "subscription" else None,
            quantity=quantity,
            payment_mode=req.payment_mode,
            cash_amount=cash_amount,
            coin_cost=coin_cost,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            status="pending",
            pay_status="unpaid",
            pay_method=None,
            pay_time=None,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return OrderInfo.model_validate(order)

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