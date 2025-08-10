"""
评论模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.pagination import PaginationParams
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.exceptions import BusinessException
from app.domains.comment.async_service import CommentAsyncService
from app.domains.comment.schemas import CommentCreate, CommentUpdate, CommentInfo, CommentQuery, CommentTreeInfo


router = APIRouter(prefix="/api/v1/comments", tags=["评论"])


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


# @router.put("/{comment_id}", response_model=SuccessResponse[CommentInfo], summary="更新评论")
# async def update_comment(
#     comment_id: int,
#     data: CommentUpdate,
#     current_user: UserContext = Depends(get_current_user_context),
#     db: AsyncSession = Depends(get_async_db),
# ):
#     try:
#         service = CommentAsyncService(db)
#         info = await service.update_comment(comment_id, current_user.user_id, data)
#         return SuccessResponse.create(data=info, message="更新成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception:
#         raise HTTPException(status_code=500, detail="更新评论失败")


# @router.delete("/{comment_id}", response_model=SuccessResponse[bool], summary="删除评论")
# async def delete_comment(
#     comment_id: int,
#     current_user: UserContext = Depends(get_current_user_context),
#     db: AsyncSession = Depends(get_async_db),
# ):
#     try:
#         service = CommentAsyncService(db)
#         ok = await service.delete_comment(comment_id, current_user.user_id)
#         return SuccessResponse.create(data=ok, message="删除成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception:
#         raise HTTPException(status_code=500, detail="删除评论失败")


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
    # status: Optional[str] = Query(None, description="状态过滤：NORMAL、HIDDEN、DELETED"),
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
            # status=status,
        )
        result = await service.list_comments(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取评论列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取评论列表失败，请稍后重试"
        )


@router.get("/tree/{comment_type}/{target_id}", response_model=SuccessResponse[List[CommentTreeInfo]], summary="获取树状评论")
async def get_comment_tree(
    comment_type: str = Path(..., description="评论类型：CONTENT、DYNAMIC"),
    target_id: int = Path(..., description="目标对象ID"),
    max_level: int = Query(3, ge=1, le=5, description="最大层级深度"),
    max_replies_per_comment: int = Query(10, ge=1, le=50, description="每个评论最大回复数"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取树状评论结构"""
    try:
        service = CommentAsyncService(db)
        tree = await service.get_comment_tree(comment_type, target_id, max_level, max_replies_per_comment)
        return SuccessResponse.create(data=tree, message="获取树状评论成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取树状评论失败")


@router.get("/{comment_id}/replies", response_model=PaginationResponse[CommentInfo], summary="获取评论回复")
async def get_comment_replies(
    comment_id: int,
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取指定评论的回复列表"""
    try:
        service = CommentAsyncService(db)
        result = await service.get_comment_replies(comment_id, pagination)
        return PaginationResponse.from_pagination_result(result, "获取回复成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取回复失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取回复失败，请稍后重试"
        )


@router.get("/count/{comment_type}/{target_id}", response_model=SuccessResponse[int], summary="获取评论总数")
async def get_comment_count(
    comment_type: str = Path(..., description="评论类型：CONTENT、DYNAMIC"),
    target_id: int = Path(..., description="目标对象ID"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取指定目标的评论总数"""
    try:
        service = CommentAsyncService(db)
        count = await service.get_comment_count(comment_type, target_id)
        return SuccessResponse.create(data=count, message="获取评论总数成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取评论总数失败")

