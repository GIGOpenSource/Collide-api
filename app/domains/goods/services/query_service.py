from typing import List, Optional

from sqlalchemy import and_, or_, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.goods.models import Goods
from app.domains.goods.schemas import GoodsInfo, GoodsQuery


class GoodsQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, goods_id: int) -> GoodsInfo:
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")
        return GoodsInfo.model_validate(goods)

    async def list(self, query: GoodsQuery, pagination: PaginationParams) -> PaginationResult[GoodsInfo]:
        conditions = []
        if query.category_id:
            conditions.append(Goods.category_id == query.category_id)
        if query.goods_type:
            conditions.append(Goods.goods_type == query.goods_type)
        if query.seller_id:
            conditions.append(Goods.seller_id == query.seller_id)
        if query.status:
            conditions.append(Goods.status == query.status)
        if query.keyword:
            conditions.append(or_(
                Goods.name.contains(query.keyword),
                Goods.description.contains(query.keyword),
                Goods.seller_name.contains(query.keyword),
            ))
        if query.min_price is not None:
            conditions.append(Goods.price >= query.min_price)
        if query.max_price is not None:
            conditions.append(Goods.price <= query.max_price)
        if query.min_coin_price is not None:
            conditions.append(Goods.coin_price >= query.min_coin_price)
        if query.max_coin_price is not None:
            conditions.append(Goods.coin_price <= query.max_coin_price)

        stmt = select(Goods).where(and_(*conditions)).order_by(Goods.create_time.desc())
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        goods_list = rows.scalars().all()
        items = [GoodsInfo.model_validate(x) for x in goods_list]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def increase_view_count(self, goods_id: int):
        await self.db.execute(update(Goods).where(Goods.id == goods_id).values(view_count=Goods.view_count + 1))
        await self.db.commit()

    async def increase_sales_count(self, goods_id: int, quantity: int = 1):
        await self.db.execute(update(Goods).where(Goods.id == goods_id).values(sales_count=Goods.sales_count + quantity))
        await self.db.commit()

