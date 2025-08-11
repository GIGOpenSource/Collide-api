from typing import Optional, Tuple

from sqlalchemy import select, insert, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.cache_service import cache_service
from app.domains.follow.models import Follow
from app.domains.follow.schemas import FollowToggleRequest, FollowInfo
from app.domains.interaction.services.record_service import InteractionRecordService


class FollowToggleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.interaction_service = InteractionRecordService(db)

    async def toggle_follow(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: FollowToggleRequest) -> Tuple[bool, FollowInfo]:
        cached_result = await cache_service.check_idempotent(user_id, "toggle_follow", req.followee_id)
        if cached_result is not None:
            return cached_result.get("is_following", False), FollowInfo.model_validate(cached_result.get("follow_info"))
        if user_id == req.followee_id:
            raise BusinessException("不能关注自己")
        follow = (await self.db.execute(select(Follow).where(and_(Follow.follower_id == user_id, Follow.followee_id == req.followee_id)))).scalar_one_or_none()
        if follow is None:
            await self.db.execute(insert(Follow).values(follower_id=user_id, followee_id=req.followee_id, follower_nickname=user_nickname, follower_avatar=user_avatar, status="active"))
            await self.db.commit()
            follow = (await self.db.execute(select(Follow).where(and_(Follow.follower_id == user_id, Follow.followee_id == req.followee_id)))).scalar_one()
            is_following = True
            # 记录到互动表
            await self.interaction_service.record_interaction(
                interaction_type="FOLLOW",
                target_id=req.followee_id,
                user_id=user_id,
                user_nickname=user_nickname or "未知用户",
                user_avatar=user_avatar
            )
        else:
            new_status = "cancelled" if follow.status == "active" else "active"
            await self.db.execute(update(Follow).where(Follow.id == follow.id).values(status=new_status))
            await self.db.commit()
            is_following = (new_status == "active")
            # 更新互动表状态
            if new_status == "cancelled":
                await self.interaction_service.cancel_interaction("FOLLOW", req.followee_id, user_id)
            else:
                await self.interaction_service.record_interaction(
                    interaction_type="FOLLOW",
                    target_id=req.followee_id,
                    user_id=user_id,
                    user_nickname=user_nickname or "未知用户",
                    user_avatar=user_avatar
                )
        follow = (await self.db.execute(select(Follow).where(Follow.id == follow.id))).scalar_one()
        info = FollowInfo.model_validate(follow)
        await cache_service.delete_pattern("follow:*")
        await cache_service.delete_pattern("user:stats:*")
        result = {"is_following": is_following, "follow_info": info.model_dump()}
        await cache_service.set_idempotent_result(user_id, "toggle_follow", result, req.followee_id)
        return is_following, info

