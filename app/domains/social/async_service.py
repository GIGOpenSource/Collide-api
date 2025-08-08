"""
社交动态模块异步服务层
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func

from app.domains.social.models import SocialDynamic
from app.domains.social.schemas import DynamicCreate, DynamicUpdate, DynamicInfo, DynamicQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException


class SocialAsyncService:
    """社交动态异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dynamic(
        self,
        user_id: int,
        user_nickname: Optional[str],
        user_avatar: Optional[str],
        data: DynamicCreate,
    ) -> DynamicInfo:
        """发布动态"""
        try:
            dynamic = SocialDynamic(
                content=data.content,
                dynamic_type=data.dynamic_type,
                images=data.images,
                video_url=data.video_url,
                share_target_type=data.share_target_type,
                share_target_id=data.share_target_id,
                share_target_title=data.share_target_title,
                user_id=user_id,
                user_nickname=user_nickname,
                user_avatar=user_avatar,
                status="normal",
            )
            self.db.add(dynamic)
            await self.db.commit()
            await self.db.refresh(dynamic)
            return DynamicInfo.model_validate(dynamic)
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"发布动态失败: {str(e)}")

    async def update_dynamic(self, dynamic_id: int, user_id: int, data: DynamicUpdate) -> DynamicInfo:
        """更新动态（仅作者可改）"""
        try:
            stmt = select(SocialDynamic).where(and_(SocialDynamic.id == dynamic_id, SocialDynamic.user_id == user_id))
            dynamic = (await self.db.execute(stmt)).scalar_one_or_none()
            if not dynamic:
                raise BusinessException("动态不存在或无权限")

            update_values = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
            if update_values:
                await self.db.execute(update(SocialDynamic).where(SocialDynamic.id == dynamic_id).values(**update_values))
                await self.db.commit()
                await self.db.refresh(dynamic)
            return DynamicInfo.model_validate(dynamic)
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新动态失败: {str(e)}")

    async def delete_dynamic(self, dynamic_id: int, user_id: int) -> bool:
        """删除动态（软/硬删除：这里直接删除，后续可改为状态置位）"""
        try:
            result = await self.db.execute(delete(SocialDynamic).where(and_(SocialDynamic.id == dynamic_id, SocialDynamic.user_id == user_id)))
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除动态失败: {str(e)}")

    async def get_dynamic_by_id(self, dynamic_id: int) -> DynamicInfo:
        """获取动态详情"""
        stmt = select(SocialDynamic).where(SocialDynamic.id == dynamic_id)
        dynamic = (await self.db.execute(stmt)).scalar_one_or_none()
        if not dynamic:
            raise BusinessException("动态不存在")
        return DynamicInfo.model_validate(dynamic)

    async def list_dynamics(self, query: DynamicQuery, pagination: PaginationParams) -> PaginationResult[DynamicInfo]:
        """获取动态列表（关键词/类型/用户/状态筛选 + 分页 + 时间倒序）"""
        stmt = select(SocialDynamic)
        conditions = []
        if query.keyword:
            conditions.append(SocialDynamic.content.contains(query.keyword))
        if query.dynamic_type:
            conditions.append(SocialDynamic.dynamic_type == query.dynamic_type)
        if query.user_id is not None:
            conditions.append(SocialDynamic.user_id == query.user_id)
        if query.status:
            conditions.append(SocialDynamic.status == query.status)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(SocialDynamic.create_time.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()

        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        items = [DynamicInfo.model_validate(r) for r in rows]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

