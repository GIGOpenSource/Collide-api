from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.favorite.models import Favorite
from app.domains.favorite.schemas import FavoriteInfo, FavoriteQuery


class FavoriteQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_favorite_list(self, user_id: int, query: FavoriteQuery, pagination: PaginationParams) -> PaginationResult[FavoriteInfo]:
        cache_key = f"favorite:list:{user_id}:{hash(str(query.model_dump()) + str(pagination.model_dump()))}"
        cached = await cache_service.get(cache_key)
        if cached:
            return PaginationResult.model_validate(cached)
        conditions = [Favorite.user_id == user_id]
        if query.favorite_type:
            conditions.append(Favorite.favorite_type == query.favorite_type)
        if query.status:
            conditions.append(Favorite.status == query.status)
        stmt = select(Favorite).where(and_(*conditions)).order_by(Favorite.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [FavoriteInfo.model_validate(x) for x in rows.scalars().all()]
        result = PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        await cache_service.set(cache_key, result.model_dump(), ttl=300)
        return result

