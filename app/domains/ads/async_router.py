"""
广告模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.ads.async_service import AdAsyncService
from app.domains.ads.schemas import AdCreate, AdUpdate, AdInfo, AdQuery


router = APIRouter(prefix="/api/v1/ads", tags=["广告管理"])


@router.post("/", response_model=SuccessResponse[AdInfo], summary="创建广告")
async def create_ad(
    req: AdCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """创建广告"""
    try:
        service = AdAsyncService(db)
        ad = await service.create_ad(req)
        return SuccessResponse.create(data=ad, message="创建广告成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建广告失败")


@router.put("/{ad_id}", response_model=SuccessResponse[AdInfo], summary="更新广告")
async def update_ad(
    ad_id: int,
    req: AdUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """更新广告"""
    try:
        service = AdAsyncService(db)
        ad = await service.update_ad(ad_id, req)
        return SuccessResponse.create(data=ad, message="更新广告成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新广告失败")


@router.delete("/{ad_id}", response_model=SuccessResponse[dict], summary="删除广告")
async def delete_ad(
    ad_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """删除广告"""
    try:
        service = AdAsyncService(db)
        await service.delete_ad(ad_id)
        return SuccessResponse.create(data={}, message="删除广告成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除广告失败")


@router.get("/{ad_id}", response_model=SuccessResponse[AdInfo], summary="获取广告详情")
async def get_ad_by_id(
    ad_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取广告详情"""
    try:
        service = AdAsyncService(db)
        ad = await service.get_ad_by_id(ad_id)
        return SuccessResponse.create(data=ad, message="获取广告详情成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取广告详情失败")


@router.get("/", response_model=PaginationResponse[AdInfo], summary="获取广告列表")
async def get_ad_list(
    ad_type: Optional[str] = Query(None, description="广告类型：banner、sidebar、popup、feed"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取广告列表"""
    try:
        service = AdAsyncService(db)
        query = AdQuery(
            ad_type=ad_type,
            is_active=is_active,
            keyword=keyword
        )
        result = await service.get_ad_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取广告列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取广告列表失败")


@router.get("/type/{ad_type}", response_model=SuccessResponse[List[AdInfo]], summary="根据类型获取活跃广告")
async def get_active_ads_by_type(
    ad_type: str,
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_async_db),
):
    """根据类型获取活跃广告"""
    try:
        service = AdAsyncService(db)
        ads = await service.get_active_ads_by_type(ad_type, limit)
        return SuccessResponse.create(data=ads, message="获取广告成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取广告失败")


@router.post("/{ad_id}/toggle", response_model=SuccessResponse[AdInfo], summary="切换广告状态")
async def toggle_ad_status(
    ad_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """切换广告状态"""
    try:
        service = AdAsyncService(db)
        ad = await service.toggle_ad_status(ad_id)
        return SuccessResponse.create(data=ad, message="切换广告状态成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="切换广告状态失败") 