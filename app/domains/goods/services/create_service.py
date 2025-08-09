from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.goods.models import Goods
from app.domains.goods.schemas import GoodsCreate, GoodsInfo


class GoodsCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, req: GoodsCreate) -> GoodsInfo:
        await self._validate_goods_type_fields(req)
        goods = Goods(
            name=req.name,
            description=req.description,
            category_id=req.category_id,
            goods_type=req.goods_type,
            price=req.price,
            original_price=req.original_price,
            coin_price=req.coin_price,
            coin_amount=req.coin_amount,
            content_id=req.content_id,
            subscription_duration=req.subscription_duration,
            subscription_type=req.subscription_type,
            stock=req.stock,
            cover_url=req.cover_url,
            images=req.images,
            seller_id=req.seller_id,
            seller_name=req.seller_name,
        )
        self.db.add(goods)
        await self.db.commit()
        await self.db.refresh(goods)
        return GoodsInfo.model_validate(goods)

    async def _validate_goods_type_fields(self, req: GoodsCreate):
        if req.goods_type == "coin":
            if req.coin_amount is None or req.coin_amount <= 0:
                raise BusinessException("金币类商品必须设置金币数量")
            if req.content_id is not None:
                raise BusinessException("金币类商品不能关联内容")
        elif req.goods_type == "content":
            if req.content_id is None:
                raise BusinessException("内容类商品必须关联内容ID")
            if req.coin_amount is not None:
                raise BusinessException("内容类商品不能设置金币数量")
        elif req.goods_type == "subscription":
            if req.subscription_duration is None or req.subscription_duration <= 0:
                raise BusinessException("订阅类商品必须设置订阅时长")
            if req.subscription_type is None:
                raise BusinessException("订阅类商品必须设置订阅类型")
        elif req.goods_type == "goods":
            pass
        else:
            raise BusinessException("不支持的商品类型")

