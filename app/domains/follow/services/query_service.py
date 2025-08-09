from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.follow.models import Follow
from app.domains.follow.schemas import FollowInfo, FollowQuery, FollowStats


class FollowQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_follow_list(self, user_id: int, query: FollowQuery, pagination: PaginationParams) -> PaginationResult[FollowInfo]:
        cache_key = f"follow:list:{user_id}:{hash(str(query.model_dump()) + str(pagination.model_dump()))}"
        cached = await cache_service.get(cache_key)
        if cached:
            return PaginationResult.model_validate(cached)
        conditions = [Follow.follower_id == user_id]
        if query.status:
            conditions.append(Follow.status == query.status)
        stmt = select(Follow).where(and_(*conditions)).order_by(Follow.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [FollowInfo.model_validate(x) for x in rows.scalars().all()]
        result = PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        await cache_service.set(cache_key, result.model_dump(), ttl=300)
        return result

    async def get_follow_stats(self, user_id: int) -> FollowStats:
        """获取用户的关注数和粉丝数"""
        # 1. Get following count
        following_stmt = select(func.count(Follow.id)).where(and_(
            Follow.follower_id == user_id,
            Follow.status == "active"
        ))
        following_count = (await self.db.execute(following_stmt)).scalar() or 0

        # 2. Get follower count
        follower_stmt = select(func.count(Follow.id)).where(and_(
            Follow.followee_id == user_id,
            Follow.status == "active"
        ))
        follower_count = (await self.db.execute(follower_stmt)).scalar() or 0

        return FollowStats(
            following_count=following_count,
            follower_count=follower_count
        )

