"""支付路由"""
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.dependencies import get_current_user_context, UserContext
from app.common.response import SuccessResponse, handle_business_error, handle_system_error
from app.common.exceptions import BusinessException
from app.domains.payment.async_service import PaymentAsyncService
from app.domains.payment.schemas import PaymentCreate, PaymentNotify, PaymentInfo
from app.domains.payment.adapters import get_adapter

router = APIRouter(prefix="/api/v1/payments", tags=["支付管理"]) 


@router.post("/init", summary="创建支付单/预下单（透传上游返回）")
async def init_payment(
    req: PaymentCreate,
    db: AsyncSession = Depends(get_async_db),
    user: UserContext = Depends(get_current_user_context),
    request: Request = None,
):
    try:
        svc = PaymentAsyncService(db)
        upstream = await svc.create_payment(user.user_id, req, request)
        return upstream
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


@router.post("/callback/{provider}", summary="第三方支付回调(纯文本应答)")
async def payment_callback(provider: str, request: Request, db: AsyncSession = Depends(get_async_db)):
    try:
        adapter = get_adapter(provider)
        svc = PaymentAsyncService(db)
        text = await svc.handle_provider_callback(adapter, request)
        return Response(content=text, media_type="text/plain; charset=utf-8")
    except BusinessException as e:
        # 出于对方重试考虑，不泄漏内部信息，返回非success纯文本
        return Response(content="fail", media_type="text/plain; charset=utf-8", status_code=200)
    except Exception:
        return Response(content="fail", media_type="text/plain; charset=utf-8", status_code=200)