from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.domains.follow.models import Follow
from app.domains.follow.schemas import FollowStatus


class FollowStatusService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_follow_status(self, current_user_id: int, target_user_id: int) -> FollowStatus:
        # 1. Check if current_user follows target_user
        following_stmt = select(Follow).where(and_(
            Follow.follower_id == current_user_id,
            Follow.followee_id == target_user_id,
            Follow.status == "active"
        ))
        following = (await self.db.execute(following_stmt)).scalar_one_or_none() is not None

        # 2. Check if target_user follows current_user
        followed_by_stmt = select(Follow).where(and_(
            Follow.follower_id == target_user_id,
            Follow.followee_id == current_user_id,
            Follow.status == "active"
        ))
        followed_by = (await self.db.execute(followed_by_stmt)).scalar_one_or_none() is not None

        return FollowStatus(
            following=following,
            followed_by=followed_by,
            mutual=following and followed_by
        )

    async def check_follow_status(self, follower_id: int, followee_id: int) -> bool:
        cache_key = f"follow:status:{follower_id}:{followee_id}"
        cached = await cache_service.get(cache_key)
        if cached is not None:
            return cached
        follow = (await self.db.execute(select(Follow).where(and_(Follow.follower_id == follower_id, Follow.followee_id == followee_id, Follow.status == "active")))).scalar_one_or_none()
        is_following = follow is not None
        await cache_service.set(cache_key, is_following, ttl=1800)
        return is_following

