"""
分类模块异步服务层
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func

from app.domains.category.models import Category
from app.domains.category.schemas import CategoryCreate, CategoryUpdate, CategoryInfo, CategoryQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException


class CategoryAsyncService:
    """分类异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, data: CategoryCreate) -> CategoryInfo:
        """创建分类（名称+父分类唯一）"""
        try:
            # 唯一性检查：同一 parent_id 下 name 不重复
            stmt = select(Category.id).where(and_(Category.name == data.name, Category.parent_id == data.parent_id))
            exists = (await self.db.execute(stmt)).scalar_one_or_none()
            if exists:
                raise BusinessException("分类已存在")

            category = Category(
                name=data.name,
                description=data.description,
                parent_id=data.parent_id,
                icon_url=data.icon_url,
                sort=data.sort,
                status=data.status,
            )
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)
            return CategoryInfo.model_validate(category)
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建分类失败: {str(e)}")

    async def update_category(self, category_id: int, data: CategoryUpdate) -> CategoryInfo:
        """更新分类"""
        try:
            stmt = select(Category).where(Category.id == category_id)
            result = await self.db.execute(stmt)
            category = result.scalar_one_or_none()
            if not category:
                raise BusinessException("分类不存在")

            # 若修改名称或父分类，做唯一性检查
            new_name = data.name if data.name is not None else category.name
            new_parent = data.parent_id if data.parent_id is not None else category.parent_id
            if new_name != category.name or new_parent != category.parent_id:
                check_stmt = select(Category.id).where(and_(Category.name == new_name, Category.parent_id == new_parent, Category.id != category_id))
                dup = (await self.db.execute(check_stmt)).scalar_one_or_none()
                if dup:
                    raise BusinessException("同级下分类名称已存在")

            update_values = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
            if update_values:
                await self.db.execute(update(Category).where(Category.id == category_id).values(**update_values))
                await self.db.commit()
                await self.db.refresh(category)
            return CategoryInfo.model_validate(category)
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新分类失败: {str(e)}")

    async def delete_category(self, category_id: int) -> bool:
        """删除分类（若有子分类可选择先转移或级联，当前直接删除）"""
        try:
            result = await self.db.execute(delete(Category).where(Category.id == category_id))
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除分类失败: {str(e)}")

    async def get_category_by_id(self, category_id: int) -> CategoryInfo:
        """获取分类详情"""
        stmt = select(Category).where(Category.id == category_id)
        result = await self.db.execute(stmt)
        category = result.scalar_one_or_none()
        if not category:
            raise BusinessException("分类不存在")
        return CategoryInfo.model_validate(category)

    async def get_category_list(self, query: CategoryQuery, pagination: PaginationParams) -> PaginationResult[CategoryInfo]:
        """获取分类列表（支持关键词、父级、状态筛选，分页）"""
        stmt = select(Category)
        conditions = []
        if query.keyword:
            conditions.append(Category.name.contains(query.keyword))
        if query.parent_id is not None:
            conditions.append(Category.parent_id == query.parent_id)
        if query.status is not None:
            conditions.append(Category.status == query.status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 排序：sort 降序，create_time 降序
        stmt = stmt.order_by(Category.sort.desc(), Category.create_time.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()

        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        items = [CategoryInfo.model_validate(r) for r in rows]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

