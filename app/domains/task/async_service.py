"""
任务模块异步服务层（门面）
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.task.schemas import (
    TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateInfo, TaskRewardCreate, TaskRewardInfo,
    UserTaskRecordInfo, UserRewardRecordInfo, TaskProgressUpdate, TaskQuery
)
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.task.services.template_service import TaskTemplateService
from app.domains.task.services.reward_service import TaskRewardService
from app.domains.task.services.user_task_service import UserTaskService


class TaskAsyncService:
    """任务异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task_template(self, req: TaskTemplateCreate) -> TaskTemplateInfo:
        return await TaskTemplateService(self.db).create(req)

    async def update_task_template(self, template_id: int, req: TaskTemplateUpdate) -> TaskTemplateInfo:
        return await TaskTemplateService(self.db).update(template_id, req)

    async def delete_task_template(self, template_id: int):
        return await TaskTemplateService(self.db).delete(template_id)

    async def get_task_template_by_id(self, template_id: int) -> TaskTemplateInfo:
        rows = await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
        template = rows.scalar_one_or_none()
        if not template:
            from app.common.exceptions import BusinessException
            raise BusinessException("任务模板不存在")
        return TaskTemplateInfo.model_validate(template)

    async def get_task_template_list(self, query: TaskQuery, pagination: PaginationParams) -> PaginationResult[TaskTemplateInfo]:
        return await TaskTemplateService(self.db).list(query, pagination)

    async def create_task_reward(self, req: TaskRewardCreate) -> TaskRewardInfo:
        return await TaskRewardService(self.db).create(req)

    async def get_task_rewards(self, task_id: int) -> List[TaskRewardInfo]:
        return await TaskRewardService(self.db).list(task_id)

    async def get_user_tasks(self, user_id: int, task_date=None) -> List[UserTaskRecordInfo]:
        return await UserTaskService(self.db).get_user_tasks(user_id, task_date)

    async def update_task_progress(self, user_id: int, req: TaskProgressUpdate) -> List[UserTaskRecordInfo]:
        return await UserTaskService(self.db).update_task_progress(user_id, req)

    async def claim_task_reward(self, user_id: int, task_record_id: int) -> List[UserRewardRecordInfo]:
        return await UserTaskService(self.db).claim_task_reward(user_id, task_record_id)

    async def get_user_reward_records(self, user_id: int) -> List[UserRewardRecordInfo]:
        """获取用户奖励记录"""
        stmt = select(UserRewardRecord).where(UserRewardRecord.user_id == user_id).order_by(UserRewardRecord.create_time.desc())
        result = await self.db.execute(stmt)
        reward_records = result.scalars().all()

        return [UserRewardRecordInfo.model_validate(record) for record in reward_records] 