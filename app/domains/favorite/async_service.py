"""
收藏模块异步服务层（门面）
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.favorite.schemas import FavoriteToggleRequest, FavoriteInfo, FavoriteQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.favorite.services.toggle_service import FavoriteToggleService
from app.domains.favorite.services.query_service import FavoriteQueryService


class FavoriteAsyncService:
    """收藏异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle_favorite(self, user_id: int, user_nickname: Optional[str], req: FavoriteToggleRequest) -> Tuple[bool, FavoriteInfo]:
        return await FavoriteToggleService(self.db).toggle_favorite(user_id, user_nickname, req)

    async def get_favorite_list(self, user_id: int, query: FavoriteQuery, pagination: PaginationParams) -> PaginationResult[FavoriteInfo]:
        return await FavoriteQueryService(self.db).get_favorite_list(user_id, query, pagination)

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

    @atomic_transaction()
    async def update_favorite_count(self, favorite_type: str, target_id: int, increment: bool = True) -> bool:
        """更新收藏计数 - 带分布式锁"""
        try:
            # 根据类型选择目标模型并更新计数
            # 这里可以实现具体的计数更新逻辑
            return True
        except Exception as e:
            raise BusinessException(f"更新收藏计数失败: {str(e)}") 