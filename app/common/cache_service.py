"""
缓存服务 - 增强版
支持多种缓存策略和幂等性
"""
import json
import hashlib
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta
import asyncio
from functools import wraps

from app.common.redis_client import get_redis_client


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.redis_client = None
        self._local_cache = {}  # 本地缓存
        self._cache_lock = asyncio.Lock()  # 缓存锁，防止缓存击穿
    
    async def _get_redis(self):
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))
        
        # 添加关键字参数（排序确保一致性）
        for key in sorted(kwargs.keys()):
            key_parts.append(f"{key}:{kwargs[key]}")
        
        return ":".join(key_parts)
    
    def _generate_idempotent_key(self, user_id: int, operation: str, *args, **kwargs) -> str:
        """生成幂等键"""
        # 基于用户ID、操作类型和参数生成唯一键
        key_data = {
            "user_id": user_id,
            "operation": operation,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"idempotent:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            redis = await self._get_redis()
            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"缓存获取失败: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        try:
            redis = await self._get_redis()
            await redis.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            redis = await self._get_redis()
            await redis.delete(key)
            return True
        except Exception as e:
            print(f"缓存删除失败: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """删除匹配模式的缓存"""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)
            return True
        except Exception as e:
            print(f"批量删除缓存失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            redis = await self._get_redis()
            return await redis.exists(key) > 0
        except Exception as e:
            print(f"缓存检查失败: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            redis = await self._get_redis()
            return await redis.incrby(key, amount)
        except Exception as e:
            print(f"计数器递增失败: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        try:
            redis = await self._get_redis()
            return await redis.expire(key, ttl)
        except Exception as e:
            print(f"设置过期时间失败: {e}")
            return False
    
    # ================ 业务缓存方法 ================
    
    async def get_user_cache(self, user_id: int) -> Optional[Dict]:
        """获取用户缓存"""
        key = f"user:{user_id}"
        return await self.get(key)
    
    async def set_user_cache(self, user_id: int, user_data: Dict, ttl: int = 3600) -> bool:
        """设置用户缓存"""
        key = f"user:{user_id}"
        return await self.set(key, user_data, ttl)
    
    async def delete_user_cache(self, user_id: int) -> bool:
        """删除用户缓存"""
        key = f"user:{user_id}"
        return await self.delete(key)
    
    async def get_content_cache(self, content_id: int) -> Optional[Dict]:
        """获取内容缓存"""
        key = f"content:{content_id}"
        return await self.get(key)
    
    async def set_content_cache(self, content_id: int, content_data: Dict, ttl: int = 1800) -> bool:
        """设置内容缓存"""
        key = f"content:{content_id}"
        return await self.set(key, content_data, ttl)
    
    async def delete_content_cache(self, content_id: int) -> bool:
        """删除内容缓存"""
        key = f"content:{content_id}"
        return await self.delete(key)
    
    async def get_comment_cache(self, comment_type: str, target_id: int) -> Optional[List]:
        """获取评论缓存"""
        key = f"comments:{comment_type}:{target_id}"
        return await self.get(key)
    
    async def set_comment_cache(self, comment_type: str, target_id: int, comments: List, ttl: int = 900) -> bool:
        """设置评论缓存"""
        key = f"comments:{comment_type}:{target_id}"
        return await self.set(key, comments, ttl)
    
    async def delete_comment_cache(self, comment_type: str, target_id: int) -> bool:
        """删除评论缓存"""
        key = f"comments:{comment_type}:{target_id}"
        return await self.delete(key)
    
    async def get_goods_cache(self, goods_id: int) -> Optional[Dict]:
        """获取商品缓存"""
        key = f"goods:{goods_id}"
        return await self.get(key)
    
    async def set_goods_cache(self, goods_id: int, goods_data: Dict, ttl: int = 1800) -> bool:
        """设置商品缓存"""
        key = f"goods:{goods_id}"
        return await self.set(key, goods_data, ttl)
    
    async def delete_goods_cache(self, goods_id: int) -> bool:
        """删除商品缓存"""
        key = f"goods:{goods_id}"
        return await self.delete(key)
    
    # ================ 幂等性方法 ================
    
    async def check_idempotent(self, user_id: int, operation: str, *args, **kwargs) -> Optional[Dict]:
        """检查幂等性，返回已缓存的结果"""
        key = self._generate_idempotent_key(user_id, operation, *args, **kwargs)
        return await self.get(key)
    
    async def set_idempotent_result(self, user_id: int, operation: str, result: Dict, *args, **kwargs) -> bool:
        """设置幂等性结果"""
        key = self._generate_idempotent_key(user_id, operation, *args, **kwargs)
        # 幂等性结果缓存时间较长，防止重复操作
        return await self.set(key, result, ttl=86400)  # 24小时
    
    async def clear_idempotent(self, user_id: int, operation: str, *args, **kwargs) -> bool:
        """清除幂等性缓存"""
        key = self._generate_idempotent_key(user_id, operation, *args, **kwargs)
        return await self.delete(key)
    
    # ================ 缓存装饰器 ================
    
    def cached(self, prefix: str, ttl: int = 3600):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 缓存未命中，执行原函数
                result = await func(*args, **kwargs)
                
                # 缓存结果
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    def idempotent(self, operation: str, ttl: int = 86400):
        """幂等性装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(user_id: int, *args, **kwargs):
                # 检查幂等性
                cached_result = await self.check_idempotent(user_id, operation, *args, **kwargs)
                if cached_result is not None:
                    return cached_result
                
                # 执行原函数
                result = await func(user_id, *args, **kwargs)
                
                # 缓存结果
                await self.set_idempotent_result(user_id, operation, result, *args, **kwargs)
                
                return result
            return wrapper
        return decorator


# 全局缓存服务实例
cache_service = CacheService()
