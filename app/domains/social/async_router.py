"""
社交动态模块异步API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.pagination import PaginationParams
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.exceptions import BusinessException
from app.domains.social.async_service import SocialAsyncService
from app.domains.social.schemas import DynamicCreate, DynamicUpdate, DynamicInfo, DynamicQuery


router = APIRouter(prefix="/api/v1/social", tags=["社交动态"])


@router.post("/dynamics", response_model=SuccessResponse[DynamicInfo], summary="发布动态")
async def create_dynamic(
    data: DynamicCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        info = await service.create_dynamic(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            user_avatar=None,
            data=data,
        )
        return SuccessResponse.create(data=info, message="发布成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="发布动态失败")


@router.put("/dynamics/{dynamic_id}", response_model=SuccessResponse[DynamicInfo], summary="更新动态")
async def update_dynamic(
    dynamic_id: int,
    data: DynamicUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        info = await service.update_dynamic(dynamic_id, current_user.user_id, data)
        return SuccessResponse.create(data=info, message="更新成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="更新动态失败")


@router.delete("/dynamics/{dynamic_id}", response_model=SuccessResponse[bool], summary="删除动态")
async def delete_dynamic(
    dynamic_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        ok = await service.delete_dynamic(dynamic_id, current_user.user_id)
        return SuccessResponse.create(data=ok, message="删除成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="删除动态失败")


@router.get("/dynamics/{dynamic_id}", response_model=SuccessResponse[DynamicInfo], summary="获取动态详情")
async def get_dynamic(dynamic_id: int, db: AsyncSession = Depends(get_async_db)):
    try:
        service = SocialAsyncService(db)
        info = await service.get_dynamic_by_id(dynamic_id)
        return SuccessResponse.create(data=info, message="获取成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取动态失败")


@router.get("/dynamics", response_model=PaginationResponse[DynamicInfo], summary="获取动态列表")
async def list_dynamics(
    keyword: Optional[str] = Query(None, description="关键词（内容模糊搜索）"),
    dynamic_type: Optional[str] = Query(None, description="动态类型：text、image、video、share"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤：normal、hidden、deleted"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        query = DynamicQuery(keyword=keyword, dynamic_type=dynamic_type, user_id=user_id, status=status)
        result = await service.list_dynamics(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取动态列表失败")

