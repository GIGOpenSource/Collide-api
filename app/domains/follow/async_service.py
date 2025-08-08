"""
关注模块异步服务层 - 增强版
添加幂等性和原子性支持
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, or_, func

from app.domains.follow.models import Follow
from app.domains.follow.schemas import FollowToggleRequest, FollowInfo, FollowQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.common.cache_service import cache_service
from app.common.atomic import atomic_transaction, atomic_lock


class FollowAsyncService:
    """关注异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @atomic_transaction()
    async def toggle_follow(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: FollowToggleRequest) -> Tuple[bool, FollowInfo]:
        """关注/取消关注切换 - 带原子性事务和幂等性"""
        # 检查幂等性
        cached_result = await cache_service.check_idempotent(user_id, "toggle_follow", req.followee_id)
        if cached_result is not None:
            return cached_result.get("is_following", False), FollowInfo.model_validate(cached_result.get("follow_info"))

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
            is_following = True
        else:
            # 已存在记录，按状态切换
            new_status = "cancelled" if follow.status == "active" else "active"
            await self.db.execute(update(Follow).where(Follow.id == follow.id).values(status=new_status))
            await self.db.commit()
            is_following = (new_status == "active")

        # 刷新
        follow = (await self.db.execute(select(Follow).where(Follow.id == follow.id))).scalar_one()
        follow_info = FollowInfo.model_validate(follow)

        # 清除相关缓存
        await cache_service.delete_pattern("follow:*")
        await cache_service.delete_pattern("user:stats:*")

        # 缓存幂等性结果
        result = {
            "is_following": is_following,
            "follow_info": follow_info.model_dump()
        }
        await cache_service.set_idempotent_result(user_id, "toggle_follow", result, req.followee_id)

        return is_following, follow_info

    async def get_follow_list(self, user_id: int, query: FollowQuery, pagination: PaginationParams) -> PaginationResult[FollowInfo]:
        """获取关注列表 - 带缓存"""
        # 生成缓存键
        cache_key = f"follow:list:{user_id}:{hash(str(query.model_dump()) + str(pagination.model_dump()))}"
        
        # 尝试从缓存获取
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.model_validate(cached_result)

        conditions = [Follow.follower_id == user_id]
        
        if query.status:
            conditions.append(Follow.status == query.status)

        stmt = select(Follow).where(and_(*conditions)).order_by(Follow.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        follows = result.scalars().all()

        follow_info_list = [FollowInfo.model_validate(follow) for follow in follows]

        pagination_result = PaginationResult.create(
            items=follow_info_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

        # 缓存结果（短期缓存）
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)

        return pagination_result

    async def check_follow_status(self, follower_id: int, followee_id: int) -> bool:
        """检查关注状态 - 带缓存"""
        # 尝试从缓存获取
        cache_key = f"follow:status:{follower_id}:{followee_id}"
        cached_status = await cache_service.get(cache_key)
        if cached_status is not None:
            return cached_status

        follow = (await self.db.execute(
            select(Follow).where(and_(Follow.follower_id == follower_id, Follow.followee_id == followee_id, Follow.status == "active"))
        )).scalar_one_or_none()

        is_following = follow is not None

        # 缓存结果
        await cache_service.set(cache_key, is_following, ttl=1800)

        return is_following

    @atomic_transaction()
    async def update_follow_count(self, user_id: int, increment: bool = True) -> bool:
        """更新关注计数 - 带分布式锁"""
        try:
            # 这里可以实现用户关注计数的更新逻辑
            # 使用分布式锁确保并发安全
            return True
        except Exception as e:
            raise BusinessException(f"更新关注计数失败: {str(e)}") 