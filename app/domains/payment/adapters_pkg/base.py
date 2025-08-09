from __future__ import annotations

import hashlib
import random
import string
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request


@dataclass
class PaymentInitResult:
    order_no: str
    pay_url: Optional[str]
    status: str
    pay_mode: Optional[str] = None
    platform_order_no: Optional[str] = None
    response_sign: Optional[str] = None


@dataclass
class NormalizedCallback:
    order_no: str
    platform_order_no: Optional[str]
    status: str  # "paid" | "failed"
    actual_amount: Optional[float]
    pay_time: Optional[datetime]
    raw: str
    sign: Optional[str]
    extra: Dict[str, Any]


class PaymentAdapter:
    name: str

    def build_init_request(self, *, order_no: str, amount: float, notify_url: str, channel_cfg: Dict[str, Any], return_url: Optional[str]) -> Dict[str, Any]:
        raise NotImplementedError

    def sign_init_request(self, payload: Dict[str, Any], channel_cfg: Dict[str, Any]) -> str:
        raise NotImplementedError

    def parse_init_response(self, resp_json: Dict[str, Any], channel_cfg: Dict[str, Any]) -> PaymentInitResult:
        raise NotImplementedError

    def init_endpoint(self, channel_cfg: Dict[str, Any]) -> str:
        raise NotImplementedError

    async def verify_and_parse_callback(self, request: Request, channel_cfg: Dict[str, Any]) -> NormalizedCallback:
        raise NotImplementedError

    def success_response_text(self) -> str:
        return "success"

    def extract_order_no(self, raw_text: str) -> Optional[str]:
        raise NotImplementedError

    def extract_merc_id(self, raw_text: str) -> Optional[str]:
        raise NotImplementedError


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _random_digits(length: int) -> str:
    return ''.join(random.choices(string.digits, k=length))


def _random_alpha_num(length: int) -> str:
    choices = string.ascii_lowercase + string.digits
    return ''.join(random.choices(choices, k=length))

