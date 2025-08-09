from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request

from .base import (
    PaymentAdapter,
    PaymentInitResult,
    NormalizedCallback,
    _md5,
    _random_alpha_num,
    _random_digits,
)


class SharkAdapter(PaymentAdapter):
    name = "shark"

    def build_init_request(self, *, order_no: str, amount: float, notify_url: str, channel_cfg: Dict[str, Any], return_url: Optional[str]) -> Dict[str, Any]:
        merc_id = channel_cfg["merchant_id"]
        pay_type = channel_cfg.get("default_pay_type", "alipay")
        info = {
            "playerId": _random_alpha_num(12),
            "playerIp": "0.0.0.0",
            "deviceId": _random_alpha_num(20),
            "deviceType": random.choice(["ios", "android", "pc"]),
            "name": "",
            "tel": _random_digits(11),
            "payAct": _random_digits(11),
        }
        payload = {
            "mercId": merc_id,
            "type": pay_type,
            "money": f"{amount:.2f}",
            "tradeNo": order_no,
            "notifyUrl": notify_url,
            "info": info,
            "time": str(int(datetime.now().timestamp() * 1000)),
            "mode": channel_cfg.get("mode", "url"),
        }
        payload["sign"] = self.sign_init_request(payload, channel_cfg)
        return payload

    def sign_init_request(self, payload: Dict[str, Any], channel_cfg: Dict[str, Any]) -> str:
        raw = f"{payload['mercId']}{payload['money']}{payload['notifyUrl']}{payload['tradeNo']}{payload['type']}{channel_cfg['app_secret']}"
        return _md5(raw)

    def init_endpoint(self, channel_cfg: Dict[str, Any]) -> str:
        return "/api/shark/topay"

    def parse_init_response(self, resp_json: Dict[str, Any], channel_cfg: Dict[str, Any]) -> PaymentInitResult:
        code = resp_json.get("code")
        msg = resp_json.get("msg") or {}
        if code == 200:
            return PaymentInitResult(
                order_no="",
                pay_url=msg.get("payUrl"),
                status="pending",
                pay_mode=msg.get("mode"),
                platform_order_no=msg.get("oid"),
                response_sign=msg.get("sign"),
            )
        else:
            return PaymentInitResult(order_no="", pay_url=None, status="failed")

    async def verify_and_parse_callback(self, request: Request, channel_cfg: Dict[str, Any]) -> NormalizedCallback:
        body_bytes = await request.body()
        raw_text = body_bytes.decode("utf-8") if body_bytes else ""
        return self.verify_and_parse_callback_from_raw(raw_text, channel_cfg)

    def verify_and_parse_callback_from_raw(self, raw_text: str, channel_cfg: Dict[str, Any]) -> NormalizedCallback:
        try:
            data = json.loads(raw_text or "{}")
        except json.JSONDecodeError:
            data = {}
        sign = data.get("sign")
        code = data.get("code")
        merc_id = data.get("mercId")
        oid = data.get("oid")
        pay_money = data.get("payMoney")
        trade_no = data.get("tradeNo")
        expected = _md5(f"{code}{merc_id}{oid}{pay_money}{trade_no}{channel_cfg['app_secret']}") if all([code is not None, merc_id, oid, pay_money, trade_no]) else None
        verified = (sign == expected)

        status = "paid" if (str(code) == "200" and verified) else "failed"
        pay_time = None
        if data.get("payTime"):
            try:
                pay_time = datetime.fromisoformat(str(data["payTime"])) if isinstance(data["payTime"], str) else None
            except Exception:
                pay_time = None

        actual_amount = None
        try:
            actual_amount = float(pay_money) if pay_money is not None else None
        except Exception:
            actual_amount = None

        return NormalizedCallback(
            order_no=trade_no or "",
            platform_order_no=oid,
            status=status,
            actual_amount=actual_amount,
            pay_time=pay_time,
            raw=raw_text,
            sign=sign,
            extra={
                "verified": 1 if verified else 0,
                "code": code,
                "mercId": merc_id,
                "payload": data.get("payload"),
            },
        )

    def extract_order_no(self, raw_text: str) -> Optional[str]:
        try:
            data = json.loads(raw_text or "{}")
            return data.get("tradeNo")
        except Exception:
            return None

    def extract_merc_id(self, raw_text: str) -> Optional[str]:
        try:
            data = json.loads(raw_text or "{}")
            return data.get("mercId")
        except Exception:
            return None

