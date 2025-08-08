"""
收藏模块异步服务层 - 增强版
添加幂等性和原子性支持
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, or_, func

from app.domains.favorite.models import Favorite
from app.domains.favorite.schemas import FavoriteToggleRequest, FavoriteInfo, FavoriteQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.common.cache_service import cache_service
from app.common.atomic import atomic_transaction, atomic_lock


class FavoriteAsyncService:
    """收藏异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @atomic_transaction()
    async def toggle_favorite(self, user_id: int, user_nickname: Optional[str], req: FavoriteToggleRequest) -> Tuple[bool, FavoriteInfo]:
        """收藏/取消收藏切换 - 带原子性事务和幂等性"""
        # 检查幂等性
        cached_result = await cache_service.check_idempotent(user_id, "toggle_favorite", req.favorite_type, req.target_id)
        if cached_result is not None:
            return cached_result.get("is_favorited", False), FavoriteInfo.model_validate(cached_result.get("favorite_info"))

        favorite = (await self.db.execute(
            select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == req.favorite_type, Favorite.target_id == req.target_id))
        )).scalar_one_or_none()

        if favorite is None:
            # 首次收藏
            await self.db.execute(insert(Favorite).values(
                favorite_type=req.favorite_type,
                target_id=req.target_id,
                user_id=user_id,
                user_nickname=user_nickname,
                status="active",
            ))
            await self.db.commit()
            favorite = (await self.db.execute(
                select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == req.favorite_type, Favorite.target_id == req.target_id))
            )).scalar_one()
            is_favorited = True
        else:
            # 已存在记录，按状态切换
            new_status = "cancelled" if favorite.status == "active" else "active"
            await self.db.execute(update(Favorite).where(Favorite.id == favorite.id).values(status=new_status))
            await self.db.commit()
            is_favorited = (new_status == "active")

        # 刷新
        favorite = (await self.db.execute(select(Favorite).where(Favorite.id == favorite.id))).scalar_one()
        favorite_info = FavoriteInfo.model_validate(favorite)

        # 清除相关缓存
        await cache_service.delete_pattern("favorite:*")
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("goods:*")

        # 缓存幂等性结果
        result = {
            "is_favorited": is_favorited,
            "favorite_info": favorite_info.model_dump()
        }
        await cache_service.set_idempotent_result(user_id, "toggle_favorite", result, req.favorite_type, req.target_id)

        return is_favorited, favorite_info

    async def get_favorite_list(self, user_id: int, query: FavoriteQuery, pagination: PaginationParams) -> PaginationResult[FavoriteInfo]:
        """获取收藏列表 - 带缓存"""
        # 生成缓存键
        cache_key = f"favorite:list:{user_id}:{hash(str(query.model_dump()) + str(pagination.model_dump()))}"
        
        # 尝试从缓存获取
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.create(**cached_result)

        conditions = [Favorite.user_id == user_id]
        
        if query.favorite_type:
            conditions.append(Favorite.favorite_type == query.favorite_type)
        if query.status:
            conditions.append(Favorite.status == query.status)

        stmt = select(Favorite).where(and_(*conditions)).order_by(Favorite.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        favorites = result.scalars().all()

        favorite_info_list = [FavoriteInfo.model_validate(favorite) for favorite in favorites]

        pagination_result = PaginationResult.create(
            items=favorite_info_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

        # 缓存结果（短期缓存）
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)

        return pagination_result

    async def check_favorite_status(self, user_id: int, favorite_type: str, target_id: int) -> bool:
        """检查收藏状态 - 带缓存"""
        # 尝试从缓存获取
        cache_key = f"favorite:status:{user_id}:{favorite_type}:{target_id}"
        cached_status = await cache_service.get(cache_key)
        if cached_status is not None:
            return cached_status

        favorite = (await self.db.execute(
            select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == favorite_type, Favorite.target_id == target_id, Favorite.status == "active"))
        )).scalar_one_or_none()

        is_favorited = favorite is not None

        # 缓存结果
        await cache_service.set(cache_key, is_favorited, ttl=1800)

        return is_favorited

    @atomic_lock(lambda *args, **kwargs: f"favorite:count:{kwargs.get('favorite_type')}:{kwargs.get('target_id')}")
    async def update_favorite_count(self, favorite_type: str, target_id: int, increment: bool = True) -> bool:
        """更新收藏计数 - 带分布式锁"""
        try:
            # 根据类型选择目标模型并更新计数
            # 这里可以实现具体的计数更新逻辑
            return True
        except Exception as e:
            raise BusinessException(f"更新收藏计数失败: {str(e)}") 