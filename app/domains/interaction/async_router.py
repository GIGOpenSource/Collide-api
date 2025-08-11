"""
互动模块异步API路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.interaction.async_service import InteractionAsyncService
from app.domains.interaction.schemas import InteractionQuery, InteractionInfo, InteractionUserInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/interactions", tags=["互动管理"])


@router.get("/", response_model=PaginationResponse[InteractionInfo], summary="获取互动列表")
async def get_interactions(
    interaction_type: Optional[str] = Query(None, description="互动类型：COMMENT、LIKE、FOLLOW"),
    target_id: Optional[int] = Query(None, description="目标对象ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    status: Optional[str] = Query(None, description="状态：active、cancelled"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取互动列表，支持多种查询条件"""
    try:
        query = InteractionQuery(
            interaction_type=interaction_type,
            target_id=target_id,
            user_id=user_id,
            status=status
        )
        service = InteractionAsyncService(db)
        result = await service.get_interactions(query, pagination)
        return PaginationResponse.from_pagination_result(result, message="获取成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取互动列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取互动列表失败，请稍后重试"
        )


@router.get("/me", response_model=PaginationResponse[InteractionInfo], summary="获取我的互动记录")
async def get_my_interactions(
    interaction_type: Optional[str] = Query(None, description="互动类型：COMMENT、LIKE、FOLLOW"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取当前登录用户的互动记录"""
    try:
        service = InteractionAsyncService(db)
        result = await service.get_user_interactions(
            user_id=current_user.user_id,
            interaction_type=interaction_type,
            pagination=pagination
        )
        return PaginationResponse.from_pagination_result(result, message="获取成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取我的互动记录失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取我的互动记录失败，请稍后重试"
        )


@router.get("/{interaction_type}/{target_id}/users", response_model=PaginationResponse[InteractionUserInfo], summary="获取互动用户列表")
async def get_interaction_users_by_target(
    interaction_type: str = Path(..., description="互动类型: COMMENT, LIKE, FOLLOW"),
    target_id: int = Path(..., description="目标对象ID"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取对指定目标进行互动的用户列表"""
    try:
        service = InteractionAsyncService(db)
        result = await service.get_interactions_by_target(interaction_type, target_id, pagination)
        return PaginationResponse.from_pagination_result(result, message="获取成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取互动用户列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取互动用户列表失败，请稍后重试"
        ) 