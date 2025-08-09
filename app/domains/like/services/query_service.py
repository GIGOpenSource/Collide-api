from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.like.models import Like
from app.domains.like.schemas import LikeQuery, LikeInfo, LikeUserInfo


class LikeQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_my_likes(self, user_id: int, query: LikeQuery, pagination: PaginationParams) -> PaginationResult[LikeInfo]:
        """获取我的点赞列表 (只返回active状态)"""
        conditions = [
            Like.user_id == user_id,
            Like.status == "active"
        ]
        if query.like_type:
            conditions.append(Like.like_type == query.like_type)
        
        stmt = select(Like).where(and_(*conditions)).order_by(Like.create_time.desc())
        
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar() or 0
        
        result_stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(result_stmt)).scalars().all()
        
        items = [LikeInfo.model_validate(r) for r in rows]
        
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_likers_by_target(self, like_type: str, target_id: int, pagination: PaginationParams) -> PaginationResult[LikeUserInfo]:
        """获取点赞了某个对象的用户列表 (只返回active状态)"""
        conditions = [
            Like.like_type == like_type,
            Like.target_id == target_id,
            Like.status == "active"
        ]
        
        stmt = select(Like).where(and_(*conditions)).order_by(Like.create_time.desc())
        
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar() or 0
        
        result_stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(result_stmt)).scalars().all()
        
        # 构造返回用户信息列表
        items = [LikeUserInfo(
            user_id=r.user_id,
            user_nickname=r.user_nickname,
            user_avatar=r.user_avatar,
            like_time=r.create_time
        ) for r in rows]
        
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)