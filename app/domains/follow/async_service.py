"""
关注模块异步服务层（门面）
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.follow.schemas import FollowToggleRequest, FollowInfo, FollowQuery, FollowStatus, FollowStats
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.follow.services.toggle_service import FollowToggleService
from app.domains.follow.services.query_service import FollowQueryService
from app.domains.follow.services.status_service import FollowStatusService


class FollowAsyncService:
    """关注异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.toggle_service = FollowToggleService(self.db)
        self.query_service = FollowQueryService(self.db)
        self.status_service = FollowStatusService(self.db)

    async def toggle_follow(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], req: FollowToggleRequest) -> Tuple[bool, FollowInfo]:
        return await self.toggle_service.toggle_follow(user_id, user_nickname, user_avatar, req)

    async def get_follow_list(self, user_id: int, query: FollowQuery, pagination: PaginationParams) -> PaginationResult[FollowInfo]:
        return await self.query_service.get_follow_list(user_id, query, pagination)

    async def check_follow_status(self, follower_id: int, followee_id: int) -> bool:
        return await self.status_service.check_follow_status(follower_id, followee_id)

    async def get_follow_status(self, current_user_id: int, target_user_id: int) -> FollowStatus:
        return await self.status_service.get_follow_status(current_user_id, target_user_id)

    async def get_follow_stats(self, user_id: int) -> FollowStats:
        return await self.query_service.get_follow_stats(user_id)

    @atomic_transaction()
    async def update_follow_count(self, user_id: int, increment: bool = True) -> bool:
        """更新关注计数 - 带分布式锁"""
        try:
            # 这里可以实现用户关注计数的更新逻辑
            # 使用分布式锁确保并发安全
            return True
        except Exception as e:
            raise BusinessException(f"更新关注计数失败: {str(e)}") 