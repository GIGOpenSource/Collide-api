"""
任务模块异步API路由
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.task.async_service import TaskAsyncService
from app.domains.task.schemas import (
    TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateInfo, TaskRewardCreate, TaskRewardInfo,
    UserTaskRecordInfo, UserRewardRecordInfo, TaskProgressUpdate, TaskQuery
)


router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])


@router.post("/templates", response_model=SuccessResponse[TaskTemplateInfo], summary="创建任务模板")
async def create_task_template(
    req: TaskTemplateCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """创建任务模板"""
    try:
        service = TaskAsyncService(db)
        task_template = await service.create_task_template(req)
        return SuccessResponse.create(data=task_template, message="创建任务模板成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建任务模板失败")


@router.put("/templates/{template_id}", response_model=SuccessResponse[TaskTemplateInfo], summary="更新任务模板")
async def update_task_template(
    template_id: int,
    req: TaskTemplateUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """更新任务模板"""
    try:
        service = TaskAsyncService(db)
        task_template = await service.update_task_template(template_id, req)
        return SuccessResponse.create(data=task_template, message="更新任务模板成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新任务模板失败")


@router.delete("/templates/{template_id}", response_model=SuccessResponse[dict], summary="删除任务模板")
async def delete_task_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """删除任务模板"""
    try:
        service = TaskAsyncService(db)
        await service.delete_task_template(template_id)
        return SuccessResponse.create(data={}, message="删除任务模板成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除任务模板失败")


@router.get("/templates/{template_id}", response_model=SuccessResponse[TaskTemplateInfo], summary="获取任务模板详情")
async def get_task_template_by_id(
    template_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取任务模板详情"""
    try:
        service = TaskAsyncService(db)
        task_template = await service.get_task_template_by_id(template_id)
        return SuccessResponse.create(data=task_template, message="获取任务模板详情成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取任务模板详情失败")


@router.get("/templates", response_model=PaginationResponse[TaskTemplateInfo], summary="获取任务模板列表")
async def get_task_template_list(
    task_type: Optional[int] = Query(None, description="任务类型：1-daily, 2-weekly, 3-monthly, 4-achievement"),
    task_category: Optional[int] = Query(None, description="任务分类：1-login, 2-content, 3-social, 4-consume, 5-invite"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取任务模板列表"""
    try:
        service = TaskAsyncService(db)
        query = TaskQuery(
            task_type=task_type,
            task_category=task_category,
            is_active=is_active
        )
        result = await service.get_task_template_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取任务模板列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取任务模板列表失败")


@router.post("/rewards", response_model=SuccessResponse[TaskRewardInfo], summary="创建任务奖励")
async def create_task_reward(
    req: TaskRewardCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """创建任务奖励"""
    try:
        service = TaskAsyncService(db)
        task_reward = await service.create_task_reward(req)
        return SuccessResponse.create(data=task_reward, message="创建任务奖励成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建任务奖励失败")


@router.get("/rewards/{task_id}", response_model=SuccessResponse[List[TaskRewardInfo]], summary="获取任务奖励列表")
async def get_task_rewards(
    task_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取任务奖励列表"""
    try:
        service = TaskAsyncService(db)
        task_rewards = await service.get_task_rewards(task_id)
        return SuccessResponse.create(data=task_rewards, message="获取任务奖励列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取任务奖励列表失败")


@router.get("/user", response_model=SuccessResponse[List[UserTaskRecordInfo]], summary="获取用户任务列表")
async def get_user_tasks(
    task_date: Optional[date] = Query(None, description="任务日期"),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户任务列表"""
    try:
        service = TaskAsyncService(db)
        user_tasks = await service.get_user_tasks(current_user.user_id, task_date)
        return SuccessResponse.create(data=user_tasks, message="获取用户任务列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取用户任务列表失败")


@router.post("/progress", response_model=SuccessResponse[List[UserTaskRecordInfo]], summary="更新任务进度")
async def update_task_progress(
    req: TaskProgressUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """更新任务进度"""
    try:
        service = TaskAsyncService(db)
        updated_tasks = await service.update_task_progress(current_user.user_id, req)
        return SuccessResponse.create(data=updated_tasks, message="更新任务进度成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新任务进度失败")


@router.post("/claim/{task_record_id}", response_model=SuccessResponse[List[UserRewardRecordInfo]], summary="领取任务奖励")
async def claim_task_reward(
    task_record_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """领取任务奖励"""
    try:
        service = TaskAsyncService(db)
        reward_records = await service.claim_task_reward(current_user.user_id, task_record_id)
        return SuccessResponse.create(data=reward_records, message="领取任务奖励成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="领取任务奖励失败")


@router.get("/rewards", response_model=SuccessResponse[List[UserRewardRecordInfo]], summary="获取用户奖励记录")
async def get_user_reward_records(
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户奖励记录"""
    try:
        service = TaskAsyncService(db)
        reward_records = await service.get_user_reward_records(current_user.user_id)
        return SuccessResponse.create(data=reward_records, message="获取用户奖励记录成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取用户奖励记录失败") 