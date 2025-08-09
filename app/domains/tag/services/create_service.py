from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.tag.models import Tag, UserInterestTag, ContentTag
from app.domains.tag.schemas import TagCreate, TagInfo, UserInterestTagCreate


class TagCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, req: TagCreate) -> TagInfo:
        existing = (await self.db.execute(select(Tag).where(and_(Tag.name == req.name, Tag.tag_type == req.tag_type)))).scalar_one_or_none()
        if existing:
            raise BusinessException("标签名称已存在")
        tag = Tag(name=req.name, description=req.description, tag_type=req.tag_type, category_id=req.category_id)
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return TagInfo.model_validate(tag)

    async def add_user_interest_tag(self, user_id: int, req: UserInterestTagCreate):
        tag = (await self.db.execute(select(Tag).where(Tag.id == req.tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")
        existing = (await self.db.execute(select(UserInterestTag).where(and_(UserInterestTag.user_id == user_id, UserInterestTag.tag_id == req.tag_id)))).scalar_one_or_none()
        if existing:
            await self.db.execute(UserInterestTag.__table__.update().where(UserInterestTag.id == existing.id).values(interest_score=req.interest_score))
            await self.db.commit()
            existing = (await self.db.execute(select(UserInterestTag).where(UserInterestTag.id == existing.id))).scalar_one()
            from app.domains.tag.schemas import UserInterestTagInfo
            return UserInterestTagInfo.model_validate(existing)
        ut = UserInterestTag(user_id=user_id, tag_id=req.tag_id, interest_score=req.interest_score)
        self.db.add(ut)
        await self.db.commit()
        await self.db.refresh(ut)
        from app.domains.tag.schemas import UserInterestTagInfo
        return UserInterestTagInfo.model_validate(ut)

    async def add_content_tags(self, content_id: int, tag_ids: list[int]):
        from app.domains.content.models import Content
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        # 校验标签存在
        for tid in tag_ids:
            if (await self.db.execute(select(Tag).where(Tag.id == tid))).scalar_one_or_none() is None:
                raise BusinessException(f"标签ID {tid} 不存在")
        # 清空并重建关联
        await self.db.execute(ContentTag.__table__.delete().where(ContentTag.content_id == content_id))
        for tid in tag_ids:
            self.db.add(ContentTag(content_id=content_id, tag_id=tid))
            await self.db.execute(Tag.__table__.update().where(Tag.id == tid).values(usage_count=Tag.usage_count + 1))
        await self.db.commit()

