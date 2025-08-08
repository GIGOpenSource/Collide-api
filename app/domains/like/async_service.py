"""
点赞模块异步服务层
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_

from app.domains.like.models import Like
from app.domains.like.schemas import LikeToggleRequest, LikeInfo
from app.common.exceptions import BusinessException
from app.domains.content.models import Content
from app.domains.comment.models import Comment
from app.domains.social.models import SocialDynamic


class LikeAsyncService:
    """点赞异步服务类（支持幂等切换）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle_like(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: LikeToggleRequest) -> Tuple[bool, LikeInfo]:
        """点赞/取消点赞切换

        返回 (is_liked, like_info)
        is_liked=True 表示当前操作后为点赞状态
        """
        like = (await self.db.execute(
            select(Like).where(and_(Like.user_id == user_id, Like.like_type == req.like_type, Like.target_id == req.target_id))
        )).scalar_one_or_none()

        # 目标计数字段定位
        target_model, counter_field = self._resolve_target(req.like_type)
        if not target_model:
            raise BusinessException("不支持的点赞类型")

        if like is None:
            # 首次点赞
            await self.db.execute(insert(Like).values(
                like_type=req.like_type,
                target_id=req.target_id,
                user_id=user_id,
                user_nickname=user_nickname,
                user_avatar=user_avatar,
                status="active",
            ))
            # 计数 +1
            await self.db.execute(update(target_model).where(target_model.id == req.target_id).values({counter_field: counter_field + 1}))
            await self.db.commit()
            like = (await self.db.execute(
                select(Like).where(and_(Like.user_id == user_id, Like.like_type == req.like_type, Like.target_id == req.target_id))
            )).scalar_one()
            return True, LikeInfo.model_validate(like)

        # 已存在记录，按状态切换
        new_status = "cancelled" if like.status == "active" else "active"
        delta = -1 if new_status == "cancelled" else +1
        await self.db.execute(update(Like).where(Like.id == like.id).values(status=new_status))
        await self.db.execute(update(target_model).where(target_model.id == req.target_id).values({counter_field: counter_field + delta}))
        await self.db.commit()

        # 刷新
        like = (await self.db.execute(select(Like).where(Like.id == like.id))).scalar_one()
        return new_status == "active", LikeInfo.model_validate(like)

    def _resolve_target(self, like_type: str):
        """解析点赞目标模型与计数字段"""
        if like_type == "CONTENT":
            return Content, Content.like_count
        if like_type == "COMMENT":
            return Comment, Comment.like_count
        if like_type == "DYNAMIC":
            return SocialDynamic, SocialDynamic.like_count
        return None, None

