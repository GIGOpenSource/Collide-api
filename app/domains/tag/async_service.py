"""
标签模块异步服务层（门面）
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.tag.schemas import TagCreate, TagUpdate, TagInfo, UserInterestTagCreate, UserInterestTagInfo, ContentTagCreate, TagQuery
from app.domains.tag.models import Tag, ContentTag
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.tag.services.create_service import TagCreateService
from app.domains.tag.services.update_service import TagUpdateService
from app.domains.tag.services.query_service import TagQueryService


class TagAsyncService:
    """标签异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, req: TagCreate) -> TagInfo:
        return await TagCreateService(self.db).create_tag(req)

    async def update_tag(self, tag_id: int, req: TagUpdate) -> TagInfo:
        return await TagUpdateService(self.db).update_tag(tag_id, req)

    async def delete_tag(self, tag_id: int):
        from sqlalchemy import select, delete, func
        from app.common.exceptions import BusinessException
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")
        usage_count = (await self.db.execute(select(func.count()).select_from(ContentTag).where(ContentTag.tag_id == tag_id))).scalar()
        if usage_count > 0:
            raise BusinessException("标签正在使用中，无法删除")
        await self.db.execute(delete(Tag).where(Tag.id == tag_id))
        await self.db.commit()

    async def get_tag_by_id(self, tag_id: int) -> TagInfo:
        return await TagQueryService(self.db).get_tag_by_id(tag_id)

    async def get_tag_list(self, query: TagQuery, pagination: PaginationParams) -> PaginationResult[TagInfo]:
        return await TagQueryService(self.db).get_tag_list(query, pagination)

    async def add_user_interest_tag(self, user_id: int, req: UserInterestTagCreate) -> UserInterestTagInfo:
        info = await TagCreateService(self.db).add_user_interest_tag(user_id, req)
        return info

    async def get_user_interest_tags(self, user_id: int) -> List[UserInterestTagInfo]:
        return await TagQueryService(self.db).get_user_interest_tags(user_id)

    async def add_content_tags(self, req: ContentTagCreate):
        return await TagCreateService(self.db).add_content_tags(req.content_id, req.tag_ids, req.tag_names)

    async def get_content_tags(self, content_id: int) -> List[TagInfo]:
        """获取内容的标签"""
        stmt = select(ContentTag).where(ContentTag.content_id == content_id)
        result = await self.db.execute(stmt)
        content_tags = result.scalars().all()

        tag_list = []
        for content_tag in content_tags:
            tag = (await self.db.execute(select(Tag).where(Tag.id == content_tag.tag_id))).scalar_one_or_none()
            if tag:
                tag_list.append(TagInfo.model_validate(tag))

        return tag_list

    async def get_hot_tags(self, tag_type: Optional[str] = None, limit: int = 20) -> List[TagInfo]:
        """获取热门标签列表"""
        from sqlalchemy import desc
        
        stmt = select(Tag).order_by(desc(Tag.usage_count), desc(Tag.id))
        
        if tag_type:
            stmt = stmt.where(Tag.tag_type == tag_type)
        
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        tags = result.scalars().all()
        
        return [TagInfo.model_validate(tag) for tag in tags]

    async def search_tags_by_name(self, name: str, tag_type: Optional[str] = None, limit: int = 20) -> List[TagInfo]:
        """根据标签名称搜索标签"""
        from sqlalchemy import or_, desc
        
        stmt = select(Tag).where(
            or_(
                Tag.name.contains(name),
                Tag.name.like(f"%{name}%")
            )
        ).order_by(desc(Tag.usage_count), desc(Tag.id))
        
        if tag_type:
            stmt = stmt.where(Tag.tag_type == tag_type)
        
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        tags = result.scalars().all()
        
        return [TagInfo.model_validate(tag) for tag in tags]

    async def create_tag_by_name(self, name: str, tag_type: str = "content", description: Optional[str] = None, category_id: Optional[int] = None) -> TagInfo:
        """根据标签名称创建标签"""
        from sqlalchemy import and_
        from app.common.exceptions import BusinessException
        
        # 检查标签是否已存在
        existing_tag = (await self.db.execute(
            select(Tag).where(and_(Tag.name == name, Tag.tag_type == tag_type))
        )).scalar_one_or_none()
        
        if existing_tag:
            return TagInfo.model_validate(existing_tag)
        
        # 创建新标签
        tag = Tag(
            name=name,
            description=description or f"{tag_type}标签：{name}",
            tag_type=tag_type,
            category_id=category_id,
            status="active"
        )
        
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        
        return TagInfo.model_validate(tag) 