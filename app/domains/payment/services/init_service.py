from datetime import datetime, timedelta
from typing import Any, Dict

import httpx
import orjson
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.exceptions import BusinessException
from app.domains.order.models import Order
from app.domains.payment.adapters import get_adapter
from app.domains.payment.models import PaymentChannel, PaymentOrder
from app.domains.payment.request_log_models import PaymentRequestLog


class PaymentInitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, user_id: int, req, request=None):
        # 校验订单：仅信任 orderId + userId，并读取后端金额
        if req.user_id != user_id:
            raise BusinessException(code=403, message="用户信息不匹配")
        order_row = await self.db.execute(select(Order).where(Order.id == req.order_id))
        order = order_row.scalar_one_or_none()
        if not order:
            raise BusinessException(code=404, message="订单不存在")
        if order.user_id != user_id:
            raise BusinessException(code=403, message="无权支付该订单")
        if order.pay_status == "paid":
            return {"code": 200, "msg": {"tradeNo": order.order_no, "mode": "url", "payUrl": None}}
        amount = float(order.final_amount)

        # 创建/更新支付单（不存玩家info）
        row = await self.db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order.order_no))
        po = row.scalar_one_or_none()
        if not po:
            po = PaymentOrder(
                order_no=order.order_no,
                user_id=user_id,
                channel_code=req.channel_code,
                pay_type=req.pay_type,
                amount=amount,
                status="pending",
                pay_url=f"https://pay.example.com/mock/{order.order_no}",
                expire_time=datetime.now() + timedelta(minutes=30),
                notify_url=None,
                return_url=req.return_url,
                request_time=int(datetime.now().timestamp() * 1000),
                create_time=datetime.now(),
                update_time=datetime.now(),
            )
            self.db.add(po)
        else:
            po.channel_code = req.channel_code
            po.pay_type = req.pay_type
            po.amount = amount
            po.status = "pending"
            po.pay_url = f"https://pay.example.com/mock/{order.order_no}"
            po.expire_time = datetime.now() + timedelta(minutes=30)
            po.update_time = datetime.now()

        # 读取渠道配置
        channel_row = await self.db.execute(select(PaymentChannel).where(PaymentChannel.channel_code == req.channel_code))
        channel = channel_row.scalar_one_or_none()
        if not channel:
            raise BusinessException(code=400, message="支付渠道不存在或未配置")

        # 构建回调地址（可配置 base URL）
        provider = channel.provider
        public_base = (settings.payment_public_base_url or "").rstrip('/')
        path = f"/api/v1/payments/callback/{provider}"
        notify_url = f"{public_base}{path}" if public_base else path

        # 通过适配器构建上游请求参数
        adapter = get_adapter(provider)
        payload = adapter.build_init_request(
            order_no=order.order_no,
            amount=amount,
            notify_url=notify_url,
            channel_cfg={
                "merchant_id": channel.merchant_id,
                "app_secret": channel.app_secret,
                "mode": None,
                "default_pay_type": req.pay_type,
                "api_gateway": channel.api_gateway,
            },
            return_url=req.return_url,
        )

        # 实际发起请求（HTTP/1.1），并将上游返回原样透传给前端
        request_time_ms = int(datetime.now().timestamp() * 1000)
        endpoint = adapter.init_endpoint({})
        base_url = (channel.api_gateway or settings.default_payment_api_base_url or "").rstrip('/')
        url = f"{base_url}{endpoint}"
        req_body: Dict[str, Any] = payload
        req_sign = req_body.get("sign")

        http_status = None
        resp_text = None
        resp_sign = None
        pay_url_resp = None
        pay_mode_resp = None
        platform_order_no_resp = None
        upstream_json = None
        try:
            timeout = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=3.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=req_body, headers={"Content-Type": "application/json"})
            http_status = resp.status_code
            resp_text = resp.text
            data = resp.json()
            upstream_json = data
            parsed = adapter.parse_init_response(data, {
                "merchant_id": channel.merchant_id,
                "app_secret": channel.app_secret,
            })
            pay_url_resp = parsed.pay_url
            pay_mode_resp = parsed.pay_mode
            platform_order_no_resp = parsed.platform_order_no
            resp_sign = parsed.response_sign
            if pay_url_resp:
                po.pay_url = pay_url_resp
            if pay_mode_resp:
                po.pay_mode = pay_mode_resp
            if platform_order_no_resp:
                po.platform_order_no = platform_order_no_resp
            if resp_sign:
                po.response_sign = resp_sign
            await self.db.commit()
        except Exception:
            pass

        # 记录请求日志
        try:
            log = PaymentRequestLog(
                order_no=order.order_no,
                channel_code=req.channel_code,
                attempt_no=1,
                request_time_ms=request_time_ms,
                request_body=orjson.dumps(req_body).decode(),
                request_sign=req_sign,
                response_time_ms=int(datetime.now().timestamp() * 1000),
                http_status=http_status or 0,
                response_body=resp_text or "",
                response_sign=resp_sign,
                success=1 if (http_status == 200 and pay_url_resp) else 0,
            )
            self.db.add(log)
            await self.db.commit()
        except Exception:
            pass

        # 透传上游返回
        return upstream_json or {"code": http_status or 500, "err": "empty response"}

