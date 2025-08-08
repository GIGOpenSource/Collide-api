"""
任务模块异步服务层
"""
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.task.models import TaskTemplate, TaskReward, UserTaskRecord, UserRewardRecord
from app.domains.task.schemas import (
    TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateInfo, TaskRewardCreate, TaskRewardInfo,
    UserTaskRecordInfo, UserRewardRecordInfo, TaskProgressUpdate, TaskQuery
)
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class TaskAsyncService:
    """任务异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task_template(self, req: TaskTemplateCreate) -> TaskTemplateInfo:
        """创建任务模板"""
        task_template = TaskTemplate(
            task_name=req.task_name,
            task_desc=req.task_desc,
            task_type=req.task_type,
            task_category=req.task_category,
            task_action=req.task_action,
            target_count=req.target_count,
            sort_order=req.sort_order,
            is_active=req.is_active,
            start_date=req.start_date,
            end_date=req.end_date
        )
        self.db.add(task_template)
        await self.db.commit()
        await self.db.refresh(task_template)
        return TaskTemplateInfo.model_validate(task_template)

    async def update_task_template(self, template_id: int, req: TaskTemplateUpdate) -> TaskTemplateInfo:
        """更新任务模板"""
        task_template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalar_one_or_none()
        if not task_template:
            raise BusinessException("任务模板不存在")

        # 更新字段
        update_data = {}
        if req.task_name is not None:
            update_data["task_name"] = req.task_name
        if req.task_desc is not None:
            update_data["task_desc"] = req.task_desc
        if req.task_type is not None:
            update_data["task_type"] = req.task_type
        if req.task_category is not None:
            update_data["task_category"] = req.task_category
        if req.task_action is not None:
            update_data["task_action"] = req.task_action
        if req.target_count is not None:
            update_data["target_count"] = req.target_count
        if req.sort_order is not None:
            update_data["sort_order"] = req.sort_order
        if req.is_active is not None:
            update_data["is_active"] = req.is_active
        if req.start_date is not None:
            update_data["start_date"] = req.start_date
        if req.end_date is not None:
            update_data["end_date"] = req.end_date

        await self.db.execute(update(TaskTemplate).where(TaskTemplate.id == template_id).values(**update_data))
        await self.db.commit()

        # 刷新数据
        task_template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalar_one()
        return TaskTemplateInfo.model_validate(task_template)

    async def delete_task_template(self, template_id: int):
        """删除任务模板"""
        task_template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalar_one_or_none()
        if not task_template:
            raise BusinessException("任务模板不存在")

        await self.db.execute(delete(TaskTemplate).where(TaskTemplate.id == template_id))
        await self.db.commit()

    async def get_task_template_by_id(self, template_id: int) -> TaskTemplateInfo:
        """根据ID获取任务模板"""
        task_template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))).scalar_one_or_none()
        if not task_template:
            raise BusinessException("任务模板不存在")
        return TaskTemplateInfo.model_validate(task_template)

    async def get_task_template_list(self, query: TaskQuery, pagination: PaginationParams) -> PaginationResult[TaskTemplateInfo]:
        """获取任务模板列表"""
        conditions = []

        if query.task_type:
            conditions.append(TaskTemplate.task_type == query.task_type)
        if query.task_category:
            conditions.append(TaskTemplate.task_category == query.task_category)
        if query.is_active is not None:
            conditions.append(TaskTemplate.is_active == query.is_active)

        stmt = select(TaskTemplate).where(and_(*conditions)).order_by(TaskTemplate.sort_order.asc(), TaskTemplate.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        task_templates = result.scalars().all()

        task_template_list = [TaskTemplateInfo.model_validate(task_template) for task_template in task_templates]

        return PaginationResult.create(
            items=task_template_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def create_task_reward(self, req: TaskRewardCreate) -> TaskRewardInfo:
        """创建任务奖励"""
        # 检查任务模板是否存在
        task_template = (await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == req.task_id))).scalar_one_or_none()
        if not task_template:
            raise BusinessException("任务模板不存在")

        task_reward = TaskReward(
            task_id=req.task_id,
            reward_type=req.reward_type,
            reward_name=req.reward_name,
            reward_desc=req.reward_desc,
            reward_amount=req.reward_amount,
            reward_data=req.reward_data,
            is_main_reward=req.is_main_reward
        )
        self.db.add(task_reward)
        await self.db.commit()
        await self.db.refresh(task_reward)
        return TaskRewardInfo.model_validate(task_reward)

    async def get_task_rewards(self, task_id: int) -> List[TaskRewardInfo]:
        """获取任务奖励列表"""
        stmt = select(TaskReward).where(TaskReward.task_id == task_id).order_by(TaskReward.is_main_reward.desc(), TaskReward.create_time.asc())
        result = await self.db.execute(stmt)
        task_rewards = result.scalars().all()

        return [TaskRewardInfo.model_validate(task_reward) for task_reward in task_rewards]

    async def get_user_tasks(self, user_id: int, task_date: Optional[date] = None) -> List[UserTaskRecordInfo]:
        """获取用户任务列表"""
        if task_date is None:
            task_date = date.today()

        # 获取活跃的任务模板
        active_templates = (await self.db.execute(
            select(TaskTemplate).where(TaskTemplate.is_active == True)
        )).scalars().all()

        user_tasks = []
        for template in active_templates:
            # 查找或创建用户任务记录
            user_task = (await self.db.execute(
                select(UserTaskRecord).where(and_(
                    UserTaskRecord.user_id == user_id,
                    UserTaskRecord.task_id == template.id,
                    UserTaskRecord.task_date == task_date
                ))
            )).scalar_one_or_none()

            if not user_task:
                # 创建新的用户任务记录
                user_task = UserTaskRecord(
                    user_id=user_id,
                    task_id=template.id,
                    task_date=task_date,
                    task_name=template.task_name,
                    task_type=template.task_type,
                    task_category=template.task_category,
                    target_count=template.target_count
                )
                self.db.add(user_task)
                await self.db.commit()
                await self.db.refresh(user_task)

            user_tasks.append(UserTaskRecordInfo.model_validate(user_task))

        return user_tasks

    async def update_task_progress(self, user_id: int, req: TaskProgressUpdate) -> List[UserTaskRecordInfo]:
        """更新任务进度"""
        task_date = date.today()
        
        # 查找匹配任务动作的用户任务记录
        user_tasks = (await self.db.execute(
            select(UserTaskRecord).join(TaskTemplate).where(and_(
                UserTaskRecord.user_id == user_id,
                UserTaskRecord.task_date == task_date,
                TaskTemplate.task_action == req.task_action,
                TaskTemplate.is_active == True
            ))
        )).scalars().all()

        updated_tasks = []
        for user_task in user_tasks:
            # 更新进度
            new_count = user_task.current_count + req.count
            is_completed = new_count >= user_task.target_count

            update_data = {
                "current_count": new_count,
                "is_completed": is_completed
            }

            if is_completed and not user_task.is_completed:
                update_data["complete_time"] = datetime.now()

            await self.db.execute(
                update(UserTaskRecord).where(UserTaskRecord.id == user_task.id).values(**update_data)
            )

            # 刷新数据
            user_task = (await self.db.execute(select(UserTaskRecord).where(UserTaskRecord.id == user_task.id))).scalar_one()
            updated_tasks.append(UserTaskRecordInfo.model_validate(user_task))

        await self.db.commit()
        return updated_tasks

    async def claim_task_reward(self, user_id: int, task_record_id: int) -> List[UserRewardRecordInfo]:
        """领取任务奖励"""
        # 检查任务记录
        user_task = (await self.db.execute(
            select(UserTaskRecord).where(and_(
                UserTaskRecord.id == task_record_id,
                UserTaskRecord.user_id == user_id
            ))
        )).scalar_one_or_none()

        if not user_task:
            raise BusinessException("任务记录不存在")

        if not user_task.is_completed:
            raise BusinessException("任务尚未完成")

        if user_task.is_rewarded:
            raise BusinessException("奖励已领取")

        # 获取任务奖励
        task_rewards = await self.get_task_rewards(user_task.task_id)
        if not task_rewards:
            raise BusinessException("任务无奖励配置")

        # 创建奖励记录
        reward_records = []
        for task_reward in task_rewards:
            reward_record = UserRewardRecord(
                user_id=user_id,
                task_record_id=task_record_id,
                reward_source=1,  # task
                reward_type=task_reward.reward_type,
                reward_name=task_reward.reward_name,
                reward_amount=task_reward.reward_amount,
                reward_data=task_reward.reward_data,
                status=2,  # success
                grant_time=datetime.now()
            )
            self.db.add(reward_record)
            reward_records.append(reward_record)

        # 更新任务记录状态
        await self.db.execute(
            update(UserTaskRecord).where(UserTaskRecord.id == task_record_id).values(
                is_rewarded=True,
                reward_time=datetime.now()
            )
        )

        await self.db.commit()

        # 刷新奖励记录
        for reward_record in reward_records:
            await self.db.refresh(reward_record)

        return [UserRewardRecordInfo.model_validate(record) for record in reward_records]

    async def get_user_reward_records(self, user_id: int) -> List[UserRewardRecordInfo]:
        """获取用户奖励记录"""
        stmt = select(UserRewardRecord).where(UserRewardRecord.user_id == user_id).order_by(UserRewardRecord.create_time.desc())
        result = await self.db.execute(stmt)
        reward_records = result.scalars().all()

        return [UserRewardRecordInfo.model_validate(record) for record in reward_records] 