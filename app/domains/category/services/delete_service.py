from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.category.models import Category


class CategoryDeleteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_category(self, category_id: int) -> bool:
        result = await self.db.execute(delete(Category).where(Category.id == category_id))
        await self.db.commit()
        return result.rowcount > 0

