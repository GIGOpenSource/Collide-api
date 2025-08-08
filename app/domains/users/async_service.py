"""
用户模块异步服务层 - 增强版
添加缓存、幂等性和原子性支持
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func
from passlib.context import CryptContext

from app.domains.users.models import User
from app.domains.users.schemas import UserCreate, UserUpdate, UserInfo, UserQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
from app.common.cache_service import cache_service
from app.common.atomic import atomic_transaction, atomic_lock, execute_in_transaction


class UserAsyncService:
    """用户异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _hash_password(self, password: str) -> str:
        """密码加密"""
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """密码验证"""
        return self.pwd_context.verify(plain_password, hashed_password)

    @atomic_transaction()
    async def create_user(self, req: UserCreate) -> UserInfo:
        """创建用户 - 带原子性事务"""
        # 检查用户名是否已存在
        existing_user = (await self.db.execute(
            select(User).where(User.username == req.username)
        )).scalar_one_or_none()
        
        if existing_user:
            raise BusinessException("用户名已存在")

        # 检查邮箱是否已存在
        if req.email:
            existing_email = (await self.db.execute(
                select(User).where(User.email == req.email)
            )).scalar_one_or_none()
            
            if existing_email:
                raise BusinessException("邮箱已被注册")

        # 创建用户
        hashed_password = self._hash_password(req.password)
        user = User(
            username=req.username,
            email=req.email,
            nickname=req.nickname or req.username,
            hashed_password=hashed_password,
            status="active"
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 清除相关缓存
        await cache_service.delete_pattern("user:*")
        
        return UserInfo.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> UserInfo:
        """根据ID获取用户 - 带缓存"""
        # 尝试从缓存获取
        cached_user = await cache_service.get_user_cache(user_id)
        if cached_user:
            return UserInfo.model_validate(cached_user)

        # 缓存未命中，从数据库获取
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        user_info = UserInfo.model_validate(user)
        
        # 缓存用户信息
        await cache_service.set_user_cache(user_id, user_info.model_dump())
        
        return user_info

    async def get_user_by_username(self, username: str) -> UserInfo:
        """根据用户名获取用户 - 带缓存"""
        # 尝试从缓存获取
        cache_key = f"user:username:{username}"
        cached_user = await cache_service.get(cache_key)
        if cached_user:
            return UserInfo.model_validate(cached_user)

        # 缓存未命中，从数据库获取
        user = (await self.db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        user_info = UserInfo.model_validate(user)
        
        # 缓存用户信息
        await cache_service.set(cache_key, user_info.model_dump(), ttl=3600)
        
        return user_info

    @atomic_transaction()
    async def update_user(self, user_id: int, req: UserUpdate) -> UserInfo:
        """更新用户 - 带原子性事务和缓存失效"""
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        # 更新字段
        update_data = {}
        if req.username is not None:
            # 检查用户名是否已被其他用户使用
            existing_user = (await self.db.execute(
                select(User).where(and_(User.username == req.username, User.id != user_id))
            )).scalar_one_or_none()
            if existing_user:
                raise BusinessException("用户名已被使用")
            update_data["username"] = req.username

        if req.email is not None:
            # 检查邮箱是否已被其他用户使用
            existing_email = (await self.db.execute(
                select(User).where(and_(User.email == req.email, User.id != user_id))
            )).scalar_one_or_none()
            if existing_email:
                raise BusinessException("邮箱已被使用")
            update_data["email"] = req.email

        if req.nickname is not None:
            update_data["nickname"] = req.nickname
        if req.avatar is not None:
            update_data["avatar"] = req.avatar
        if req.bio is not None:
            update_data["bio"] = req.bio
        if req.status is not None:
            update_data["status"] = req.status

        if update_data:
            await self.db.execute(update(User).where(User.id == user_id).values(**update_data))
            await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_user_cache(user_id)
        await cache_service.delete_pattern(f"user:username:*")

        # 重新获取用户信息
        return await self.get_user_by_id(user_id)

    @atomic_transaction()
    async def delete_user(self, user_id: int) -> bool:
        """删除用户 - 带原子性事务和缓存清理"""
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_user_cache(user_id)
        await cache_service.delete_pattern(f"user:username:*")

        return True

    async def get_user_list(self, query: UserQuery, pagination: PaginationParams) -> PaginationResult[UserInfo]:
        """获取用户列表 - 带缓存"""
        # 生成缓存键
        cache_key = f"user:list:{hash(str(query.model_dump()) + str(pagination.model_dump()))}"
        
        # 尝试从缓存获取
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.model_validate(cached_result)

        # 构建查询条件
        conditions = []
        if query.username:
            conditions.append(User.username.contains(query.username))
        if query.email:
            conditions.append(User.email.contains(query.email))
        if query.nickname:
            conditions.append(User.nickname.contains(query.nickname))
        if query.status:
            conditions.append(User.status == query.status)

        stmt = select(User).where(and_(*conditions)).order_by(User.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        user_info_list = [UserInfo.model_validate(user) for user in users]

        pagination_result = PaginationResult.create(
            items=user_info_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

        # 缓存结果（短期缓存）
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)

        return pagination_result

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInfo]:
        """用户认证 - 带缓存"""
        user = (await self.db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if not user:
            return None

        if not self._verify_password(password, user.hashed_password):
            return None

        return UserInfo.model_validate(user)

    @atomic_transaction()
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码 - 带原子性事务"""
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        if not self._verify_password(old_password, user.hashed_password):
            raise BusinessException("原密码错误")

        hashed_new_password = self._hash_password(new_password)
        await self.db.execute(
            update(User).where(User.id == user_id).values(hashed_password=hashed_new_password)
        )
        await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_user_cache(user_id)

        return True

    @atomic_transaction()
    async def reset_password(self, email: str, new_password: str) -> bool:
        """重置密码 - 带原子性事务"""
        user = (await self.db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        hashed_new_password = self._hash_password(new_password)
        await self.db.execute(
            update(User).where(User.email == email).values(hashed_password=hashed_new_password)
        )
        await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_user_cache(user.id)
        await cache_service.delete_pattern(f"user:username:*")

        return True

    async def get_user_stats(self, user_id: int) -> Dict:
        """获取用户统计信息 - 带缓存"""
        cache_key = f"user:stats:{user_id}"
        
        # 尝试从缓存获取
        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            return cached_stats

        # 从数据库计算统计信息
        stats = {
            "user_id": user_id,
            "total_posts": 0,  # 需要关联其他表
            "total_followers": 0,
            "total_following": 0,
            "total_likes": 0,
            "total_comments": 0
        }

        # 缓存统计信息
        await cache_service.set(cache_key, stats, ttl=1800)

        return stats

    @atomic_transaction()
    async def update_user_balance(self, user_id: int, amount: int, operation: str) -> bool:
        """更新用户余额 - 带分布式锁"""
        # 这里可以实现用户余额更新逻辑
        # 使用分布式锁确保并发安全
        return True
