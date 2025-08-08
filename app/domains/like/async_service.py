"""
点赞模块异步服务层 - 增强版
添加幂等性和原子性支持
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_

from app.domains.like.models import Like
from app.domains.like.schemas import LikeToggleRequest, LikeInfo
from app.common.exceptions import BusinessException
from app.common.cache_service import cache_service
from app.common.atomic import atomic_transaction, atomic_lock
# Import other models for counter updates
from app.domains.content.models import Content
from app.domains.comment.models import Comment
from app.domains.social.models import SocialDynamic


class LikeAsyncService:
    """点赞异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @atomic_transaction()
    async def toggle_like(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: LikeToggleRequest) -> Tuple[bool, LikeInfo]:
        """点赞/取消点赞切换 - 带原子性事务和幂等性"""
        # 检查幂等性
        cached_result = await cache_service.check_idempotent(user_id, "toggle_like", req.like_type, req.target_id)
        if cached_result is not None:
            return cached_result.get("is_liked", False), LikeInfo.model_validate(cached_result.get("like_info"))

        like = (await self.db.execute(
            select(Like).where(and_(Like.user_id == user_id, Like.like_type == req.like_type, Like.target_id == req.target_id))
        )).scalar_one_or_none()

        is_liked = False
        if like is None:
            # Create new like
            await self.db.execute(insert(Like).values(
                user_id=user_id,
                like_type=req.like_type,
                target_id=req.target_id,
                user_nickname=user_nickname,
                user_avatar=user_avatar,
                status="active",
            ))
            is_liked = True
        else:
            # Toggle status
            new_status = "cancelled" if like.status == "active" else "active"
            await self.db.execute(update(Like).where(Like.id == like.id).values(status=new_status))
            is_liked = (new_status == "active")
        
        await self.db.commit()
        
        # Update target's like count
        if req.like_type == "CONTENT":
            target_model = Content
        elif req.like_type == "COMMENT":
            target_model = Comment
        elif req.like_type == "DYNAMIC":
            target_model = SocialDynamic
        else:
            raise BusinessException("不支持的点赞类型")

        # Increment/decrement like_count
        if is_liked:
            await self.db.execute(update(target_model).where(target_model.id == req.target_id).values(like_count=target_model.like_count + 1))
        else:
            await self.db.execute(update(target_model).where(target_model.id == req.target_id).values(like_count=target_model.like_count - 1))
        await self.db.commit()

        # Re-fetch the like record after all updates
        like = (await self.db.execute(
            select(Like).where(and_(Like.user_id == user_id, Like.like_type == req.like_type, Like.target_id == req.target_id))
        )).scalar_one()
        
        like_info = LikeInfo.model_validate(like)

        # 清除相关缓存
        await cache_service.delete_pattern(f"like:*")
        await cache_service.delete_pattern(f"content:*")
        await cache_service.delete_pattern(f"comment:*")
        await cache_service.delete_pattern(f"social:*")

        # 缓存幂等性结果
        result = {
            "is_liked": is_liked,
            "like_info": like_info.model_dump()
        }
        await cache_service.set_idempotent_result(user_id, "toggle_like", result, req.like_type, req.target_id)

        return is_liked, like_info

    @atomic_lock(lambda *args, **kwargs: f"like:count:{kwargs.get('like_type')}:{kwargs.get('target_id')}")
    async def update_like_count(self, like_type: str, target_id: int, increment: bool = True) -> bool:
        """更新点赞计数 - 带分布式锁"""
        try:
            # 根据类型选择目标模型
            if like_type == "CONTENT":
                target_model = Content
            elif like_type == "COMMENT":
                target_model = Comment
            elif like_type == "DYNAMIC":
                target_model = SocialDynamic
            else:
                raise BusinessException("不支持的点赞类型")

            # 更新计数
            if increment:
                await self.db.execute(update(target_model).where(target_model.id == target_id).values(like_count=target_model.like_count + 1))
            else:
                await self.db.execute(update(target_model).where(target_model.id == target_id).values(like_count=target_model.like_count - 1))
            
            await self.db.commit()

            # 清除相关缓存
            await cache_service.delete_pattern(f"content:*")
            await cache_service.delete_pattern(f"comment:*")
            await cache_service.delete_pattern(f"social:*")

            return True
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新点赞计数失败: {str(e)}")

