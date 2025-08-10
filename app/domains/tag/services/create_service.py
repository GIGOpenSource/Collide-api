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
        # 确定标签ID
        tag_id = req.tag_id
        if not tag_id and req.tag_name:
            # 通过标签名称查找或创建标签
            tag = (await self.db.execute(select(Tag).where(and_(Tag.name == req.tag_name, Tag.tag_type == "interest")))).scalar_one_or_none()
            if not tag:
                # 标签不存在，自动创建
                tag = Tag(
                    name=req.tag_name, 
                    description=f"用户兴趣标签：{req.tag_name}", 
                    tag_type="interest"
                )
                self.db.add(tag)
                await self.db.commit()
                await self.db.refresh(tag)
            tag_id = tag.id
        elif not tag_id and not req.tag_name:
            raise BusinessException("必须提供tag_id或tag_name")
        
        # 检查标签是否存在
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")
        
        # 检查是否已存在用户兴趣标签关联
        existing = (await self.db.execute(select(UserInterestTag).where(and_(UserInterestTag.user_id == user_id, UserInterestTag.tag_id == tag_id)))).scalar_one_or_none()
        if existing:
            # 更新兴趣分数
            await self.db.execute(UserInterestTag.__table__.update().where(UserInterestTag.id == existing.id).values(interest_score=req.interest_score))
            await self.db.commit()
            existing = (await self.db.execute(select(UserInterestTag).where(UserInterestTag.id == existing.id))).scalar_one()
            from app.domains.tag.schemas import UserInterestTagInfo
            return UserInterestTagInfo.model_validate(existing)
        
        # 创建新的用户兴趣标签关联
        ut = UserInterestTag(user_id=user_id, tag_id=tag_id, interest_score=req.interest_score)
        self.db.add(ut)
        await self.db.commit()
        await self.db.refresh(ut)
        from app.domains.tag.schemas import UserInterestTagInfo
        return UserInterestTagInfo.model_validate(ut)

    async def add_content_tags(self, content_id: int, tag_ids: list[int] = None, tag_names: list[str] = None):
        from app.domains.content.models import Content
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        
        # 确定要使用的标签ID列表
        final_tag_ids = []
        
        if tag_ids:
            # 使用提供的标签ID
            final_tag_ids = tag_ids
        elif tag_names:
            # 通过标签名称查找或创建标签
            for tag_name in tag_names:
                # 查找现有标签
                tag = (await self.db.execute(select(Tag).where(and_(Tag.name == tag_name, Tag.tag_type == "content")))).scalar_one_or_none()
                if not tag:
                    # 标签不存在，自动创建
                    tag = Tag(
                        name=tag_name, 
                        description=f"内容标签：{tag_name}", 
                        tag_type="content"
                    )
                    self.db.add(tag)
                    await self.db.commit()
                    await self.db.refresh(tag)
                final_tag_ids.append(tag.id)
        else:
            raise BusinessException("必须提供tag_ids或tag_names")
        
        # 校验标签存在
        for tid in final_tag_ids:
            if (await self.db.execute(select(Tag).where(Tag.id == tid))).scalar_one_or_none() is None:
                raise BusinessException(f"标签ID {tid} 不存在")
        
        # 清空并重建关联
        await self.db.execute(ContentTag.__table__.delete().where(ContentTag.content_id == content_id))
        for tid in final_tag_ids:
            self.db.add(ContentTag(content_id=content_id, tag_id=tid))
            await self.db.execute(Tag.__table__.update().where(Tag.id == tid).values(usage_count=Tag.usage_count + 1))
        await self.db.commit()

