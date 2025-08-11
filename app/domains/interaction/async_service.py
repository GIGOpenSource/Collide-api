"""
互动模块异步服务
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.interaction.schemas import InteractionQuery, InteractionInfo, InteractionUserInfo
from app.domains.interaction.services.query_service import InteractionQueryService


class InteractionAsyncService:
    """互动异步服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.query_service = InteractionQueryService(db)

    async def get_interactions(
        self, 
        query: InteractionQuery, 
        pagination: PaginationParams
    ) -> PaginationResult[InteractionInfo]:
        """获取互动列表"""
        return await self.query_service.get_interactions(query, pagination)

    async def get_interactions_by_target(
        self, 
        interaction_type: str, 
        target_id: int, 
        pagination: PaginationParams
    ) -> PaginationResult[InteractionUserInfo]:
        """获取指定目标的互动用户列表"""
        return await self.query_service.get_interactions_by_target(interaction_type, target_id, pagination)

    async def get_user_interactions(
        self, 
        user_id: int, 
        interaction_type: Optional[str] = None,
        pagination: PaginationParams = None
    ) -> PaginationResult[InteractionInfo]:
        """获取用户的互动记录"""
        return await self.query_service.get_user_interactions(user_id, interaction_type, pagination) 