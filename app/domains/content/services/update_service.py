from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.domains.content.models import Content
from app.domains.content.schemas import ContentUpdate, ContentInfo


class ContentUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_content(self, content_id: int, content_data: ContentUpdate, user_id: int) -> ContentInfo:
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if content.author_id != user_id:
            raise BusinessException("无权限修改此内容")

        update_data = {}
        if content_data.title is not None:
            update_data["title"] = content_data.title
        if content_data.description is not None:
            update_data["description"] = content_data.description
        if content_data.content_type is not None:
            update_data["content_type"] = content_data.content_type
        if content_data.category_id is not None:
            update_data["category_id"] = content_data.category_id
        if content_data.content_data is not None:
            update_data["content_data"] = content_data.content_data
        if content_data.content_data_time is not None:
            update_data["content_data_time"] = content_data.content_data_time
        if content_data.cover_url is not None:
            update_data["cover_url"] = content_data.cover_url
        if content_data.tags is not None:
            update_data["tags"] = content_data.tags

        if update_data:
            await self.db.execute(update(Content).where(Content.id == content_id).values(**update_data))
            await self.db.commit()

        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")
        return await self._get_content(content_id)

    async def delete_content(self, content_id: int, user_id: int) -> bool:
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if content.author_id != user_id:
            raise BusinessException("无权限删除此内容")
        await self.db.execute(delete(Content).where(Content.id == content_id))
        await self.db.commit()
        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("user:stats:*")
        return True

    async def _get_content(self, content_id: int) -> ContentInfo:
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        return ContentInfo.model_validate(content)

