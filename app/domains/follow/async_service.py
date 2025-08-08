"""
关注模块异步服务层
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, or_

from app.domains.follow.models import Follow
from app.domains.follow.schemas import FollowToggleRequest, FollowInfo, FollowQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class FollowAsyncService:
    """关注异步服务类（支持幂等切换）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle_follow(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: FollowToggleRequest) -> Tuple[bool, FollowInfo]:
        """关注/取消关注切换

        返回 (is_following, follow_info)
        is_following=True 表示当前操作后为关注状态
        """
        if user_id == req.followee_id:
            raise BusinessException("不能关注自己")

        follow = (await self.db.execute(
            select(Follow).where(and_(Follow.follower_id == user_id, Follow.followee_id == req.followee_id))
        )).scalar_one_or_none()

        if follow is None:
            # 首次关注
            await self.db.execute(insert(Follow).values(
                follower_id=user_id,
                followee_id=req.followee_id,
                follower_nickname=user_nickname,
                follower_avatar=user_avatar,
                status="active",
            ))
            await self.db.commit()
            follow = (await self.db.execute(
                select(Follow).where(and_(Follow.follower_id == user_id, Follow.followee_id == req.followee_id))
            )).scalar_one()
            return True, FollowInfo.model_validate(follow)

        # 已存在记录，按状态切换
        new_status = "cancelled" if follow.status == "active" else "active"
        await self.db.execute(update(Follow).where(Follow.id == follow.id).values(status=new_status))
        await self.db.commit()

        # 刷新
        follow = (await self.db.execute(select(Follow).where(Follow.id == follow.id))).scalar_one()
        return new_status == "active", FollowInfo.model_validate(follow)

    async def get_follow_list(self, query: FollowQuery, pagination: PaginationParams) -> PaginationResult[FollowInfo]:
        """获取关注列表"""
        conditions = []

        if query.user_id:
            if query.follow_type == "following":
                # 我关注的
                conditions.append(Follow.follower_id == query.user_id)
            elif query.follow_type == "followers":
                # 关注我的
                conditions.append(Follow.followee_id == query.user_id)
            else:
                # 默认查询我关注的
                conditions.append(Follow.follower_id == query.user_id)

        if query.status:
            conditions.append(Follow.status == query.status)
        else:
            # 默认只查询活跃状态
            conditions.append(Follow.status == "active")

        stmt = select(Follow).where(and_(*conditions)).order_by(Follow.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        follows = result.scalars().all()

        follow_list = [FollowInfo.model_validate(follow) for follow in follows]

        return PaginationResult.create(
            items=follow_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def check_follow_status(self, follower_id: int, followee_id: int) -> bool:
        """检查关注状态"""
        follow = (await self.db.execute(
            select(Follow).where(and_(
                Follow.follower_id == follower_id,
                Follow.followee_id == followee_id,
                Follow.status == "active"
            ))
        )).scalar_one_or_none()
        return follow is not None 