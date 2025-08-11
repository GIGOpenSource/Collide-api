"""
标签模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.tag.async_service import TagAsyncService
from app.domains.tag.schemas import (
    TagCreate, TagUpdate, TagInfo, UserInterestTagCreate, UserInterestTagInfo,
    ContentTagCreate, TagQuery
)


router = APIRouter(prefix="/api/v1/tags", tags=["标签管理"])


# ==================== 管理员接口（已注释） ====================

@router.post("/", response_model=SuccessResponse[TagInfo], summary="创建标签")
async def create_tag(
    req: TagCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """创建标签"""
    try:
        service = TagAsyncService(db)
        tag = await service.create_tag(req)
        return SuccessResponse.create(data=tag, message="创建标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建标签失败")


# @router.put("/{tag_id}", response_model=SuccessResponse[TagInfo], summary="更新标签")
# async def update_tag(
#     tag_id: int,
#     req: TagUpdate,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     """更新标签"""
#     try:
#         service = TagAsyncService(db)
#         tag = await service.update_tag(tag_id, req)
#         return SuccessResponse.create(data=tag, message="更新标签成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="更新标签失败")


# @router.delete("/{tag_id}", response_model=SuccessResponse[dict], summary="删除标签")
# async def delete_tag(
#     tag_id: int,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     """删除标签"""
#     try:
#         service = TagAsyncService(db)
#         await service.delete_tag(tag_id)
#         return SuccessResponse.create(data={}, message="删除标签成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="删除标签失败")


# @router.get("/{tag_id}", response_model=SuccessResponse[TagInfo], summary="获取标签详情")
# async def get_tag_by_id(
#     tag_id: int,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     """获取标签详情"""
#     try:
#         service = TagAsyncService(db)
#         tag = await service.get_tag_by_id(tag_id)
#         return SuccessResponse.create(data=tag, message="获取标签详情成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="获取标签详情失败")


@router.get("/", response_model=PaginationResponse[TagInfo], summary="获取标签列表")
async def get_tag_list(
    tag_type: Optional[str] = Query(None, description="标签类型：content、interest、system"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    status: Optional[str] = Query(None, description="状态：active、inactive"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取标签列表"""
    try:
        service = TagAsyncService(db)
        query = TagQuery(
            tag_type=tag_type,
            category_id=category_id,
            status=status,
            keyword=keyword
        )
        result = await service.get_tag_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取标签列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签列表失败")


# ==================== 用户标签接口 ====================

@router.get("/hot", response_model=SuccessResponse[List[TagInfo]], summary="获取热门标签列表")
async def get_hot_tags(
    tag_type: Optional[str] = Query(None, description="标签类型：content、interest、system"),
    limit: int = Query(20, ge=1, le=100, description="返回数量，默认20个"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取热门标签列表
    
    - **tag_type**: 标签类型筛选
    - **limit**: 返回数量限制
    """
    try:
        service = TagAsyncService(db)
        hot_tags = await service.get_hot_tags(tag_type, limit)
        return SuccessResponse.create(data=hot_tags, message="获取热门标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取热门标签失败")


@router.get("/search", response_model=SuccessResponse[List[TagInfo]], summary="根据标签名称搜索标签")
async def search_tags_by_name(
    name: str = Query(..., min_length=1, description="标签名称（支持模糊搜索）"),
    tag_type: Optional[str] = Query(None, description="标签类型：content、interest、system"),
    limit: int = Query(20, ge=1, le=100, description="返回数量，默认20个"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    根据标签名称搜索标签
    
    - **name**: 标签名称（支持模糊搜索）
    - **tag_type**: 标签类型筛选
    - **limit**: 返回数量限制
    """
    try:
        service = TagAsyncService(db)
        tags = await service.search_tags_by_name(name, tag_type, limit)
        return SuccessResponse.create(data=tags, message="搜索标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索标签失败")


@router.post("/create-by-name", response_model=SuccessResponse[TagInfo], summary="根据标签名称创建标签")
async def create_tag_by_name(
    name: str = Query(..., min_length=1, max_length=50, description="标签名称"),
    tag_type: str = Query("content", description="标签类型：content、interest、system"),
    description: Optional[str] = Query(None, description="标签描述"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    根据标签名称创建标签
    
    - **name**: 标签名称
    - **tag_type**: 标签类型
    - **description**: 标签描述（可选）
    - **category_id**: 分类ID（可选）
    """
    try:
        service = TagAsyncService(db)
        tag = await service.create_tag_by_name(name, tag_type, description, category_id)
        return SuccessResponse.create(data=tag, message="创建标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建标签失败")


@router.post("/user-interest", response_model=SuccessResponse[UserInterestTagInfo], summary="添加用户兴趣标签")
async def add_user_interest_tag(
    req: UserInterestTagCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    添加用户兴趣标签
    
    - **tag_id**: 标签ID（与tag_name二选一）
    - **tag_name**: 标签名称（与tag_id二选一，不存在则自动创建）
    - **interest_score**: 兴趣分数（0-100）
    """
    try:
        service = TagAsyncService(db)
        interest_tag = await service.add_user_interest_tag(current_user.user_id, req)
        return SuccessResponse.create(data=interest_tag, message="添加兴趣标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="添加兴趣标签失败")


@router.get("/user-interest", response_model=SuccessResponse[List[UserInterestTagInfo]], summary="获取用户兴趣标签")
async def get_user_interest_tags(
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户兴趣标签"""
    try:
        service = TagAsyncService(db)
        interest_tags = await service.get_user_interest_tags(current_user.user_id)
        return SuccessResponse.create(data=interest_tags, message="获取兴趣标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取兴趣标签失败")


@router.post("/content", response_model=SuccessResponse[dict], summary="为内容添加标签")
async def add_content_tags(
    req: ContentTagCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    为内容添加标签
    
    - **content_id**: 内容ID
    - **tag_ids**: 标签ID列表（与tag_names二选一）
    - **tag_names**: 标签名称列表（与tag_ids二选一，不存在则自动创建）
    """
    try:
        service = TagAsyncService(db)
        await service.add_content_tags(req)
        return SuccessResponse.create(data={}, message="添加内容标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="添加内容标签失败")


@router.get("/content/{content_id}", response_model=SuccessResponse[List[TagInfo]], summary="获取内容标签")
async def get_content_tags(
    content_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取内容标签"""
    try:
        service = TagAsyncService(db)
        tags = await service.get_content_tags(content_id)
        return SuccessResponse.create(data=tags, message="获取内容标签成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取内容标签失败") 