from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
from app.domains.social.models import SocialDynamic
from app.domains.social.schemas import DynamicInfo, DynamicQuery


class SocialQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dynamic_by_id(self, dynamic_id: int) -> DynamicInfo:
        dynamic = (await self.db.execute(select(SocialDynamic).where(SocialDynamic.id == dynamic_id))).scalar_one_or_none()
        if not dynamic:
            raise BusinessException("动态不存在")
        return DynamicInfo.model_validate(dynamic)

    async def list_dynamics(self, query: DynamicQuery, pagination: PaginationParams) -> PaginationResult[DynamicInfo]:
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
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [DynamicInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

