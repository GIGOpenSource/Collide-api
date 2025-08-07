"""
Redis客户端管理
提供异步Redis连接和基础操作
"""
import json
import logging
from typing import Optional, Any, Union, List
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis

from app.common.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
        self._connection_pool = None
    
    async def init_redis(self) -> None:
        """初始化Redis连接"""
        try:
            # 创建连接池
            self._connection_pool = redis.ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                decode_responses=True,
                encoding='utf-8'
            )
            
            # 创建Redis客户端
            self._redis = Redis(connection_pool=self._connection_pool)
            
            # 测试连接
            await self._redis.ping()
            logger.info(f"Redis连接成功: {settings.redis_host}:{settings.redis_port}")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self._redis = None
            raise
    
    async def close_redis(self) -> None:
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis连接已关闭")
            self._redis = None
        
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
    
    @property
    def redis(self) -> Redis:
        """获取Redis客户端"""
        if not self._redis:
            raise RuntimeError("Redis未初始化，请先调用init_redis()")
        return self._redis
    
    @asynccontextmanager
    async def get_redis(self):
        """获取Redis连接的上下文管理器"""
        if not self._redis:
            await self.init_redis()
        try:
            yield self._redis
        except Exception as e:
            logger.error(f"Redis操作异常: {e}")
            raise


class RedisClient:
    """Redis操作客户端"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET失败 key={key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """设置字符串值"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except Exception as e:
            logger.error(f"Redis SET失败 key={key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """删除键"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE失败 keys={keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.exists(*keys)
        except Exception as e:
            logger.error(f"Redis EXISTS失败 keys={keys}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE失败 key={key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键剩余过期时间"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL失败 key={key}: {e}")
            return -1
    
    # JSON操作方法
    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置JSON值"""
        try:
            json_str = json.dumps(value, ensure_ascii=False, default=str)
            return await self.set(key, json_str, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET_JSON失败 key={key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """获取JSON值"""
        try:
            json_str = await self.get(key)
            if json_str:
                return json.loads(json_str)
            return None
        except Exception as e:
            logger.error(f"Redis GET_JSON失败 key={key}: {e}")
            return None
    
    # Hash操作方法
    async def hset(self, name: str, mapping: dict) -> int:
        """设置哈希字段"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.hset(name, mapping=mapping)
        except Exception as e:
            logger.error(f"Redis HSET失败 name={name}: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段值"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET失败 name={name} key={key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> dict:
        """获取所有哈希字段"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL失败 name={name}: {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis HDEL失败 name={name} keys={keys}: {e}")
            return 0
    
    # List操作方法
    async def lpush(self, name: str, *values: str) -> int:
        """从左侧推入列表"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.lpush(name, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH失败 name={name}: {e}")
            return 0
    
    async def rpop(self, name: str) -> Optional[str]:
        """从右侧弹出列表元素"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.rpop(name)
        except Exception as e:
            logger.error(f"Redis RPOP失败 name={name}: {e}")
            return None
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """获取列表范围元素"""
        try:
            async with self.redis_manager.get_redis() as redis:
                return await redis.lrange(name, start, end)
        except Exception as e:
            logger.error(f"Redis LRANGE失败 name={name}: {e}")
            return []


# 全局Redis管理器和客户端实例
redis_manager = RedisManager()
redis_client = RedisClient(redis_manager)


async def init_redis():
    """初始化Redis连接"""
    await redis_manager.init_redis()


async def close_redis():
    """关闭Redis连接"""
    await redis_manager.close_redis()


def get_redis_client() -> RedisClient:
    """获取Redis客户端"""
    return redis_client
