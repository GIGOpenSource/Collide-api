"""
支付适配器聚合入口：暴露统一注册表与获取函数
实现拆分到 adapters_pkg/
"""
from typing import Dict

from .adapters_pkg.base import PaymentAdapter
from .adapters_pkg.shark import SharkAdapter

_REGISTRY: Dict[str, PaymentAdapter] = {
    SharkAdapter.name: SharkAdapter(),
}


def get_adapter(provider: str) -> PaymentAdapter:
    adapter = _REGISTRY.get(provider)
    if not adapter:
        raise ValueError(f"未支持的支付提供商: {provider}")
    return adapter

