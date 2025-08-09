"""
商品模块异步服务层（门面），具体逻辑在 services/ 中
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.goods.schemas import GoodsCreate, GoodsUpdate, GoodsInfo, GoodsQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.goods.services.create_service import GoodsCreateService
from app.domains.goods.services.update_service import GoodsUpdateService
from app.domains.goods.services.query_service import GoodsQueryService


class GoodsAsyncService:
    """商品异步服务类（门面）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_goods(self, req: GoodsCreate) -> GoodsInfo:
        return await GoodsCreateService(self.db).create(req)

    async def update_goods(self, goods_id: int, req: GoodsUpdate) -> GoodsInfo:
        return await GoodsUpdateService(self.db).update(goods_id, req)

    async def delete_goods(self, goods_id: int):
        return await GoodsUpdateService(self.db).delete(goods_id)

    async def get_goods_by_id(self, goods_id: int) -> GoodsInfo:
        return await GoodsQueryService(self.db).get_by_id(goods_id)

    async def get_goods_list(self, query: GoodsQuery, pagination: PaginationParams) -> PaginationResult[GoodsInfo]:
        return await GoodsQueryService(self.db).list(query, pagination)

    async def increase_view_count(self, goods_id: int):
        return await GoodsQueryService(self.db).increase_view_count(goods_id)

    async def increase_sales_count(self, goods_id: int, quantity: int = 1):
        return await GoodsQueryService(self.db).increase_sales_count(goods_id, quantity)

    async def update_stock(self, goods_id: int, quantity: int):
        # 保留在门面内或单独再抽服务（按需）
        from sqlalchemy import select, update
        from app.domains.goods.models import Goods
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            from app.common.exceptions import BusinessException
            raise BusinessException("商品不存在")
        if goods.stock != -1:
            new_stock = goods.stock - quantity
            if new_stock < 0:
                from app.common.exceptions import BusinessException
                raise BusinessException("库存不足")
            await self.db.execute(update(Goods).where(Goods.id == goods_id).values(stock=new_stock))
            await self.db.commit()

    async def get_goods_by_category(self, category_id: int, limit: int = 20) -> List[GoodsInfo]:
        from sqlalchemy import select, and_
        from app.domains.goods.models import Goods
        stmt = select(Goods).where(and_(Goods.category_id == category_id, Goods.status == "active")).order_by(Goods.create_time.desc()).limit(limit)
        rows = await self.db.execute(stmt)
        goods_list = rows.scalars().all()
        return [GoodsInfo.model_validate(g) for g in goods_list]

    async def get_hot_goods(self, goods_type: Optional[str] = None, limit: int = 10) -> List[GoodsInfo]:
        from sqlalchemy import select, and_
        from app.domains.goods.models import Goods
        conditions = [Goods.status == "active"]
        if goods_type:
            conditions.append(Goods.goods_type == goods_type)
        stmt = select(Goods).where(and_(*conditions)).order_by(Goods.sales_count.desc(), Goods.view_count.desc()).limit(limit)
        rows = await self.db.execute(stmt)
        goods_list = rows.scalars().all()
        return [GoodsInfo.model_validate(g) for g in goods_list]