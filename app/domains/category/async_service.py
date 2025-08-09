"""
分类模块异步服务层（门面）
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.category.schemas import CategoryCreate, CategoryUpdate, CategoryInfo, CategoryQuery, CategoryTreeNode
from app.domains.category.services.create_service import CategoryCreateService
from app.domains.category.services.update_service import CategoryUpdateService
from app.domains.category.services.query_service import CategoryQueryService
from app.domains.category.services.delete_service import CategoryDeleteService


class CategoryAsyncService:
    """分类异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.query_service = CategoryQueryService(self.db)

    async def create_category(self, data: CategoryCreate) -> CategoryInfo:
        return await CategoryCreateService(self.db).create_category(data)

    async def update_category(self, category_id: int, data: CategoryUpdate) -> CategoryInfo:
        return await CategoryUpdateService(self.db).update_category(category_id, data)

    async def delete_category(self, category_id: int) -> bool:
        return await CategoryDeleteService(self.db).delete_category(category_id)

    async def get_category_by_id(self, category_id: int) -> CategoryInfo:
        return await self.query_service.get_category_by_id(category_id)

    async def get_category_list(self, query: CategoryQuery, pagination: PaginationParams) -> PaginationResult[CategoryInfo]:
        return await self.query_service.get_category_list(query, pagination)

    async def get_category_tree(self) -> List[CategoryTreeNode]:
        return await self.query_service.get_category_tree()

    async def get_category_ancestors(self, category_id: int) -> List[CategoryInfo]:
        return await self.query_service.get_category_ancestors(category_id)

