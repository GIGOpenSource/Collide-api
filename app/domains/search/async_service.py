"""
搜索模块异步服务层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, and_, func, or_

from app.domains.search.models import SearchHistory, HotSearch
from app.domains.search.schemas import SearchRequest, SearchHistoryInfo, HotSearchInfo, SearchResult
from app.domains.content.models import Content
from app.domains.users.models import User
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class SearchAsyncService:
    """搜索异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_content(self, keyword: str, pagination: PaginationParams) -> PaginationResult[dict]:
        """搜索内容"""
        conditions = [
            Content.status == "PUBLISHED",
            Content.review_status == "APPROVED",
            or_(
                Content.title.contains(keyword),
                Content.description.contains(keyword),
                Content.tags.contains(keyword),
                Content.author_nickname.contains(keyword)
            )
        ]

        stmt = select(Content).where(and_(*conditions)).order_by(Content.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        contents = result.scalars().all()

        content_list = []
        for content in contents:
            content_list.append({
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "content_type": content.content_type,
                "author_id": content.author_id,
                "author_nickname": content.author_nickname,
                "cover_url": content.cover_url,
                "view_count": content.view_count,
                "like_count": content.like_count,
                "create_time": content.create_time.isoformat() if content.create_time else None
            })

        return PaginationResult.create(
            items=content_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def search_users(self, keyword: str, pagination: PaginationParams) -> PaginationResult[dict]:
        """搜索用户"""
        conditions = [
            User.status == "active",
            or_(
                User.username.contains(keyword),
                User.nickname.contains(keyword),
                User.email.contains(keyword)
            )
        ]

        stmt = select(User).where(and_(*conditions)).order_by(User.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "email": user.email,
                "status": user.status,
                "create_time": user.create_time.isoformat() if user.create_time else None
            })

        return PaginationResult.create(
            items=user_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

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
            await self.record_search_history(user_id, req.keyword, req.search_type, result.total)

        # 更新热搜统计
        await self.update_hot_search(req.keyword)

        return SearchResult(
            keyword=req.keyword,
            search_type=req.search_type,
            result_count=result.total,
            results=result.items
        )

    async def record_search_history(self, user_id: int, keyword: str, search_type: str, result_count: int):
        """记录搜索历史"""
        await self.db.execute(insert(SearchHistory).values(
            user_id=user_id,
            keyword=keyword,
            search_type=search_type,
            result_count=result_count
        ))
        await self.db.commit()

    async def update_hot_search(self, keyword: str):
        """更新热搜统计"""
        # 查找或创建热搜记录
        hot_search = (await self.db.execute(
            select(HotSearch).where(HotSearch.keyword == keyword)
        )).scalar_one_or_none()

        if hot_search:
            # 更新搜索次数
            await self.db.execute(
                update(HotSearch).where(HotSearch.id == hot_search.id).values(
                    search_count=HotSearch.search_count + 1
                )
            )
        else:
            # 创建新记录
            await self.db.execute(insert(HotSearch).values(
                keyword=keyword,
                search_count=1
            ))
        await self.db.commit()

    async def get_search_history(self, user_id: int, search_type: Optional[str] = None) -> List[SearchHistoryInfo]:
        """获取搜索历史"""
        conditions = [SearchHistory.user_id == user_id]
        if search_type:
            conditions.append(SearchHistory.search_type == search_type)

        stmt = select(SearchHistory).where(and_(*conditions)).order_by(SearchHistory.create_time.desc()).limit(20)
        result = await self.db.execute(stmt)
        histories = result.scalars().all()

        return [SearchHistoryInfo.model_validate(history) for history in histories]

    async def get_hot_searches(self, limit: int = 10) -> List[HotSearchInfo]:
        """获取热门搜索"""
        stmt = select(HotSearch).where(HotSearch.status == "active").order_by(HotSearch.search_count.desc()).limit(limit)
        result = await self.db.execute(stmt)
        hot_searches = result.scalars().all()

        return [HotSearchInfo.model_validate(hot_search) for hot_search in hot_searches] 