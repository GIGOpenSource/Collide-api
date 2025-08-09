from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.category.models import Category
from app.domains.category.schemas import CategoryCreate, CategoryInfo


class CategoryCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, data: CategoryCreate) -> CategoryInfo:
        stmt = select(Category.id).where(and_(Category.name == data.name, Category.parent_id == data.parent_id))
        exists = (await self.db.execute(stmt)).scalar_one_or_none()
        if exists:
            raise BusinessException("分类已存在")
        category = Category(name=data.name, description=data.description, parent_id=data.parent_id, icon_url=data.icon_url, sort=data.sort, status=data.status)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return CategoryInfo.model_validate(category)

