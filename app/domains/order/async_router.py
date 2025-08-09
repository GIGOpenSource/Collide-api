"""订单路由"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.dependencies import get_current_user_context, get_pagination, UserContext
from app.common.pagination import PaginationParams
from app.common.response import SuccessResponse, PaginationResponse, handle_business_error, handle_system_error
from app.common.exceptions import BusinessException
from app.domains.order.async_service import OrderAsyncService
from app.domains.order.schemas import OrderCreate, OrderInfo, OrderQuery

router = APIRouter(prefix="/api/v1/orders", tags=["订单管理"]) 


@router.post("/", response_model=SuccessResponse[OrderInfo], summary="创建订单")
async def create_order(
    req: OrderCreate,
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context)
):
    try:
        svc = OrderAsyncService(db)
        data = await svc.create_order(user.user_id, user.username, req)
        return SuccessResponse.create(data=data, message="下单成功")
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("下单失败，请稍后重试")


@router.get("/{order_id}", response_model=SuccessResponse[OrderInfo], summary="订单详情")
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context)
):
    try:
        svc = OrderAsyncService(db)
        data = await svc.get_order(order_id, user.user_id)
        return SuccessResponse.create(data=data, message="获取成功")
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("获取订单失败，请稍后重试")


@router.get("/", response_model=PaginationResponse[OrderInfo], summary="订单列表")
async def list_orders(
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context),
    pagination: PaginationParams = Depends(get_pagination),
    status: Optional[str] = None,
    pay_status: Optional[str] = None,
    goods_type: Optional[str] = None,
):
    try:
        svc = OrderAsyncService(db)
        q = OrderQuery(status=status, pay_status=pay_status, goods_type=goods_type)
        result = await svc.list_orders(user.user_id, q, pagination)
        return PaginationResponse.create(
            datas=result.items, total=result.total,
            current_page=result.page, page_size=result.page_size, message="获取成功"
        )
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("获取订单列表失败，请稍后重试")


@router.post("/{order_id}/cancel", response_model=SuccessResponse[bool], summary="取消订单")
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context)
):
    try:
        svc = OrderAsyncService(db)
        ok = await svc.cancel_order(order_id, user.user_id)
        return SuccessResponse.create(data=ok, message="订单已取消")
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("取消失败，请稍后重试")