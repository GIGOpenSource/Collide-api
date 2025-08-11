"""
互动查询服务
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.interaction.models import Interaction
from app.domains.interaction.schemas import InteractionQuery, InteractionInfo, InteractionUserInfo


class InteractionQueryService:
    """互动查询服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_interactions(
        self, 
        query: InteractionQuery, 
        pagination: PaginationParams
    ) -> PaginationResult[InteractionInfo]:
        """获取互动列表"""
        # 构建查询条件
        conditions = []
        
        if query.interaction_type:
            conditions.append(Interaction.interaction_type == query.interaction_type)
        
        if query.target_id:
            conditions.append(Interaction.target_id == query.target_id)
        
        if query.user_id:
            conditions.append(Interaction.user_id == query.user_id)
        
        if query.status:
            conditions.append(Interaction.status == query.status)
        else:
            # 默认只查询active状态的记录
            conditions.append(Interaction.status == "active")

        # 构建查询
        stmt = select(Interaction).where(and_(*conditions)).order_by(desc(Interaction.create_time))
        
        # 执行分页查询
        total_stmt = select(Interaction).where(and_(*conditions))
        total_result = await self.db.execute(total_stmt)
        total = len(total_result.scalars().all())

        # 分页
        stmt = stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        result = await self.db.execute(stmt)
        interactions = result.scalars().all()

        # 转换为Pydantic模型
        interaction_infos = [InteractionInfo.model_validate(interaction) for interaction in interactions]

        return PaginationResult(
            datas=interaction_infos,
            total=total,
            current_page=pagination.page,
            page_size=pagination.page_size
        )

    async def get_interactions_by_target(
        self, 
        interaction_type: str, 
        target_id: int, 
        pagination: PaginationParams
    ) -> PaginationResult[InteractionUserInfo]:
        """获取指定目标的互动用户列表"""
        stmt = select(Interaction).where(
            and_(
                Interaction.interaction_type == interaction_type,
                Interaction.target_id == target_id,
                Interaction.status == "active"
            )
        ).order_by(desc(Interaction.create_time))

        # 获取总数
        total_stmt = select(Interaction).where(
            and_(
                Interaction.interaction_type == interaction_type,
                Interaction.target_id == target_id,
                Interaction.status == "active"
            )
        )
        total_result = await self.db.execute(total_stmt)
        total = len(total_result.scalars().all())

        # 分页查询
        stmt = stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        result = await self.db.execute(stmt)
        interactions = result.scalars().all()

        # 转换为用户信息
        user_infos = []
        for interaction in interactions:
            user_info = InteractionUserInfo(
                user_id=interaction.user_id,
                user_nickname=interaction.user_nickname or "未知用户",
                user_avatar=interaction.user_avatar,
                interaction_time=interaction.create_time
            )
            user_infos.append(user_info)

        return PaginationResult(
            datas=user_infos,
            total=total,
            current_page=pagination.page,
            page_size=pagination.page_size
        )

    async def get_user_interactions(
        self, 
        user_id: int, 
        interaction_type: Optional[str] = None,
        pagination: PaginationParams = None
    ) -> PaginationResult[InteractionInfo]:
        """获取用户的互动记录"""
        conditions = [Interaction.user_id == user_id, Interaction.status == "active"]
        
        if interaction_type:
            conditions.append(Interaction.interaction_type == interaction_type)

        stmt = select(Interaction).where(and_(*conditions)).order_by(desc(Interaction.create_time))

        # 获取总数
        total_stmt = select(Interaction).where(and_(*conditions))
        total_result = await self.db.execute(total_stmt)
        total = len(total_result.scalars().all())

        # 分页查询
        if pagination:
            stmt = stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        
        result = await self.db.execute(stmt)
        interactions = result.scalars().all()

        # 转换为Pydantic模型
        interaction_infos = [InteractionInfo.model_validate(interaction) for interaction in interactions]

        if pagination:
            return PaginationResult(
                datas=interaction_infos,
                total=total,
                current_page=pagination.page,
                page_size=pagination.page_size
            )
        else:
            return PaginationResult(
                datas=interaction_infos,
                total=total,
                current_page=1,
                page_size=total
            ) 