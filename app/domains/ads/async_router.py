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
from app.domains.ads.schemas import AdCreate, AdUpdate, AdInfo, AdQuery, GameImageCreate, GameImageCreateWithAdId, GameImageUpdate, GameImageInfo, GameImageBatchCreate, GameAdInfo


router = APIRouter(prefix="/api/v1/ads", tags=["广告查询"])


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


# @router.put("/{ad_id}", response_model=SuccessResponse[AdInfo], summary="更新广告")
# async def update_ad(
#     ad_id: int,
#     req: AdUpdate,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     """更新广告"""
#     try:
#         service = AdAsyncService(db)
#         ad = await service.update_ad(ad_id, req)
#         return SuccessResponse.create(data=ad, message="更新广告成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="更新广告失败")


# @router.delete("/{ad_id}", response_model=SuccessResponse[dict], summary="删除广告")
# async def delete_ad(
#     ad_id: int,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     """删除广告"""
#     try:
#         service = AdAsyncService(db)
#         await service.delete_ad(ad_id)
#         return SuccessResponse.create(data={}, message="删除广告成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="删除广告失败")


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
    ad_types: Optional[List[str]] = Query(None, description="广告类型集合，OR 关系，如多选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词"),
    ad_name: Optional[str] = Query(None, description="广告名称，模糊"),
    ad_title: Optional[str] = Query(None, description="广告标题，模糊"),
    target_type: Optional[str] = Query(None, description="链接打开方式：_blank/_self"),
    start_time: Optional[str] = Query(None, description="创建时间起，ISO8601"),
    end_time: Optional[str] = Query(None, description="创建时间止，ISO8601"),
    min_sort: Optional[int] = Query(None, description="最小排序权重"),
    max_sort: Optional[int] = Query(None, description="最大排序权重"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取广告列表"""
    try:
        from datetime import datetime
        def parse_dt(s: Optional[str]):
            try:
                return datetime.fromisoformat(s) if s else None
            except Exception:
                return None
        service = AdAsyncService(db)
        query = AdQuery(
            ad_type=ad_type,
            ad_types=ad_types,
            is_active=is_active,
            keyword=keyword,
            ad_name=ad_name,
            ad_title=ad_title,
            target_type=target_type,
            start_time=parse_dt(start_time),
            end_time=parse_dt(end_time),
            min_sort=min_sort,
            max_sort=max_sort,
        )
        result = await service.get_ad_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取广告列表成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
            except Exception as e:
            return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取广告列表失败，请稍后重试"
        )


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


# @router.post("/{ad_id}/toggle", response_model=SuccessResponse[AdInfo], summary="切换广告状态")
# async def toggle_ad_status(
#     ad_id: int,
#     db: AsyncSession = Depends(get_async_db),
# ):
#     """切换广告状态"""
#     try:
#         service = AdAsyncService(db)
#         ad = await service.toggle_ad_status(ad_id)
#         return SuccessResponse.create(data=ad, message="切换广告状态成功")
#     except BusinessException as e:
#         raise HTTPException(status_code=400, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="切换广告状态失败")

# ================ 游戏图片相关接口 ================

@router.post("/game-images", response_model=SuccessResponse[GameImageInfo], summary="创建游戏图片")
async def create_game_image(
    req: GameImageCreateWithAdId,
    db: AsyncSession = Depends(get_async_db),
):
    """创建游戏图片"""
    try:
        service = AdAsyncService(db)
        game_image = await service.create_game_image(req)
        return SuccessResponse.create(data=game_image, message="创建游戏图片成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建游戏图片失败")


@router.post("/game-images/batch", response_model=SuccessResponse[List[GameImageInfo]], summary="批量创建游戏图片")
async def batch_create_game_images(
    req: GameImageBatchCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """批量创建游戏图片"""
    try:
        service = AdAsyncService(db)
        game_images = await service.batch_create_game_images(req)
        return SuccessResponse.create(data=game_images, message="批量创建游戏图片成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="批量创建游戏图片失败")


@router.get("/game-images/{image_id}", response_model=SuccessResponse[GameImageInfo], summary="获取游戏图片详情")
async def get_game_image_by_id(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取游戏图片详情"""
    try:
        service = AdAsyncService(db)
        game_image = await service.get_game_image_by_id(image_id)
        return SuccessResponse.create(data=game_image, message="获取游戏图片详情成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取游戏图片详情失败")


@router.get("/{ad_id}/game-images", response_model=PaginationResponse[GameImageInfo], summary="获取广告的游戏图片列表")
async def get_game_images_by_ad_id(
    ad_id: int,
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取广告的游戏图片列表"""
    try:
        service = AdAsyncService(db)
        result = await service.get_game_images_by_ad_id(ad_id, pagination)
        return PaginationResponse.from_pagination_result(result, "获取游戏图片列表成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取游戏图片列表失败，请稍后重试"
        )


@router.put("/game-images/{image_id}", response_model=SuccessResponse[GameImageInfo], summary="更新游戏图片")
async def update_game_image(
    image_id: int,
    req: GameImageUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """更新游戏图片"""
    try:
        service = AdAsyncService(db)
        game_image = await service.update_game_image(image_id, req)
        return SuccessResponse.create(data=game_image, message="更新游戏图片成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新游戏图片失败")


@router.delete("/game-images/{image_id}", response_model=SuccessResponse[dict], summary="删除游戏图片")
async def delete_game_image(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """删除游戏图片"""
    try:
        service = AdAsyncService(db)
        await service.delete_game_image(image_id)
        return SuccessResponse.create(data={}, message="删除游戏图片成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除游戏图片失败")


@router.post("/game-images/{image_id}/toggle", response_model=SuccessResponse[GameImageInfo], summary="切换游戏图片状态")
async def toggle_game_image_status(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """切换游戏图片状态"""
    try:
        service = AdAsyncService(db)
        game_image = await service.toggle_game_image_status(image_id)
        return SuccessResponse.create(data=game_image, message="切换游戏图片状态成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="切换游戏图片状态失败")


@router.get("/{ad_id}/with-images", response_model=SuccessResponse[GameAdInfo], summary="获取包含图片列表的游戏广告")
async def get_game_ad_with_images(
    ad_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取包含图片列表的游戏广告"""
    try:
        service = AdAsyncService(db)
        game_ad = await service.get_game_ad_with_images(ad_id)
        return SuccessResponse.create(data=game_ad, message="获取游戏广告详情成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取游戏广告详情失败") 