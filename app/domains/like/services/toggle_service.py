from typing import Optional, Tuple

from sqlalchemy import select, insert, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.cache_service import cache_service
from app.domains.like.models import Like
from app.domains.like.schemas import LikeToggleRequest, LikeInfo
from app.domains.content.models import Content
from app.domains.comment.models import Comment
from app.domains.social.models import SocialDynamic


class LikeToggleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle_like(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: LikeToggleRequest) -> Tuple[bool, LikeInfo]:
        cached = await cache_service.check_idempotent(user_id, "toggle_like", req.like_type, req.target_id)
        if cached is not None:
            return cached.get("is_liked", False), LikeInfo.model_validate(cached.get("like_info"))
        like = (await self.db.execute(select(Like).where(and_(Like.user_id == user_id, Like.like_type == req.like_type, Like.target_id == req.target_id)))).scalar_one_or_none()
        is_liked = False
        if like is None:
            await self.db.execute(insert(Like).values(user_id=user_id, like_type=req.like_type, target_id=req.target_id, user_nickname=user_nickname, user_avatar=user_avatar, status="active"))
            is_liked = True
        else:
            new_status = "cancelled" if like.status == "active" else "active"
            await self.db.execute(update(Like).where(Like.id == like.id).values(status=new_status))
            is_liked = (new_status == "active")
        await self.db.commit()
        target_model = Content if req.like_type == "CONTENT" else Comment if req.like_type == "COMMENT" else SocialDynamic if req.like_type == "DYNAMIC" else None
        if target_model is None:
            raise BusinessException("不支持的点赞类型")
        if is_liked:
            await self.db.execute(update(target_model).where(target_model.id == req.target_id).values(like_count=target_model.like_count + 1))
        else:
            await self.db.execute(update(target_model).where(target_model.id == req.target_id).values(like_count=target_model.like_count - 1))
        await self.db.commit()
        like = (await self.db.execute(select(Like).where(and_(Like.user_id == user_id, Like.like_type == req.like_type, Like.target_id == req.target_id)))).scalar_one()
        info = LikeInfo.model_validate(like)
        await cache_service.delete_pattern("like:*")
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("comment:*")
        await cache_service.delete_pattern("social:*")
        result = {"is_liked": is_liked, "like_info": info.model_dump()}
        await cache_service.set_idempotent_result(user_id, "toggle_like", result, req.like_type, req.target_id)
        return is_liked, info

