from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.domains.content.models import Content
from app.domains.content.schemas import ScoreContentRequest


class ContentRatingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def score_content(self, content_id: int, user_id: int, score_request: ScoreContentRequest) -> bool:
        cached_result = await cache_service.check_idempotent(user_id, "score_content", content_id, score_request.score)
        if cached_result is not None:
            return cached_result.get("success", False)

        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if not (1 <= score_request.score <= 5):
            raise BusinessException("评分必须在1-5之间")

        new_score = (content.score * content.score_count + score_request.score) / (content.score_count + 1)
        new_score_count = content.score_count + 1
        await self.db.execute(update(Content).where(Content.id == content_id).values(score=new_score, score_count=new_score_count))
        await self.db.commit()
        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")
        result = {"success": True, "new_score": new_score, "new_score_count": new_score_count}
        await cache_service.set_idempotent_result(user_id, "score_content", result, content_id, score_request.score)
        return True

