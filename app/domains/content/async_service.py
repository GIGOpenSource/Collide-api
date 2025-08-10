"""
内容模块异步服务层（门面）
拆分子服务：创建、查询、更新、章节、付费、统计、评分
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.atomic import atomic_transaction
from app.domains.content.schemas import (
    ContentCreate, ContentUpdate, ContentInfo, ContentQueryParams,
    ChapterCreate, ChapterUpdate, ChapterInfo, ChapterListItem,
    ContentPaymentCreate, ContentPaymentInfo,
    UserContentPurchaseCreate, UserContentPurchaseInfo,
    PublishContentRequest, ContentStatsUpdate, ScoreContentRequest
)
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.content.services.create_service import ContentCreateService
from app.domains.content.services.query_service import ContentQueryService
from app.domains.content.services.update_service import ContentUpdateService
from app.domains.content.services.chapter_service import ContentChapterService
from app.domains.content.services.payment_service import ContentPaymentService
from app.domains.content.services.stats_service import ContentStatsService
from app.domains.content.services.rating_service import ContentRatingService


class ContentAsyncService:
    """内容异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_content(self, content_data: ContentCreate, user_id: int) -> ContentInfo:
        # 获取用户信息
        from app.domains.users.models import User
        from sqlalchemy import select
        
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            from app.common.exceptions import BusinessException
            raise BusinessException("用户不存在")
        
        return await ContentCreateService(self.db).create_content(
            content_data, 
            user_id, 
            user.nickname or user.username,
            user.avatar or ""
        )

    async def get_content_by_id(self, content_id: int, user_id: Optional[int] = None) -> ContentInfo:
        return await ContentQueryService(self.db).get_content_by_id(content_id)

    async def update_content(self, content_id: int, content_data: ContentUpdate, user_id: int) -> ContentInfo:
        return await ContentUpdateService(self.db).update_content(content_id, content_data, user_id)

    async def delete_content(self, content_id: int, user_id: int) -> bool:
        return await ContentUpdateService(self.db).delete_content(content_id, user_id)

    async def get_content_list(self, query_params: ContentQueryParams, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[ContentInfo]:
        return await ContentQueryService(self.db).get_content_list(query_params, pagination, current_user_id)

    async def increment_content_stats(self, content_id: int, stat_type: str, increment_value: int = 1) -> bool:
        return await ContentStatsService(self.db).increment_content_stats(content_id, stat_type, increment_value)

    async def score_content(self, content_id: int, user_id: int, score_request: ScoreContentRequest) -> bool:
        return await ContentRatingService(self.db).score_content(content_id, user_id, score_request)

    # ================ 章节相关方法 ================

    async def create_chapter(self, chapter_data: ChapterCreate, user_id: int) -> ChapterInfo:
        return await ContentChapterService(self.db).create_chapter(chapter_data, user_id)

    async def get_content_chapters(self, content_id: int, user_id: Optional[int] = None) -> List[ChapterListItem]:
        return await ContentQueryService(self.db).get_content_chapters(content_id)

    # ================ 付费相关方法 ================

    @atomic_transaction()
    async def create_content_payment(self, content_id: int, payment_data: ContentPaymentCreate, user_id: int) -> ContentPaymentInfo:
        return await ContentPaymentService(self.db).create_content_payment(content_id, payment_data, user_id)

    async def get_content_payment(self, content_id: int) -> Optional[ContentPaymentInfo]:
        return await ContentPaymentService(self.db).get_content_payment(content_id)

    # ================ 聚合查询方法 ================

    async def get_content_list_by_category_name(self, category_name: str, match: str, query_params: ContentQueryParams, pagination: PaginationParams) -> PaginationResult[ContentInfo]:
        """根据分类名称查询内容 - 带缓存"""
        # 生成缓存键
        cache_key = f"content:category:{category_name}:{match}:{hash(str(query_params.model_dump()) + str(pagination.model_dump()))}"
        
        # 尝试从缓存获取
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.model_validate(cached_result)

        # 这里需要关联分类表查询，简化处理
        # 实际实现中需要根据分类名称查询分类ID，然后查询内容
        
        # 模拟查询结果
        contents = []
        total = 0

        pagination_result = PaginationResult.create(
            items=contents,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

        # 缓存结果（短期缓存）
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)

        return pagination_result
