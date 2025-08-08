"""
标签模块异步服务层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.tag.models import Tag, UserInterestTag, ContentTag
from app.domains.tag.schemas import TagCreate, TagUpdate, TagInfo, UserInterestTagCreate, UserInterestTagInfo, ContentTagCreate, TagQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class TagAsyncService:
    """标签异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, req: TagCreate) -> TagInfo:
        """创建标签"""
        # 检查标签名称是否已存在
        existing_tag = (await self.db.execute(
            select(Tag).where(and_(Tag.name == req.name, Tag.tag_type == req.tag_type))
        )).scalar_one_or_none()

        if existing_tag:
            raise BusinessException("标签名称已存在")

        tag = Tag(
            name=req.name,
            description=req.description,
            tag_type=req.tag_type,
            category_id=req.category_id
        )
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return TagInfo.model_validate(tag)

    async def update_tag(self, tag_id: int, req: TagUpdate) -> TagInfo:
        """更新标签"""
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")

        # 如果更新名称，检查是否重复
        if req.name and req.name != tag.name:
            existing_tag = (await self.db.execute(
                select(Tag).where(and_(Tag.name == req.name, Tag.tag_type == tag.tag_type, Tag.id != tag_id))
            )).scalar_one_or_none()
            if existing_tag:
                raise BusinessException("标签名称已存在")

        # 更新字段
        update_data = {}
        if req.name is not None:
            update_data["name"] = req.name
        if req.description is not None:
            update_data["description"] = req.description
        if req.tag_type is not None:
            update_data["tag_type"] = req.tag_type
        if req.category_id is not None:
            update_data["category_id"] = req.category_id
        if req.status is not None:
            update_data["status"] = req.status

        await self.db.execute(update(Tag).where(Tag.id == tag_id).values(**update_data))
        await self.db.commit()

        # 刷新数据
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one()
        return TagInfo.model_validate(tag)

    async def delete_tag(self, tag_id: int):
        """删除标签"""
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")

        # 检查是否有关联使用
        usage_count = (await self.db.execute(
            select(func.count()).select_from(ContentTag).where(ContentTag.tag_id == tag_id)
        )).scalar()

        if usage_count > 0:
            raise BusinessException("标签正在使用中，无法删除")

        await self.db.execute(delete(Tag).where(Tag.id == tag_id))
        await self.db.commit()

    async def get_tag_by_id(self, tag_id: int) -> TagInfo:
        """根据ID获取标签"""
        tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")
        return TagInfo.model_validate(tag)

    async def get_tag_list(self, query: TagQuery, pagination: PaginationParams) -> PaginationResult[TagInfo]:
        """获取标签列表"""
        conditions = []

        if query.tag_type:
            conditions.append(Tag.tag_type == query.tag_type)
        if query.category_id:
            conditions.append(Tag.category_id == query.category_id)
        if query.status:
            conditions.append(Tag.status == query.status)
        if query.keyword:
            conditions.append(or_(
                Tag.name.contains(query.keyword),
                Tag.description.contains(query.keyword)
            ))

        stmt = select(Tag).where(and_(*conditions)).order_by(Tag.usage_count.desc(), Tag.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        tags = result.scalars().all()

        tag_list = [TagInfo.model_validate(tag) for tag in tags]

        return PaginationResult.create(
            items=tag_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def add_user_interest_tag(self, user_id: int, req: UserInterestTagCreate) -> UserInterestTagInfo:
        """添加用户兴趣标签"""
        # 检查标签是否存在
        tag = (await self.db.execute(select(Tag).where(Tag.id == req.tag_id))).scalar_one_or_none()
        if not tag:
            raise BusinessException("标签不存在")

        # 检查是否已存在
        existing = (await self.db.execute(
            select(UserInterestTag).where(and_(UserInterestTag.user_id == user_id, UserInterestTag.tag_id == req.tag_id))
        )).scalar_one_or_none()

        if existing:
            # 更新兴趣分数
            await self.db.execute(
                update(UserInterestTag).where(UserInterestTag.id == existing.id).values(
                    interest_score=req.interest_score
                )
            )
            await self.db.commit()
            existing = (await self.db.execute(select(UserInterestTag).where(UserInterestTag.id == existing.id))).scalar_one()
        else:
            # 创建新记录
            user_interest_tag = UserInterestTag(
                user_id=user_id,
                tag_id=req.tag_id,
                interest_score=req.interest_score
            )
            self.db.add(user_interest_tag)
            await self.db.commit()
            await self.db.refresh(user_interest_tag)
            existing = user_interest_tag

        return UserInterestTagInfo.model_validate(existing)

    async def get_user_interest_tags(self, user_id: int) -> List[UserInterestTagInfo]:
        """获取用户兴趣标签"""
        stmt = select(UserInterestTag).where(
            and_(UserInterestTag.user_id == user_id, UserInterestTag.status == "active")
        ).order_by(UserInterestTag.interest_score.desc())
        
        result = await self.db.execute(stmt)
        interest_tags = result.scalars().all()

        interest_tag_list = []
        for interest_tag in interest_tags:
            # 获取标签信息
            tag = (await self.db.execute(select(Tag).where(Tag.id == interest_tag.tag_id))).scalar_one()
            interest_tag_info = UserInterestTagInfo.model_validate(interest_tag)
            interest_tag_info.tag_info = TagInfo.model_validate(tag)
            interest_tag_list.append(interest_tag_info)

        return interest_tag_list

    async def add_content_tags(self, req: ContentTagCreate):
        """为内容添加标签"""
        # 检查内容是否存在
        from app.domains.content.models import Content
        content = (await self.db.execute(select(Content).where(Content.id == req.content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")

        # 检查标签是否存在
        for tag_id in req.tag_ids:
            tag = (await self.db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()
            if not tag:
                raise BusinessException(f"标签ID {tag_id} 不存在")

        # 删除现有关联
        await self.db.execute(delete(ContentTag).where(ContentTag.content_id == req.content_id))

        # 添加新关联
        for tag_id in req.tag_ids:
            content_tag = ContentTag(content_id=req.content_id, tag_id=tag_id)
            self.db.add(content_tag)

        # 更新标签使用次数
        for tag_id in req.tag_ids:
            await self.db.execute(
                update(Tag).where(Tag.id == tag_id).values(usage_count=Tag.usage_count + 1)
            )

        await self.db.commit()

    async def get_content_tags(self, content_id: int) -> List[TagInfo]:
        """获取内容的标签"""
        stmt = select(ContentTag).where(ContentTag.content_id == content_id)
        result = await self.db.execute(stmt)
        content_tags = result.scalars().all()

        tag_list = []
        for content_tag in content_tags:
            tag = (await self.db.execute(select(Tag).where(Tag.id == content_tag.tag_id))).scalar_one()
            if tag:
                tag_list.append(TagInfo.model_validate(tag))

        return tag_list 