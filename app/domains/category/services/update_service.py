from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.category.models import Category
from app.domains.category.schemas import CategoryUpdate, CategoryInfo


class CategoryUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_category(self, category_id: int, data: CategoryUpdate) -> CategoryInfo:
        stmt = select(Category).where(Category.id == category_id)
        category = (await self.db.execute(stmt)).scalar_one_or_none()
        if not category:
            raise BusinessException("分类不存在")
        new_name = data.name if data.name is not None else category.name
        new_parent = data.parent_id if data.parent_id is not None else category.parent_id
        if new_name != category.name or new_parent != category.parent_id:
            dup = (await self.db.execute(select(Category.id).where(and_(Category.name == new_name, Category.parent_id == new_parent, Category.id != category_id)))).scalar_one_or_none()
            if dup:
                raise BusinessException("同级下分类名称已存在")
        update_values = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
        if update_values:
            await self.db.execute(update(Category).where(Category.id == category_id).values(**update_values))
            await self.db.commit()
            await self.db.refresh(category)
        return CategoryInfo.model_validate(category)

