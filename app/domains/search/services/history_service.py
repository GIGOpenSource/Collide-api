from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.search.models import SearchHistory


class SearchHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(self, user_id: int, keyword: str, search_type: str, result_count: int):
        await self.db.execute(insert(SearchHistory).values(user_id=user_id, keyword=keyword, search_type=search_type, result_count=result_count))
        await self.db.commit()

    async def get_history(self, user_id: int, search_type: str | None = None) -> list[dict]:
        from sqlalchemy import and_
        conditions = [SearchHistory.user_id == user_id]
        if search_type:
            conditions.append(SearchHistory.search_type == search_type)
        rows = await self.db.execute(select(SearchHistory).where(and_(*conditions)).order_by(SearchHistory.create_time.desc()).limit(20))
        histories = rows.scalars().all()
        return [
            {
                "id": h.id,
                "keyword": h.keyword,
                "search_type": h.search_type,
                "result_count": h.result_count,
                "create_time": h.create_time.isoformat() if h.create_time else None,
            }
            for h in histories
        ]

