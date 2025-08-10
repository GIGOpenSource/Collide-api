"""
雪花算法ID生成器
简化版：64位结构
- 1位符号位（固定为0）
- 41位时间戳（毫秒，偏移自自定义纪元）
- 5位数据中心ID
- 5位机器ID
- 12位序列号

配置通过环境变量或默认值提供。
"""
from __future__ import annotations

import os
import threading
import time
from typing import Final


class SnowflakeGenerator:
    _epoch_ms: Final[int] = int(time.mktime((2024, 1, 1, 0, 0, 0, 0, 0, 0)) * 1000)

    def __init__(self, datacenter_id: Optional[int] = None, worker_id: Optional[int] = None):
        self.datacenter_id_bits: Final[int] = 5
        self.worker_id_bits: Final[int] = 5
        self.sequence_bits: Final[int] = 12

        self.max_datacenter_id: Final[int] = (1 << self.datacenter_id_bits) - 1
        self.max_worker_id: Final[int] = (1 << self.worker_id_bits) - 1
        self.sequence_mask: Final[int] = (1 << self.sequence_bits) - 1

        self.worker_id_shift: Final[int] = self.sequence_bits
        self.datacenter_id_shift: Final[int] = self.sequence_bits + self.worker_id_bits
        self.timestamp_shift: Final[int] = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits

        env_dc = os.getenv("SNOWFLAKE_DATACENTER_ID")
        env_wk = os.getenv("SNOWFLAKE_WORKER_ID")
        self.datacenter_id: int = datacenter_id if datacenter_id is not None else int(env_dc or 0)
        self.worker_id: int = worker_id if worker_id is not None else int(env_wk or 0)

        if not (0 <= self.datacenter_id <= self.max_datacenter_id):
            raise ValueError(f"datacenter_id 超出范围: 0~{self.max_datacenter_id}")
        if not (0 <= self.worker_id <= self.max_worker_id):
            raise ValueError(f"worker_id 超出范围: 0~{self.max_worker_id}")

        self._last_timestamp = -1
        self._sequence = 0
        self._lock = threading.Lock()

    def _timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_ts: int) -> int:
        ts = self._timestamp_ms()
        while ts <= last_ts:
            time.sleep(0.0001)
            ts = self._timestamp_ms()
        return ts

    def next_id(self) -> int:
        with self._lock:
            timestamp = self._timestamp_ms()
            if timestamp < self._last_timestamp:
                # 时钟回拨处理：等待到上次时间戳
                timestamp = self._wait_next_millis(self._last_timestamp)

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & self.sequence_mask
                if self._sequence == 0:
                    timestamp = self._wait_next_millis(self._last_timestamp)
            else:
                self._sequence = 0

            self._last_timestamp = timestamp

            diff = timestamp - self._epoch_ms
            snowflake_id = (
                (diff << self.timestamp_shift)
                | (self.datacenter_id << self.datacenter_id_shift)
                | (self.worker_id << self.worker_id_shift)
                | self._sequence
            )
            return snowflake_id


# 全局生成器（可直接使用）
_global_generator = SnowflakeGenerator()


def generate_snowflake_id() -> int:
    return _global_generator.next_id()

