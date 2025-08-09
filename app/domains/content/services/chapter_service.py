from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.domains.content.models import Content, ContentChapter
from app.domains.content.schemas import ChapterCreate, ChapterUpdate, ChapterInfo


class ContentChapterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chapter(self, chapter_data: ChapterCreate, user_id: int) -> ChapterInfo:
        content = (await self.db.execute(select(Content).where(Content.id == chapter_data.content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if content.author_id != user_id:
            raise BusinessException("无权限为此内容创建章节")
        existing = (await self.db.execute(select(ContentChapter).where(and_(ContentChapter.content_id == chapter_data.content_id, ContentChapter.chapter_num == chapter_data.chapter_num)))).scalar_one_or_none()
        if existing:
            raise BusinessException("章节号已存在")
        chapter = ContentChapter(
            content_id=chapter_data.content_id,
            chapter_num=chapter_data.chapter_num,
            title=chapter_data.title,
            content=chapter_data.content,
            word_count=chapter_data.word_count or len(chapter_data.content),
            status="DRAFT",
        )
        self.db.add(chapter)
        await self.db.commit()
        await self.db.refresh(chapter)
        await cache_service.delete_pattern("chapter:*")
        await cache_service.delete_content_cache(chapter_data.content_id)
        return ChapterInfo.model_validate(chapter)

