"""
关注模块异步API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.follow.async_service import FollowAsyncService
from app.domains.follow.schemas import FollowToggleRequest, FollowInfo, FollowQuery


router = APIRouter(prefix="/api/v1/follows", tags=["关注管理"])


@router.post("/toggle", response_model=SuccessResponse[dict], summary="关注/取消关注切换")
async def toggle_follow(
    req: FollowToggleRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """关注/取消关注切换"""
    try:
        service = FollowAsyncService(db)
        is_following, follow_info = await service.toggle_follow(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            user_avatar=None,
            req=req,
        )
        return SuccessResponse.create(
            data={"isFollowing": is_following, "follow": follow_info.model_dump()},
            message="操作成功"
        )
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="关注操作失败")


@router.get("/list", response_model=PaginationResponse[FollowInfo], summary="获取关注列表")
async def get_follow_list(
    follow_type: Optional[str] = Query(None, description="关注类型：following-我关注的、followers-关注我的"),
    status: Optional[str] = Query(None, description="状态：active、cancelled"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取关注列表"""
    try:
        service = FollowAsyncService(db)
        query = FollowQuery(
            user_id=current_user.user_id,
            follow_type=follow_type,
            status=status
        )
        result = await service.get_follow_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取关注列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取关注列表失败")


@router.get("/check/{followee_id}", response_model=SuccessResponse[dict], summary="检查关注状态")
async def check_follow_status(
    followee_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """检查是否关注了指定用户"""
    try:
        service = FollowAsyncService(db)
        is_following = await service.check_follow_status(current_user.user_id, followee_id)
        return SuccessResponse.create(
            data={"isFollowing": is_following},
            message="查询成功"
        )
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="查询关注状态失败") 