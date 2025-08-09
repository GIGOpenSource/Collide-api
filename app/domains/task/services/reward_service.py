from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.task.models import TaskTemplate, TaskReward
from app.domains.task.schemas import TaskRewardCreate, TaskRewardInfo


class TaskRewardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, req: TaskRewardCreate) -> TaskRewardInfo:
        template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == req.task_id))).scalar_one_or_none()
        if not template:
            raise BusinessException("任务模板不存在")
        reward = TaskReward(**req.model_dump())
        self.db.add(reward)
        await self.db.commit()
        await self.db.refresh(reward)
        return TaskRewardInfo.model_validate(reward)

    async def list(self, task_id: int) -> list[TaskRewardInfo]:
        rows = await self.db.execute(select(TaskReward).where(TaskReward.task_id == task_id).order_by(TaskReward.is_main_reward.desc(), TaskReward.create_time.asc()))
        rewards = rows.scalars().all()
        return [TaskRewardInfo.model_validate(r) for r in rewards]

