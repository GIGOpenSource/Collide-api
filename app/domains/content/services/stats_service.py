from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.domains.content.models import Content


class ContentStatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def increment_content_stats(self, content_id: int, stat_type: str, increment_value: int = 1) -> bool:
        if stat_type == "view_count":
            await self.db.execute(update(Content).where(Content.id == content_id).values(view_count=Content.view_count + increment_value))
        elif stat_type == "like_count":
            await self.db.execute(update(Content).where(Content.id == content_id).values(like_count=Content.like_count + increment_value))
        elif stat_type == "favorite_count":
            await self.db.execute(update(Content).where(Content.id == content_id).values(favorite_count=Content.favorite_count + increment_value))
        elif stat_type == "comment_count":
            await self.db.execute(update(Content).where(Content.id == content_id).values(comment_count=Content.comment_count + increment_value))
        elif stat_type == "share_count":
            await self.db.execute(update(Content).where(Content.id == content_id).values(share_count=Content.share_count + increment_value))
        else:
            raise BusinessException("不支持的统计类型")
        await self.db.commit()
        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")
        return True

