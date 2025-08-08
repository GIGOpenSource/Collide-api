"""
商品模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.goods.async_service import GoodsAsyncService
from app.domains.goods.schemas import GoodsCreate, GoodsUpdate, GoodsInfo, GoodsQuery


router = APIRouter(prefix="/api/v1/goods", tags=["商品管理"])


@router.post("/", response_model=SuccessResponse[GoodsInfo], summary="创建商品")
async def create_goods(
    req: GoodsCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """创建商品"""
    try:
        service = GoodsAsyncService(db)
        goods = await service.create_goods(req)
        return SuccessResponse.create(data=goods, message="创建商品成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建商品失败")


@router.put("/{goods_id}", response_model=SuccessResponse[GoodsInfo], summary="更新商品")
async def update_goods(
    goods_id: int,
    req: GoodsUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """更新商品"""
    try:
        service = GoodsAsyncService(db)
        goods = await service.update_goods(goods_id, req)
        return SuccessResponse.create(data=goods, message="更新商品成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新商品失败")


@router.delete("/{goods_id}", response_model=SuccessResponse[dict], summary="删除商品")
async def delete_goods(
    goods_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """删除商品"""
    try:
        service = GoodsAsyncService(db)
        await service.delete_goods(goods_id)
        return SuccessResponse.create(data={}, message="删除商品成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除商品失败")


@router.get("/{goods_id}", response_model=SuccessResponse[GoodsInfo], summary="获取商品详情")
async def get_goods_by_id(
    goods_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """获取商品详情"""
    try:
        service = GoodsAsyncService(db)
        goods = await service.get_goods_by_id(goods_id)
        # 增加查看数
        await service.increase_view_count(goods_id)
        return SuccessResponse.create(data=goods, message="获取商品详情成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取商品详情失败")


@router.get("/", response_model=PaginationResponse[GoodsInfo], summary="获取商品列表")
async def get_goods_list(
    category_id: Optional[int] = Query(None, description="分类ID"),
    goods_type: Optional[str] = Query(None, description="商品类型：coin、goods、subscription、content"),
    seller_id: Optional[int] = Query(None, description="商家ID"),
    status: Optional[str] = Query(None, description="状态：active、inactive、sold_out"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    min_price: Optional[float] = Query(None, description="最低价格"),
    max_price: Optional[float] = Query(None, description="最高价格"),
    min_coin_price: Optional[int] = Query(None, description="最低金币价格"),
    max_coin_price: Optional[int] = Query(None, description="最高金币价格"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
):
    """获取商品列表"""
    try:
        service = GoodsAsyncService(db)
        query = GoodsQuery(
            category_id=category_id,
            goods_type=goods_type,
            seller_id=seller_id,
            status=status,
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
            min_coin_price=min_coin_price,
            max_coin_price=max_coin_price
        )
        result = await service.get_goods_list(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取商品列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取商品列表失败")


@router.get("/category/{category_id}", response_model=SuccessResponse[List[GoodsInfo]], summary="根据分类获取商品")
async def get_goods_by_category(
    category_id: int,
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_async_db),
):
    """根据分类获取商品"""
    try:
        service = GoodsAsyncService(db)
        goods_list = await service.get_goods_by_category(category_id, limit)
        return SuccessResponse.create(data=goods_list, message="获取分类商品成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分类商品失败")


@router.get("/hot", response_model=SuccessResponse[List[GoodsInfo]], summary="获取热门商品")
async def get_hot_goods(
    goods_type: Optional[str] = Query(None, description="商品类型"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取热门商品"""
    try:
        service = GoodsAsyncService(db)
        goods_list = await service.get_hot_goods(goods_type, limit)
        return SuccessResponse.create(data=goods_list, message="获取热门商品成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取热门商品失败") 