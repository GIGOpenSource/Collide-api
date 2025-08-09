"""支付路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.dependencies import get_current_user_context, UserContext
from app.common.response import SuccessResponse, handle_business_error, handle_system_error
from app.common.exceptions import BusinessException
from app.domains.payment.async_service import PaymentAsyncService
from app.domains.payment.schemas import PaymentCreate, PaymentInitResponse, PaymentNotify, PaymentInfo

router = APIRouter(prefix="/api/v1/payments", tags=["支付管理"]) 


@router.post("/init", response_model=SuccessResponse[PaymentInitResponse], summary="创建支付单/预支付")
async def init_payment(
    req: PaymentCreate,
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context)
):
    try:
        svc = PaymentAsyncService(db)
        data = await svc.create_payment(user.user_id, req)
        return SuccessResponse.create(data=data, message="预支付创建成功")
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("预支付失败，请稍后重试")


@router.get("/{order_no}", response_model=SuccessResponse[PaymentInfo], summary="查询支付单")
async def get_payment(
    order_no: str,
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context)
):
    try:
        svc = PaymentAsyncService(db)
        data = await svc.get_payment(order_no, user.user_id)
        return SuccessResponse.create(data=data, message="获取成功")
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("获取失败，请稍后重试")


@router.post("/notify", response_model=SuccessResponse[bool], summary="支付回调(模拟)")
async def payment_notify(
    notify: PaymentNotify,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        svc = PaymentAsyncService(db)
        ok = await svc.handle_notify(notify)
        return SuccessResponse.create(data=ok, message="回调处理完成")
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception:
        return handle_system_error("回调处理失败")