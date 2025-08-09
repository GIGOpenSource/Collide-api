"""
搜索模块异步服务层（门面）
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.search.schemas import SearchRequest, SearchHistoryInfo, HotSearchInfo, SearchResult
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.search.services.query_service import SearchQueryService
from app.domains.search.services.history_service import SearchHistoryService
from app.domains.search.services.hot_service import HotSearchService


class SearchAsyncService:
    """搜索异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_content(self, keyword: str, pagination: PaginationParams) -> PaginationResult[dict]:
        return await SearchQueryService(self.db).search_content(keyword, pagination)

    async def search_users(self, keyword: str, pagination: PaginationParams) -> PaginationResult[dict]:
        return await SearchQueryService(self.db).search_users(keyword, pagination)

    async def search(self, req: SearchRequest, user_id: Optional[int], pagination: PaginationParams) -> SearchResult:
        """执行搜索"""
        if req.search_type == "content":
            result = await self.search_content(req.keyword, pagination)
        elif req.search_type == "user":
            result = await self.search_users(req.keyword, pagination)
        else:
            raise BusinessException("不支持的搜索类型")

        # 记录搜索历史
        if user_id:
            await SearchHistoryService(self.db).record(user_id, req.keyword, req.search_type, result.total)

        # 更新热搜统计
        await HotSearchService(self.db).update_hot(req.keyword)

        return SearchResult(
            keyword=req.keyword,
            search_type=req.search_type,
            result_count=result.total,
            results=result.items
        )

    # 下沉到 SearchHistoryService

    # 下沉到 HotSearchService

    async def get_search_history(self, user_id: int, search_type: Optional[str] = None) -> List[SearchHistoryInfo]:
        rows = await SearchHistoryService(self.db).get_history(user_id, search_type)
        return [SearchHistoryInfo(**r) for r in rows]

    async def get_hot_searches(self, limit: int = 10) -> List[HotSearchInfo]:
        rows = await HotSearchService(self.db).get_hot(limit)
        return [HotSearchInfo(**r) for r in rows]