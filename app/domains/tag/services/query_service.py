from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.tag.models import Tag, UserInterestTag, ContentTag
from app.domains.tag.schemas import TagInfo, TagQuery, UserInterestTagInfo


class TagQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tag_by_id(self, tag_id: int) -> TagInfo:
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            from app.common.exceptions import BusinessException
            raise BusinessException("标签不存在")
        return TagInfo.model_validate(tag)

    async def get_tag_list(self, query: TagQuery, pagination: PaginationParams) -> PaginationResult[TagInfo]:
        conditions = []
        if query.tag_type:
            conditions.append(Tag.tag_type == query.tag_type)
        if query.category_id:
            conditions.append(Tag.category_id == query.category_id)
        if query.status:
            conditions.append(Tag.status == query.status)
        if query.keyword:
            conditions.append(or_(Tag.name.contains(query.keyword), Tag.description.contains(query.keyword)))
        stmt = select(Tag).where(and_(*conditions)).order_by(Tag.usage_count.desc(), Tag.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [TagInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_user_interest_tags(self, user_id: int) -> list[UserInterestTagInfo]:
        rows = await self.db.execute(select(UserInterestTag).where(and_(UserInterestTag.user_id == user_id, UserInterestTag.status == "active")).order_by(UserInterestTag.interest_score.desc()))
        interests = rows.scalars().all()
        result: list[UserInterestTagInfo] = []
        for it in interests:
            tag = (await self.db.execute(select(Tag).where(Tag.id == it.tag_id))).scalar_one()
            info = UserInterestTagInfo.model_validate(it)
            info.tag_info = TagInfo.model_validate(tag)
            result.append(info)
        return result

