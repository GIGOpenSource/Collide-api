"""
商品模块异步服务层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.goods.models import Goods
from app.domains.goods.schemas import GoodsCreate, GoodsUpdate, GoodsInfo, GoodsQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class GoodsAsyncService:
    """商品异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_goods(self, req: GoodsCreate) -> GoodsInfo:
        """创建商品"""
        # 验证商品类型和字段的匹配
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
            seller_name=req.seller_name
        )
        self.db.add(goods)
        await self.db.commit()
        await self.db.refresh(goods)
        return GoodsInfo.model_validate(goods)

    async def _validate_goods_type_fields(self, req: GoodsCreate):
        """验证商品类型和字段的匹配"""
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
            # 普通商品，无特殊要求
            pass
        else:
            raise BusinessException("不支持的商品类型")

    async def update_goods(self, goods_id: int, req: GoodsUpdate) -> GoodsInfo:
        """更新商品"""
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")

        # 更新字段
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

        # 刷新数据
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one()
        return GoodsInfo.model_validate(goods)

    async def delete_goods(self, goods_id: int):
        """删除商品"""
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")

        await self.db.execute(delete(Goods).where(Goods.id == goods_id))
        await self.db.commit()

    async def get_goods_by_id(self, goods_id: int) -> GoodsInfo:
        """根据ID获取商品"""
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")
        return GoodsInfo.model_validate(goods)

    async def get_goods_list(self, query: GoodsQuery, pagination: PaginationParams) -> PaginationResult[GoodsInfo]:
        """获取商品列表"""
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
                Goods.seller_name.contains(query.keyword)
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

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        goods_list = result.scalars().all()

        goods_info_list = [GoodsInfo.model_validate(goods) for goods in goods_list]

        return PaginationResult.create(
            items=goods_info_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def increase_view_count(self, goods_id: int):
        """增加商品查看数"""
        await self.db.execute(
            update(Goods).where(Goods.id == goods_id).values(view_count=Goods.view_count + 1)
        )
        await self.db.commit()

    async def increase_sales_count(self, goods_id: int, quantity: int = 1):
        """增加商品销量"""
        await self.db.execute(
            update(Goods).where(Goods.id == goods_id).values(sales_count=Goods.sales_count + quantity)
        )
        await self.db.commit()

    async def update_stock(self, goods_id: int, quantity: int):
        """更新商品库存"""
        goods = (await self.db.execute(select(Goods).where(Goods.id == goods_id))).scalar_one_or_none()
        if not goods:
            raise BusinessException("商品不存在")

        if goods.stock != -1:  # 无限库存不更新
            new_stock = goods.stock - quantity
            if new_stock < 0:
                raise BusinessException("库存不足")

            await self.db.execute(
                update(Goods).where(Goods.id == goods_id).values(stock=new_stock)
            )
            await self.db.commit()

    async def get_goods_by_category(self, category_id: int, limit: int = 20) -> List[GoodsInfo]:
        """根据分类获取商品"""
        stmt = select(Goods).where(
            and_(Goods.category_id == category_id, Goods.status == "active")
        ).order_by(Goods.create_time.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        goods_list = result.scalars().all()

        return [GoodsInfo.model_validate(goods) for goods in goods_list]

    async def get_hot_goods(self, goods_type: Optional[str] = None, limit: int = 10) -> List[GoodsInfo]:
        """获取热门商品"""
        conditions = [Goods.status == "active"]
        if goods_type:
            conditions.append(Goods.goods_type == goods_type)

        stmt = select(Goods).where(and_(*conditions)).order_by(Goods.sales_count.desc(), Goods.view_count.desc()).limit(limit)
        result = await self.db.execute(stmt)
        goods_list = result.scalars().all()

        return [GoodsInfo.model_validate(goods) for goods in goods_list] 