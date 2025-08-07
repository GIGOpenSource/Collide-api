"""
缓存服务
提供用户相关的缓存操作
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta

from app.common.redis_client import get_redis_client
from app.domains.users.schemas import UserInfo

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        
        # 缓存过期时间配置（秒）
        self.USER_INFO_EXPIRE = 3600  # 用户信息缓存1小时
        self.USER_SESSION_EXPIRE = 2592000  # 用户会话缓存30天
        self.USER_LIST_EXPIRE = 300  # 用户列表缓存5分钟
        self.USER_STATS_EXPIRE = 1800  # 用户统计缓存30分钟
        
        # 缓存键前缀
        self.USER_INFO_PREFIX = "user:info:"
        self.USER_SESSION_PREFIX = "user:session:"
        self.USER_LIST_PREFIX = "user:list:"
        self.USER_STATS_PREFIX = "user:stats:"
        self.USER_WALLET_PREFIX = "user:wallet:"
    
    # ==================== 用户信息缓存 ====================
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息缓存"""
        key = f"{self.USER_INFO_PREFIX}{user_id}"
        try:
            return await self.redis_client.get_json(key)
        except Exception as e:
            logger.error(f"获取用户信息缓存失败 user_id={user_id}: {e}")
            return None
    
    async def set_user_info(self, user_id: int, user_info: Dict[str, Any]) -> bool:
        """设置用户信息缓存"""
        key = f"{self.USER_INFO_PREFIX}{user_id}"
        try:
            return await self.redis_client.set_json(key, user_info, ex=self.USER_INFO_EXPIRE)
        except Exception as e:
            logger.error(f"设置用户信息缓存失败 user_id={user_id}: {e}")
            return False
    
    async def delete_user_info(self, user_id: int) -> bool:
        """删除用户信息缓存"""
        key = f"{self.USER_INFO_PREFIX}{user_id}"
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"删除用户信息缓存失败 user_id={user_id}: {e}")
            return False
    
    # ==================== 用户会话缓存 ====================
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取用户会话缓存"""
        key = f"{self.USER_SESSION_PREFIX}{session_id}"
        try:
            return await self.redis_client.get_json(key)
        except Exception as e:
            logger.error(f"获取用户会话缓存失败 session_id={session_id}: {e}")
            return None
    
    async def set_user_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """设置用户会话缓存"""
        key = f"{self.USER_SESSION_PREFIX}{session_id}"
        try:
            return await self.redis_client.set_json(key, session_data, ex=self.USER_SESSION_EXPIRE)
        except Exception as e:
            logger.error(f"设置用户会话缓存失败 session_id={session_id}: {e}")
            return False
    
    async def delete_user_session(self, session_id: str) -> bool:
        """删除用户会话缓存"""
        key = f"{self.USER_SESSION_PREFIX}{session_id}"
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"删除用户会话缓存失败 session_id={session_id}: {e}")
            return False
    
    # ==================== 用户钱包缓存 ====================
    
    async def get_user_wallet(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户钱包缓存"""
        key = f"{self.USER_WALLET_PREFIX}{user_id}"
        try:
            return await self.redis_client.get_json(key)
        except Exception as e:
            logger.error(f"获取用户钱包缓存失败 user_id={user_id}: {e}")
            return None
    
    async def set_user_wallet(self, user_id: int, wallet_info: Dict[str, Any]) -> bool:
        """设置用户钱包缓存"""
        key = f"{self.USER_WALLET_PREFIX}{user_id}"
        try:
            return await self.redis_client.set_json(key, wallet_info, ex=self.USER_INFO_EXPIRE)
        except Exception as e:
            logger.error(f"设置用户钱包缓存失败 user_id={user_id}: {e}")
            return False
    
    async def delete_user_wallet(self, user_id: int) -> bool:
        """删除用户钱包缓存"""
        key = f"{self.USER_WALLET_PREFIX}{user_id}"
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"删除用户钱包缓存失败 user_id={user_id}: {e}")
            return False
    
    # ==================== 用户列表缓存 ====================
    
    async def get_user_list(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取用户列表缓存"""
        key = f"{self.USER_LIST_PREFIX}{cache_key}"
        try:
            return await self.redis_client.get_json(key)
        except Exception as e:
            logger.error(f"获取用户列表缓存失败 cache_key={cache_key}: {e}")
            return None
    
    async def set_user_list(self, cache_key: str, user_list_data: Dict[str, Any]) -> bool:
        """设置用户列表缓存"""
        key = f"{self.USER_LIST_PREFIX}{cache_key}"
        try:
            return await self.redis_client.set_json(key, user_list_data, ex=self.USER_LIST_EXPIRE)
        except Exception as e:
            logger.error(f"设置用户列表缓存失败 cache_key={cache_key}: {e}")
            return False
    
    # ==================== 用户统计缓存 ====================
    
    async def get_user_stats(self, stats_key: str) -> Optional[Dict[str, Any]]:
        """获取用户统计缓存"""
        key = f"{self.USER_STATS_PREFIX}{stats_key}"
        try:
            return await self.redis_client.get_json(key)
        except Exception as e:
            logger.error(f"获取用户统计缓存失败 stats_key={stats_key}: {e}")
            return None
    
    async def set_user_stats(self, stats_key: str, stats_data: Dict[str, Any]) -> bool:
        """设置用户统计缓存"""
        key = f"{self.USER_STATS_PREFIX}{stats_key}"
        try:
            return await self.redis_client.set_json(key, stats_data, ex=self.USER_STATS_EXPIRE)
        except Exception as e:
            logger.error(f"设置用户统计缓存失败 stats_key={stats_key}: {e}")
            return False
    
    # ==================== 批量操作 ====================
    
    async def delete_user_all_cache(self, user_id: int) -> bool:
        """删除用户相关的所有缓存"""
        try:
            keys_to_delete = [
                f"{self.USER_INFO_PREFIX}{user_id}",
                f"{self.USER_WALLET_PREFIX}{user_id}",
            ]
            
            # 删除所有相关缓存
            deleted_count = await self.redis_client.delete(*keys_to_delete)
            
            logger.info(f"删除用户 {user_id} 的 {deleted_count} 个缓存")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"删除用户所有缓存失败 user_id={user_id}: {e}")
            return False
    
    async def refresh_user_cache(self, user_id: int, user_info: Dict[str, Any]) -> bool:
        """刷新用户缓存"""
        try:
            # 先删除旧缓存
            await self.delete_user_all_cache(user_id)
            
            # 设置新缓存
            return await self.set_user_info(user_id, user_info)
            
        except Exception as e:
            logger.error(f"刷新用户缓存失败 user_id={user_id}: {e}")
            return False
    
    # ==================== 工具方法 ====================
    
    async def cache_exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"检查缓存存在性失败 key={key}: {e}")
            return False
    
    async def get_cache_ttl(self, key: str) -> int:
        """获取缓存剩余过期时间"""
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"获取缓存TTL失败 key={key}: {e}")
            return -1
    
    def generate_list_cache_key(self, **params) -> str:
        """生成列表缓存键"""
        # 将参数排序并组合成缓存键
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params if v is not None)
        return f"list_{hash(param_str)}"
    
    def generate_stats_cache_key(self, stats_type: str, **params) -> str:
        """生成统计缓存键"""
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params if v is not None)
        return f"{stats_type}_{hash(param_str)}"


# 全局缓存服务实例
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    return cache_service
