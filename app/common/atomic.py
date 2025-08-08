"""
原子性管理模块
提供数据库事务、分布式锁、乐观锁等原子性保障机制
"""
import asyncio
import time
import uuid
from typing import Optional, Callable, Any, Dict, List
from functools import wraps
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException


class AtomicManager:
    """原子性管理器"""
    
    def __init__(self):
        self._locks = {}  # 本地锁缓存
        self._lock_timeout = 30  # 锁超时时间（秒）
        self._retry_times = 3  # 重试次数
        self._retry_delay = 0.1  # 重试延迟（秒）

    # ================ 数据库事务管理 ================

    @asynccontextmanager
    async def transaction(self, db: AsyncSession, rollback_on_error: bool = True):
        """数据库事务上下文管理器"""
        try:
            yield db
            await db.commit()
        except Exception as e:
            if rollback_on_error:
                await db.rollback()
            raise e

    async def execute_in_transaction(self, db: AsyncSession, func: Callable, *args, **kwargs):
        """在事务中执行函数"""
        async with self.transaction(db):
            return await func(*args, **kwargs)

    # ================ 分布式锁机制 ================

    async def acquire_lock(self, lock_key: str, timeout: int = None, owner: str = None) -> bool:
        """获取分布式锁"""
        if timeout is None:
            timeout = self._lock_timeout
        
        if owner is None:
            owner = str(uuid.uuid4())
        
        lock_value = {
            "owner": owner,
            "acquire_time": time.time(),
            "expire_time": time.time() + timeout
        }
        
        # 尝试获取锁
        success = await cache_service.set(f"lock:{lock_key}", lock_value, ttl=timeout)
        
        if success:
            # 记录锁信息
            self._locks[lock_key] = {
                "owner": owner,
                "acquire_time": lock_value["acquire_time"]
            }
        
        return success

    async def release_lock(self, lock_key: str, owner: str = None) -> bool:
        """释放分布式锁"""
        # 检查锁是否存在且属于当前所有者
        lock_data = await cache_service.get(f"lock:{lock_key}")
        if not lock_data:
            return True  # 锁不存在，认为释放成功
        
        if owner and lock_data.get("owner") != owner:
            return False  # 锁不属于当前所有者
        
        # 删除锁
        success = await cache_service.delete(f"lock:{lock_key}")
        
        if success:
            # 清理本地记录
            self._locks.pop(lock_key, None)
        
        return success

    async def is_locked(self, lock_key: str) -> bool:
        """检查锁是否存在"""
        lock_data = await cache_service.get(f"lock:{lock_key}")
        if not lock_data:
            return False
        
        # 检查锁是否过期
        if time.time() > lock_data.get("expire_time", 0):
            await cache_service.delete(f"lock:{lock_key}")
            return False
        
        return True

    @asynccontextmanager
    async def distributed_lock(self, lock_key: str, timeout: int = None, owner: str = None):
        """分布式锁上下文管理器"""
        if owner is None:
            owner = str(uuid.uuid4())
        
        acquired = False
        try:
            acquired = await self.acquire_lock(lock_key, timeout, owner)
            if not acquired:
                raise BusinessException("获取分布式锁失败")
            yield
        finally:
            if acquired:
                await self.release_lock(lock_key, owner)

    # ================ 乐观锁机制 ================

    async def get_version(self, table_name: str, record_id: int, db: AsyncSession) -> Optional[int]:
        """获取记录版本号"""
        result = await db.execute(
            text(f"SELECT version FROM {table_name} WHERE id = :id"),
            {"id": record_id}
        )
        row = result.fetchone()
        return row[0] if row else None

    async def update_with_version(self, table_name: str, record_id: int, data: Dict, 
                                expected_version: int, db: AsyncSession) -> bool:
        """带版本号的更新操作"""
        # 构建更新SQL
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        sql = f"""
            UPDATE {table_name} 
            SET {set_clause}, version = version + 1 
            WHERE id = :id AND version = :expected_version
        """
        
        # 执行更新
        result = await db.execute(text(sql), {**data, "id": record_id, "expected_version": expected_version})
        await db.commit()
        
        return result.rowcount > 0

    async def optimistic_update(self, table_name: str, record_id: int, data: Dict, 
                              db: AsyncSession, max_retries: int = 3) -> bool:
        """乐观锁更新操作"""
        for attempt in range(max_retries):
            # 获取当前版本
            current_version = await self.get_version(table_name, record_id, db)
            if current_version is None:
                raise BusinessException("记录不存在")
            
            # 尝试更新
            success = await self.update_with_version(table_name, record_id, data, current_version, db)
            if success:
                return True
            
            # 更新失败，等待后重试
            if attempt < max_retries - 1:
                await asyncio.sleep(self._retry_delay * (attempt + 1))
        
        raise BusinessException("乐观锁更新失败，请重试")

    # ================ 原子性装饰器 ================

    def atomic_transaction(self, rollback_on_error: bool = True):
        """事务原子性装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 查找数据库会话参数
                db_session = None
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db_session = arg
                        break
                
                if not db_session:
                    for value in kwargs.values():
                        if isinstance(value, AsyncSession):
                            db_session = value
                            break
                
                if not db_session:
                    raise BusinessException("未找到数据库会话")
                
                async with self.transaction(db_session, rollback_on_error):
                    return await func(*args, **kwargs)
            
            return wrapper
        return decorator

    def atomic_lock(self, lock_key_func: Callable = None, timeout: int = None):
        """分布式锁原子性装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成锁键
                if lock_key_func:
                    lock_key = lock_key_func(*args, **kwargs)
                else:
                    # 默认使用函数名和参数生成锁键
                    lock_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                async with self.distributed_lock(lock_key, timeout):
                    return await func(*args, **kwargs)
            
            return wrapper
        return decorator

    def atomic_optimistic(self, table_name: str, id_param: str = "id", 
                         version_param: str = "version", max_retries: int = 3):
        """乐观锁原子性装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 查找数据库会话和记录ID
                db_session = None
                record_id = None
                
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db_session = arg
                
                if not db_session:
                    for value in kwargs.values():
                        if isinstance(value, AsyncSession):
                            db_session = value
                            break
                
                if not db_session:
                    raise BusinessException("未找到数据库会话")
                
                # 从参数中获取记录ID
                if id_param in kwargs:
                    record_id = kwargs[id_param]
                else:
                    # 尝试从位置参数中获取
                    for arg in args:
                        if isinstance(arg, int) and arg > 0:
                            record_id = arg
                            break
                
                if not record_id:
                    raise BusinessException("未找到记录ID")
                
                # 执行乐观锁更新
                return await self.optimistic_update(table_name, record_id, kwargs, db_session, max_retries)
            
            return wrapper
        return decorator

    # ================ 批量原子操作 ================

    async def batch_atomic_operation(self, operations: List[Callable], db: AsyncSession):
        """批量原子操作"""
        async with self.transaction(db):
            results = []
            for operation in operations:
                try:
                    result = await operation()
                    results.append({"success": True, "result": result})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
                    raise e  # 回滚事务
            return results

    # ================ 条件原子操作 ================

    async def conditional_atomic_operation(self, condition: Callable, operation: Callable, 
                                         db: AsyncSession, max_retries: int = 3):
        """条件原子操作"""
        for attempt in range(max_retries):
            async with self.transaction(db):
                # 检查条件
                if not await condition():
                    raise BusinessException("条件不满足")
                
                # 执行操作
                result = await operation()
                return result
        
        raise BusinessException("条件原子操作失败")

    # ================ 锁清理 ================

    async def cleanup_expired_locks(self):
        """清理过期的锁"""
        # 这里可以实现定期清理过期锁的逻辑
        # 简化实现，实际项目中可以使用定时任务
        pass

    async def get_lock_info(self) -> Dict:
        """获取锁信息"""
        return {
            "local_locks": self._locks,
            "lock_count": len(self._locks)
        }


# 全局原子性管理器实例
atomic_manager = AtomicManager()


# ================ 便捷函数 ================

def atomic_transaction(rollback_on_error: bool = True):
    """事务原子性装饰器"""
    return atomic_manager.atomic_transaction(rollback_on_error)


def atomic_lock(lock_key_func: Callable = None, timeout: int = None):
    """分布式锁原子性装饰器"""
    return atomic_manager.atomic_lock(lock_key_func, timeout)


def atomic_optimistic(table_name: str, id_param: str = "id", 
                     version_param: str = "version", max_retries: int = 3):
    """乐观锁原子性装饰器"""
    return atomic_manager.atomic_optimistic(table_name, id_param, version_param, max_retries)


async def execute_in_transaction(db: AsyncSession, func: Callable, *args, **kwargs):
    """在事务中执行函数"""
    return await atomic_manager.execute_in_transaction(db, func, *args, **kwargs)


async def acquire_lock(lock_key: str, timeout: int = None, owner: str = None) -> bool:
    """获取分布式锁"""
    return await atomic_manager.acquire_lock(lock_key, timeout, owner)


async def release_lock(lock_key: str, owner: str = None) -> bool:
    """释放分布式锁"""
    return await atomic_manager.release_lock(lock_key, owner)


async def optimistic_update(table_name: str, record_id: int, data: Dict, 
                          db: AsyncSession, max_retries: int = 3) -> bool:
    """乐观锁更新操作"""
    return await atomic_manager.optimistic_update(table_name, record_id, data, db, max_retries) 