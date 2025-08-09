from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.goods.models import Goods
from app.domains.order.models import Order
from app.domains.order.schemas import OrderCreate, OrderInfo


class OrderCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

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
            if goods.goods_type == "coin":
                raise BusinessException(code=400, message="金币类商品不支持金币支付")
            coin_price = int(getattr(goods, "coin_price", 0) or 0)
            if coin_price <= 0:
                raise BusinessException(code=400, message="该商品不支持金币支付")
            coin_cost = coin_price * quantity

        # 生成订单号（雪花ID）
        from app.common.snowflake import generate_snowflake_id
        order_no = str(generate_snowflake_id())

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

