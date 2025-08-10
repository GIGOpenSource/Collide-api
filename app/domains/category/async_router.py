"""
分类模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.pagination import PaginationParams
from app.common.dependencies import get_pagination
from app.common.exceptions import BusinessException
from app.domains.category.async_service import CategoryAsyncService
from app.domains.category.schemas import CategoryInfo, CategoryQuery, CategoryTreeNode


router = APIRouter(prefix="/api/v1/categories", tags=["分类查询"])


# @router.post("/", response_model=SuccessResponse[CategoryInfo], summary="创建分类", description="创建新的分类，名称在同级下唯一")
# async def create_category(
#     data: CategoryCreate,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     try:
#         service = CategoryAsyncService(db)
#         info = await service.create_category(data)
#         return SuccessResponse.create(data=info, message="创建成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception:
#         raise HTTPException(status_code=500, detail="创建分类失败")


# @router.put("/{category_id}", response_model=SuccessResponse[CategoryInfo], summary="更新分类", description="更新分类基础信息")
# async def update_category(
#     category_id: int,
#     data: CategoryUpdate,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     try:
#         service = CategoryAsyncService(db)
#         info = await service.update_category(category_id, data)
#         return SuccessResponse.create(data=info, message="更新成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception:
#         raise HTTPException(status_code=500, detail="更新分类失败")


# @router.delete("/{category_id}", response_model=SuccessResponse[bool], summary="删除分类", description="删除指定分类")
# async def delete_category(
#     category_id: int,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     try:
#         service = CategoryAsyncService(db)
#         ok = await service.delete_category(category_id)
#         return SuccessResponse.create(data=ok, message="删除成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception:
#         raise HTTPException(status_code=500, detail="删除分类失败")


@router.get("/{category_id}", response_model=SuccessResponse[CategoryInfo], summary="获取分类详情")
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = CategoryAsyncService(db)
        info = await service.get_category_by_id(category_id)
        return SuccessResponse.create(data=info, message="获取成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取分类失败")


@router.get("/", response_model=PaginationResponse[CategoryInfo], summary="获取分类列表", description="支持关键词/父级/状态筛选，返回分页结果")
async def list_categories(
    keyword: Optional[str] = Query(None, description="关键词（名称模糊匹配）"),
    parent_id: Optional[int] = Query(None, ge=0, description="父分类ID过滤"),
    # status: Optional[str] = Query(None, description="状态过滤：active/inactive"), # 移除，强制active
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        query = CategoryQuery(keyword=keyword, parent_id=parent_id)
        service = CategoryAsyncService(db)
        result = await service.get_category_list(query, pagination)
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
        logger.error(f"获取分类列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取分类列表失败，请稍后重试"
        )


@router.get("/tree", response_model=SuccessResponse[List[CategoryTreeNode]], summary="获取分类树", description="获取所有活跃分类的层级结构")
async def get_category_tree(db: AsyncSession = Depends(get_async_db)):
    try:
        service = CategoryAsyncService(db)
        tree = await service.get_category_tree()
        return SuccessResponse.create(data=tree, message="获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取分类树失败")


@router.get("/{category_id}/root", response_model=SuccessResponse[List[CategoryInfo]], summary="获取分类祖先（面包屑）")
async def get_category_ancestors(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        service = CategoryAsyncService(db)
        ancestors = await service.get_category_ancestors(category_id)
        return SuccessResponse.create(data=ancestors, message="获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取分类祖先失败")

