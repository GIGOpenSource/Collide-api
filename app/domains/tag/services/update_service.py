from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.tag.models import Tag
from app.domains.tag.schemas import TagUpdate, TagInfo


class TagUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_tag(self, tag_id: int, req: TagUpdate) -> TagInfo:
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")
        if req.name and req.name != tag.name:
            dup = (await self.db.execute(select(Tag).where(and_(Tag.name == req.name, Tag.tag_type == tag.tag_type, Tag.id != tag_id)))).scalar_one_or_none()
            if dup:
                raise BusinessException("标签名称已存在")
        update_data = {k: v for k, v in req.model_dump(exclude_unset=True).items()}
        if update_data:
            await self.db.execute(update(Tag).where(Tag.id == tag_id).values(**update_data))
            await self.db.commit()
            await self.db.refresh(tag)
        return TagInfo.model_validate(tag)

