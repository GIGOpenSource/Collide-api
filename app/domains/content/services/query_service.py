from typing import Optional, List

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.content.models import Content, ContentChapter
from app.domains.content.schemas import ContentInfo, ContentQueryParams, ChapterListItem


class ContentQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_content_by_id(self, content_id: int, current_user_id: Optional[int] = None) -> ContentInfo:
        cached = await cache_service.get_content_cache(content_id)
        if cached:
            # 即使有缓存，也要检查权限
            info_from_cache = ContentInfo.model_validate(cached)
            if info_from_cache.review_status != "APPROVED" and info_from_cache.author_id != current_user_id:
                 raise BusinessException("内容不存在或无权查看")
            return info_from_cache

        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")

        # 权限检查
        if content.review_status != "APPROVED" and content.author_id != current_user_id:
            raise BusinessException("内容不存在或无权查看")

        info = ContentInfo.model_validate(content)
        await cache_service.set_content_cache(content_id, info.model_dump())
        return info

    async def get_content_list(
        self,
        query_params: ContentQueryParams,
        pagination: PaginationParams,
        current_user_id: Optional[int] = None
    ) -> PaginationResult[ContentInfo]:
        cache_key = f"content:list:{hash(str(query_params.model_dump()) + str(pagination.model_dump()))}"
        cached = await cache_service.get(cache_key)
        if cached:
            return PaginationResult.model_validate(cached)

        conditions = []

        # 根据用户身份决定 review_status 的过滤策略
        is_owner_query = query_params.author_id and query_params.author_id == current_user_id
        if not is_owner_query:
            # 非作者本人查询，强制只看已发布的
            conditions.append(Content.review_status == "APPROVED")

        if query_params.content_type:
            conditions.append(Content.content_type == query_params.content_type)
        if query_params.category_id:
            conditions.append(Content.category_id == query_params.category_id)
        if query_params.author_id:
            conditions.append(Content.author_id == query_params.author_id)
        
        # 移除前端指定的 status 和 review_status
        # if query_params.status:
        #     conditions.append(Content.status == query_params.status)
        # if query_params.review_status:
        #     conditions.append(Content.review_status == query_params.review_status)

        if query_params.keyword:
            conditions.append(or_(
                Content.title.contains(query_params.keyword),
                Content.description.contains(query_params.keyword),
                Content.tags.contains(query_params.keyword),
            ))

        if query_params.min_view_count is not None:
            conditions.append(Content.view_count >= query_params.min_view_count)
        if query_params.max_view_count is not None:
            conditions.append(Content.view_count <= query_params.max_view_count)
        if query_params.min_like_count is not None:
            conditions.append(Content.like_count >= query_params.min_like_count)
        if query_params.max_like_count is not None:
            conditions.append(Content.like_count <= query_params.max_like_count)
        if query_params.min_favorite_count is not None:
            conditions.append(Content.favorite_count >= query_params.min_favorite_count)
        if query_params.max_favorite_count is not None:
            conditions.append(Content.favorite_count <= query_params.max_favorite_count)
        if query_params.min_comment_count is not None:
            conditions.append(Content.comment_count >= query_params.min_comment_count)
        if query_params.max_comment_count is not None:
            conditions.append(Content.comment_count <= query_params.max_comment_count)

        if query_params.publish_date_start:
            conditions.append(Content.publish_time >= query_params.publish_date_start)
        if query_params.publish_date_end:
            conditions.append(Content.publish_time <= query_params.publish_date_end)
        if query_params.create_date_start:
            conditions.append(Content.create_time >= query_params.create_date_start)
        if query_params.create_date_end:
            conditions.append(Content.create_time <= query_params.create_date_end)

        stmt = select(Content)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        from sqlalchemy import case
        average_score = case(
            (Content.score_count > 0, Content.score_total / Content.score_count),
            else_=0.0
        ).label("average_score")

        order_map = {
            "create_time": Content.create_time,
            "update_time": Content.update_time,
            "publish_time": Content.publish_time,
            "view_count": Content.view_count,
            "like_count": Content.like_count,
            "favorite_count": Content.favorite_count,
            "comment_count": Content.comment_count,
            "score": average_score,
        }
        order_by = order_map.get(query_params.sort_by or "create_time", Content.create_time)
        stmt = stmt.order_by(order_by.asc() if query_params.sort_order == "asc" else order_by.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [ContentInfo.model_validate(x) for x in rows.scalars().all()]
        result = PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        await cache_service.set(cache_key, result.model_dump(), ttl=300)
        return result

    async def get_content_chapters(self, content_id: int) -> List[ChapterListItem]:
        cache_key = f"chapters:content:{content_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            from app.domains.content.schemas import ChapterListItem
            return [ChapterListItem.model_validate(c) for c in cached]
        rows = await self.db.execute(select(ContentChapter).where(ContentChapter.content_id == content_id).order_by(ContentChapter.chapter_num))
        chap_list = rows.scalars().all()
        items = [ChapterListItem.model_validate(c) for c in chap_list]
        await cache_service.set(cache_key, [c.model_dump() for c in items], ttl=1800)
        return items

