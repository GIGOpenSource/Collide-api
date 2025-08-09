from typing import List, Dict
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.category.models import Category
from app.domains.category.schemas import CategoryInfo, CategoryQuery, CategoryTreeNode


class CategoryQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_category_by_id(self, category_id: int) -> CategoryInfo:
        category = (await self.db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
        if not category:
            from app.common.exceptions import BusinessException
            raise BusinessException("分类不存在")
        return CategoryInfo.model_validate(category)

    async def get_category_list(self, query: CategoryQuery, pagination: PaginationParams) -> PaginationResult[CategoryInfo]:
        stmt = select(Category)
        conditions = [
            Category.status == "active"  # 强制只查询 active 状态
        ]
        if query.keyword:
            conditions.append(Category.name.contains(query.keyword))
        if query.parent_id is not None:
            conditions.append(Category.parent_id == query.parent_id)
        
        stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Category.sort.desc(), Category.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [CategoryInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_category_tree(self) -> List[CategoryTreeNode]:
        """获取所有活跃分类，并构建成树形结构"""
        stmt = select(Category).where(Category.status == "active").order_by(Category.sort.desc(), Category.create_time.desc())
        rows = await self.db.execute(stmt)
        nodes = [CategoryTreeNode.model_validate(c) for c in rows.scalars().all()]
        
        node_map: Dict[int, CategoryTreeNode] = {node.id: node for node in nodes}
        tree: List[CategoryTreeNode] = []
        
        for node in nodes:
            if node.parent_id and node.parent_id in node_map:
                # 如果有父节点且父节点也在活跃列表里，则添加到父节点的children
                parent_node = node_map[node.parent_id]
                parent_node.children.append(node)
            else:
                # 否则视为顶级节点（parent_id为0或父节点不存在/不活跃）
                tree.append(node)
                
        return tree

    async def get_category_ancestors(self, category_id: int) -> List[CategoryInfo]:
        """获取指定分类的所有父级（面包屑导航）"""
        ancestors: List[CategoryInfo] = []
        current_id = category_id

        while current_id:
            stmt = select(Category).where(Category.id == current_id)
            category = (await self.db.execute(stmt)).scalar_one_or_none()

            if not category or category.status != 'active':
                # 如果当前分类不存在或不活跃，则停止查找
                break

            # 如果有父级，则将其加入列表，并继续向上查找
            if category.parent_id:
                parent_stmt = select(Category).where(Category.id == category.parent_id)
                parent = (await self.db.execute(parent_stmt)).scalar_one_or_none()
                if parent and parent.status == 'active':
                    ancestors.append(CategoryInfo.model_validate(parent))
                    current_id = parent.id
                else:
                    # 父节点不存在或不活跃，停止
                    break
            else:
                # 没有父级了，停止
                break

        # 结果是[父, 祖父, ...], 反转为 [祖父, 父, ...]
        return ancestors[::-1]

