from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.search.models import HotSearch


class HotSearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_hot(self, keyword: str):
        hot = (await self.db.execute(select(HotSearch).where(HotSearch.keyword == keyword))).scalar_one_or_none()
        if hot:
            await self.db.execute(update(HotSearch).where(HotSearch.id == hot.id).values(search_count=HotSearch.search_count + 1))
        else:
            await self.db.execute(HotSearch.__table__.insert().values(keyword=keyword, search_count=1))
        await self.db.commit()

    async def get_hot(self, limit: int = 10) -> list[dict]:
        rows = await self.db.execute(select(HotSearch).where(HotSearch.status == "active").order_by(HotSearch.search_count.desc()).limit(limit))
        items = rows.scalars().all()
        return [
            {"id": h.id, "keyword": h.keyword, "search_count": h.search_count}
            for h in items
        ]

