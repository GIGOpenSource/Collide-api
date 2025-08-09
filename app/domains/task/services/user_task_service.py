from datetime import date, datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.task.models import TaskTemplate, UserTaskRecord, UserRewardRecord
from app.domains.task.schemas import TaskProgressUpdate, UserTaskRecordInfo, UserRewardRecordInfo


class UserTaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_tasks(self, user_id: int, task_date: date | None = None) -> list[UserTaskRecordInfo]:
        if task_date is None:
            task_date = date.today()
        active_templates = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.is_active == True))).scalars().all()
        user_tasks: list[UserTaskRecordInfo] = []
        for template in active_templates:
            user_task = (await self.db.execute(select(UserTaskRecord).where(and_(UserTaskRecord.user_id == user_id, UserTaskRecord.task_id == template.id, UserTaskRecord.task_date == task_date)))).scalar_one_or_none()
            if not user_task:
                user_task = UserTaskRecord(user_id=user_id, task_id=template.id, task_date=task_date, task_name=template.task_name, task_type=template.task_type, task_category=template.task_category, target_count=template.target_count)
                self.db.add(user_task)
                await self.db.commit()
                await self.db.refresh(user_task)
            user_tasks.append(UserTaskRecordInfo.model_validate(user_task))
        return user_tasks

    async def update_task_progress(self, user_id: int, req: TaskProgressUpdate) -> list[UserTaskRecordInfo]:
        today = date.today()
        rows = await self.db.execute(select(UserTaskRecord).join(TaskTemplate).where(and_(UserTaskRecord.user_id == user_id, UserTaskRecord.task_date == today, TaskTemplate.task_action == req.task_action, TaskTemplate.is_active == True)))
        user_tasks = rows.scalars().all()
        updated: list[UserTaskRecordInfo] = []
        for ut in user_tasks:
            new_count = ut.current_count + req.count
            is_completed = new_count >= ut.target_count
            update_data = {"current_count": new_count, "is_completed": is_completed}
            if is_completed and not ut.is_completed:
                update_data["complete_time"] = datetime.now()
            await self.db.execute(update(UserTaskRecord).where(UserTaskRecord.id == ut.id).values(**update_data))
            ut = (await self.db.execute(select(UserTaskRecord).where(UserTaskRecord.id == ut.id))).scalar_one()
            updated.append(UserTaskRecordInfo.model_validate(ut))
        await self.db.commit()
        return updated

    async def claim_task_reward(self, user_id: int, task_record_id: int) -> list[UserRewardRecordInfo]:
        user_task = (await self.db.execute(select(UserTaskRecord).where(and_(UserTaskRecord.id == task_record_id, UserTaskRecord.user_id == user_id)))).scalar_one_or_none()
        if not user_task:
            raise BusinessException("任务记录不存在")
        if not user_task.is_completed:
            raise BusinessException("任务尚未完成")
        if user_task.is_rewarded:
            raise BusinessException("奖励已领取")
        from app.domains.task.services.reward_service import TaskRewardService
        rewards = await TaskRewardService(self.db).list(user_task.task_id)
        if not rewards:
            raise BusinessException("任务无奖励配置")
        created: list[UserRewardRecord] = []
        for r in rewards:
            rr = UserRewardRecord(user_id=user_id, task_record_id=task_record_id, reward_source=1, reward_type=r.reward_type, reward_name=r.reward_name, reward_amount=r.reward_amount, reward_data=r.reward_data, status=2, grant_time=datetime.now())
            self.db.add(rr)
            created.append(rr)
        await self.db.execute(update(UserTaskRecord).where(UserTaskRecord.id == task_record_id).values(is_rewarded=True, reward_time=datetime.now()))
        await self.db.commit()
        for rr in created:
            await self.db.refresh(rr)
        return [UserRewardRecordInfo.model_validate(x) for x in created]

