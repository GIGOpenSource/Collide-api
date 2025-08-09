from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.domains.content.models import Content
from app.domains.content.schemas import ContentCreate, ContentInfo


class ContentCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_content(
        self,
        content_data: ContentCreate,
        user_id: int,
        user_nickname: str,
        user_avatar: str
    ) -> ContentInfo:
        content = Content(
            **content_data.model_dump(),
            author_id=user_id,
            author_nickname=user_nickname,
            author_avatar=user_avatar,
            review_status="PENDING",  # 强制设置为待审核
            status="DRAFT"  # 新建内容默认为草稿状态
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("user:stats:*")
        return ContentInfo.model_validate(content)

