"""
点赞模块异步服务层（门面）
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.like.schemas import LikeToggleRequest, LikeInfo, LikeQuery, LikeUserInfo
from app.domains.like.services.toggle_service import LikeToggleService
from app.domains.like.services.query_service import LikeQueryService


class LikeAsyncService:
    """点赞异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.toggle_service = LikeToggleService(db)
        self.query_service = LikeQueryService(db)

    async def toggle_like(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: LikeToggleRequest) -> Tuple[bool, LikeInfo]:
        return await self.toggle_service.toggle_like(user_id, user_nickname, user_avatar, req)

    async def get_my_likes(self, user_id: int, query: LikeQuery, pagination: PaginationParams) -> PaginationResult[LikeInfo]:
        return await self.query_service.get_my_likes(user_id, query, pagination)

    async def get_likers_by_target(self, like_type: str, target_id: int, pagination: PaginationParams) -> PaginationResult[LikeUserInfo]:
        return await self.query_service.get_likers_by_target(like_type, target_id, pagination)

    async def update_like_count(self, like_type: str, target_id: int, increment: bool = True) -> bool:
        # 可后续下沉到专门的计数服务
        from sqlalchemy import update
        from app.domains.content.models import Content
        from app.domains.comment.models import Comment
        from app.domains.social.models import SocialDynamic
        target_model = Content if like_type == "CONTENT" else Comment if like_type == "COMMENT" else SocialDynamic if like_type == "DYNAMIC" else None
        if target_model is None:
            from app.common.exceptions import BusinessException
            raise BusinessException("不支持的点赞类型")
        if increment:
            await self.db.execute(update(target_model).where(target_model.id == target_id).values(like_count=target_model.like_count + 1))
        else:
            await self.db.execute(update(target_model).where(target_model.id == target_id).values(like_count=target_model.like_count - 1))
        await self.db.commit()
        return True

