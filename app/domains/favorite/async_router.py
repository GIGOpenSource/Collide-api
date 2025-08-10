"""
收藏模块异步API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.favorite.async_service import FavoriteAsyncService
from app.domains.favorite.schemas import FavoriteToggleRequest, FavoriteInfo, FavoriteQuery


router = APIRouter(prefix="/api/v1/favorites", tags=["收藏管理"])


@router.post("/toggle", response_model=SuccessResponse[dict], summary="收藏/取消收藏切换")
async def toggle_favorite(
    req: FavoriteToggleRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """收藏/取消收藏切换"""
    try:
        service = FavoriteAsyncService(db)
        is_favorited, favorite_info = await service.toggle_favorite(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            req=req,
        )
        return SuccessResponse.create(
            data={"isFavorited": is_favorited, "favorite": favorite_info.model_dump()},
            message="操作成功"
        )
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="收藏操作失败")


@router.get("/list", response_model=PaginationResponse[FavoriteInfo], summary="获取收藏列表")
async def get_favorite_list(
    favorite_type: Optional[str] = Query(None, description="收藏类型：CONTENT、GOODS"),
    status: Optional[str] = Query(None, description="状态：active、cancelled"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取收藏列表"""
    try:
        service = FavoriteAsyncService(db)
        query = FavoriteQuery(
            user_id=current_user.user_id,
            favorite_type=favorite_type,
            status=status
        )
        result = await service.get_favorite_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取收藏列表成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取收藏列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取收藏列表失败，请稍后重试"
        )


@router.get("/check/{favorite_type}/{target_id}", response_model=SuccessResponse[dict], summary="检查收藏状态")
async def check_favorite_status(
    favorite_type: str,
    target_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """检查是否收藏了指定对象"""
    try:
        service = FavoriteAsyncService(db)
        is_favorited = await service.check_favorite_status(current_user.user_id, favorite_type, target_id)
        return SuccessResponse.create(
            data={"isFavorited": is_favorited},
            message="查询成功"
        )
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="查询收藏状态失败") 