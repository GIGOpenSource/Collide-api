"""
搜索模块异步API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.search.async_service import SearchAsyncService
from app.domains.search.schemas import SearchRequest, SearchHistoryInfo, HotSearchInfo, SearchResult


router = APIRouter(prefix="/api/v1/search", tags=["搜索管理"])


@router.post("/", response_model=SuccessResponse[SearchResult], summary="执行搜索")
async def search(
    req: SearchRequest,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: Optional[UserContext] = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """执行搜索"""
    try:
        service = SearchAsyncService(db)
        user_id = current_user.user_id if current_user else None
        result = await service.search(req, user_id, pagination)
        return SuccessResponse.create(data=result, message="搜索完成")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索失败")


@router.get("/history", response_model=SuccessResponse[list[SearchHistoryInfo]], summary="获取搜索历史")
async def get_search_history(
    search_type: Optional[str] = Query(None, description="搜索类型：content、goods、user"),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取搜索历史"""
    try:
        service = SearchAsyncService(db)
        histories = await service.get_search_history(current_user.user_id, search_type)
        return SuccessResponse.create(data=histories, message="获取搜索历史成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取搜索历史失败")


@router.get("/hot", response_model=SuccessResponse[list[HotSearchInfo]], summary="获取热门搜索")
async def get_hot_searches(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取热门搜索"""
    try:
        service = SearchAsyncService(db)
        hot_searches = await service.get_hot_searches(limit)
        return SuccessResponse.create(data=hot_searches, message="获取热门搜索成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取热门搜索失败") 