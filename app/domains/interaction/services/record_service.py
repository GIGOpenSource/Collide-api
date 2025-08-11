"""
互动记录服务
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.domains.interaction.models import Interaction


class InteractionRecordService:
    """互动记录服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_interaction(
        self,
        interaction_type: str,
        target_id: int,
        user_id: int,
        user_nickname: str,
        user_avatar: Optional[str] = None,
        target_title: Optional[str] = None,
        target_author_id: Optional[int] = None
    ) -> Interaction:
        """记录互动"""
        # 检查是否已存在相同的互动记录
        existing_interaction = await self._get_existing_interaction(
            interaction_type, target_id, user_id
        )
        
        if existing_interaction:
            # 如果存在且状态为cancelled，则恢复为active
            if existing_interaction.status == "cancelled":
                existing_interaction.status = "active"
                await self.db.commit()
                return existing_interaction
            # 如果已经是active状态，直接返回
            return existing_interaction
        
        # 创建新的互动记录
        interaction = Interaction(
            interaction_type=interaction_type,
            target_id=target_id,
            user_id=user_id,
            user_nickname=user_nickname,
            user_avatar=user_avatar,
            target_title=target_title,
            target_author_id=target_author_id,
            status="active"
        )
        
        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)
        
        return interaction

    async def cancel_interaction(
        self,
        interaction_type: str,
        target_id: int,
        user_id: int
    ) -> Optional[Interaction]:
        """取消互动（软删除）"""
        interaction = await self._get_existing_interaction(
            interaction_type, target_id, user_id
        )
        
        if interaction and interaction.status == "active":
            interaction.status = "cancelled"
            await self.db.commit()
            return interaction
        
        return None

    async def _get_existing_interaction(
        self,
        interaction_type: str,
        target_id: int,
        user_id: int
    ) -> Optional[Interaction]:
        """获取已存在的互动记录"""
        stmt = select(Interaction).where(
            and_(
                Interaction.interaction_type == interaction_type,
                Interaction.target_id == target_id,
                Interaction.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() 