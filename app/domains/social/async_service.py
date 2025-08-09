"""
社交动态模块异步服务层（门面）
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social.schemas import DynamicCreate, DynamicUpdate, DynamicInfo, DynamicQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.social.services.create_service import SocialCreateService
from app.domains.social.services.update_service import SocialUpdateService
from app.domains.social.services.query_service import SocialQueryService


class SocialAsyncService:
    """社交动态异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dynamic(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], data: DynamicCreate) -> DynamicInfo:
        return await SocialCreateService(self.db).create_dynamic(user_id, user_nickname, user_avatar, data)

    async def update_dynamic(self, dynamic_id: int, user_id: int, data: DynamicUpdate) -> DynamicInfo:
        return await SocialUpdateService(self.db).update_dynamic(dynamic_id, user_id, data)

    async def delete_dynamic(self, dynamic_id: int, user_id: int) -> bool:
        return await SocialUpdateService(self.db).delete_dynamic(dynamic_id, user_id)

    async def get_dynamic_by_id(self, dynamic_id: int) -> DynamicInfo:
        return await SocialQueryService(self.db).get_dynamic_by_id(dynamic_id)

    async def list_dynamics(self, query: DynamicQuery, pagination: PaginationParams) -> PaginationResult[DynamicInfo]:
        return await SocialQueryService(self.db).list_dynamics(query, pagination)

