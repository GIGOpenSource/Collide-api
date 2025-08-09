from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.task.models import TaskTemplate
from app.domains.task.schemas import TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateInfo, TaskQuery


class TaskTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, req: TaskTemplateCreate) -> TaskTemplateInfo:
        template = TaskTemplate(**req.model_dump())
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return TaskTemplateInfo.model_validate(template)

    async def update(self, template_id: int, req: TaskTemplateUpdate) -> TaskTemplateInfo:
        template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalar_one_or_none()
        if not template:
            raise BusinessException("任务模板不存在")
        update_data = {k: v for k, v in req.model_dump(exclude_unset=True).items()}
        if update_data:
            await self.db.execute(update(TaskTemplate).where(TaskTemplate.id == template_id).values(**update_data))
            await self.db.commit()
            await self.db.refresh(template)
        return TaskTemplateInfo.model_validate(template)

    async def delete(self, template_id: int):
        template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalar_one_or_none()
        if not template:
            raise BusinessException("任务模板不存在")
        await self.db.execute(delete(TaskTemplate).where(TaskTemplate.id == template_id))
        await self.db.commit()

    async def list(self, query: TaskQuery, pagination: PaginationParams) -> PaginationResult[TaskTemplateInfo]:
        conditions = []
        if query.task_type:
            conditions.append(TaskTemplate.task_type == query.task_type)
        if query.task_category:
            conditions.append(TaskTemplate.task_category == query.task_category)
        if query.is_active is not None:
            conditions.append(TaskTemplate.is_active == query.is_active)
        from sqlalchemy import and_
        stmt = select(TaskTemplate).where(and_(*conditions)).order_by(TaskTemplate.sort_order.asc(), TaskTemplate.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [TaskTemplateInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

