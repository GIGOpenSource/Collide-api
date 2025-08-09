"""
点赞模块异步API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.like.async_service import LikeAsyncService
from app.domains.like.schemas import LikeToggleRequest, LikeInfo, LikeQuery, LikeUserInfo


router = APIRouter(prefix="/api/v1/likes", tags=["点赞管理"])


@router.post("/toggle", response_model=SuccessResponse[dict], summary="点赞/取消点赞切换")
async def toggle_like(
    req: LikeToggleRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = LikeAsyncService(db)
        is_liked, like_info = await service.toggle_like(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            user_avatar=None,
            req=req,
        )
        return SuccessResponse.create(data={"isLiked": is_liked, "like": like_info.model_dump()}, message="操作成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="点赞操作失败")


@router.get("/me", response_model=PaginationResponse[LikeInfo], summary="获取我的点赞列表")
async def get_my_likes(
    query: LikeQuery = Depends(),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取当前登录用户的点赞列表，只返回active状态的记录"""
    try:
        service = LikeAsyncService(db)
        result = await service.get_my_likes(current_user.user_id, query, pagination)
        return PaginationResponse.from_pagination_result(result, message="获取成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取我的点赞列表失败")


@router.get("/{like_type}/{target_id}/users", response_model=PaginationResponse[LikeUserInfo], summary="获取点赞用户列表")
async def get_likers_by_target(
    like_type: str = Path(..., description="点赞类型: CONTENT, COMMENT, DYNAMIC"),
    target_id: int = Path(..., description="目标对象ID"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取点赞了指定对象的用户列表"""
    try:
        service = LikeAsyncService(db)
        result = await service.get_likers_by_target(like_type, target_id, pagination)
        return PaginationResponse.from_pagination_result(result, message="获取成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取点赞用户列表失败")

