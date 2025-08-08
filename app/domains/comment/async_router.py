"""
评论模块异步API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.pagination import PaginationParams
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.exceptions import BusinessException
from app.domains.comment.async_service import CommentAsyncService
from app.domains.comment.schemas import CommentCreate, CommentUpdate, CommentInfo, CommentQuery


router = APIRouter(prefix="/api/v1/comments", tags=["评论管理"])


@router.post("/", response_model=SuccessResponse[CommentInfo], summary="创建评论")
async def create_comment(
    data: CommentCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = CommentAsyncService(db)
        info = await service.create_comment(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            user_avatar=None,
            data=data,
        )
        return SuccessResponse.create(data=info, message="创建成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="创建评论失败")


@router.put("/{comment_id}", response_model=SuccessResponse[CommentInfo], summary="更新评论")
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = CommentAsyncService(db)
        info = await service.update_comment(comment_id, current_user.user_id, data)
        return SuccessResponse.create(data=info, message="更新成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="更新评论失败")


@router.delete("/{comment_id}", response_model=SuccessResponse[bool], summary="删除评论")
async def delete_comment(
    comment_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = CommentAsyncService(db)
        ok = await service.delete_comment(comment_id, current_user.user_id)
        return SuccessResponse.create(data=ok, message="删除成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="删除评论失败")


@router.get("/{comment_id}", response_model=SuccessResponse[CommentInfo], summary="评论详情")
async def get_comment(comment_id: int, db: AsyncSession = Depends(get_async_db)):
    try:
        service = CommentAsyncService(db)
        info = await service.get_comment_by_id(comment_id)
        return SuccessResponse.create(data=info, message="获取成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取评论失败")


@router.get("/", response_model=PaginationResponse[CommentInfo], summary="评论列表")
async def list_comments(
    comment_type: Optional[str] = Query(None, description="评论类型过滤：CONTENT、DYNAMIC"),
    target_id: Optional[int] = Query(None, description="目标对象ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    parent_comment_id: Optional[int] = Query(None, description="父评论ID"),
    status: Optional[str] = Query(None, description="状态过滤：NORMAL、HIDDEN、DELETED"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = CommentAsyncService(db)
        query = CommentQuery(
            comment_type=comment_type,
            target_id=target_id,
            user_id=user_id,
            parent_comment_id=parent_comment_id,
            status=status,
        )
        result = await service.list_comments(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取评论列表失败")

