from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.goods.models import Goods
from app.domains.goods.schemas import GoodsUpdate, GoodsInfo


class GoodsUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update(self, goods_id: int, req: GoodsUpdate) -> GoodsInfo:
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")

        update_data = {}
        if req.name is not None:
            update_data["name"] = req.name
        if req.description is not None:
            update_data["description"] = req.description
        if req.category_id is not None:
            update_data["category_id"] = req.category_id
        if req.goods_type is not None:
            update_data["goods_type"] = req.goods_type
        if req.price is not None:
            update_data["price"] = req.price
        if req.original_price is not None:
            update_data["original_price"] = req.original_price
        if req.coin_price is not None:
            update_data["coin_price"] = req.coin_price
        if req.coin_amount is not None:
            update_data["coin_amount"] = req.coin_amount
        if req.content_id is not None:
            update_data["content_id"] = req.content_id
        if req.subscription_duration is not None:
            update_data["subscription_duration"] = req.subscription_duration
        if req.subscription_type is not None:
            update_data["subscription_type"] = req.subscription_type
        if req.stock is not None:
            update_data["stock"] = req.stock
        if req.cover_url is not None:
            update_data["cover_url"] = req.cover_url
        if req.images is not None:
            update_data["images"] = req.images
        if req.seller_name is not None:
            update_data["seller_name"] = req.seller_name
        if req.status is not None:
            update_data["status"] = req.status

        await self.db.execute(update(Goods).where(Goods.id == goods_id).values(**update_data))
        await self.db.commit()
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one()
        return GoodsInfo.model_validate(goods)

    async def delete(self, goods_id: int) -> bool:
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")
        await self.db.execute(delete(Goods).where(Goods.id == goods_id))
        await self.db.commit()
        return True

