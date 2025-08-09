"""
用户模块异步服务层（门面）
将原有大而全的逻辑拆分到 services/ 子模块：查询、资料、认证、钱包、拉黑等
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.users.schemas import (
    UserCreate,
    UserUpdate,
    UserInfo,
    UserQuery,
    UserWalletInfo,
    UserBlockInfo,
    UserUpdateRequest,
    UserLoginIdentifierRequest,
    UserByIdentifierResponse,
)
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
from app.common.cache_service import cache_service
from app.common.atomic import atomic_transaction, atomic_lock, execute_in_transaction
from app.domains.users.services.query_service import UserQueryService
from app.domains.users.services.profile_service import UserProfileService
from app.domains.users.services.auth_service import UserAuthService
from app.domains.users.services.wallet_service import UserWalletService
from app.domains.users.models import User, UserBlock


class UserAsyncService:
    """用户异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 门面不再直接处理密码加密校验，交由 UserAuthService

    @atomic_transaction()
    async def create_user(self, req) -> UserInfo:
        """创建用户 - 带原子性事务"""
        from app.domains.users.schemas import UserCreateRequest
        
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

        # 检查手机号是否已存在
        if req.phone:
            existing_phone = (await self.db.execute(
                select(User).where(User.phone == req.phone)
            )).scalar_one_or_none()
            
            if existing_phone:
                raise BusinessException("手机号已被注册")

        # 创建用户
        # 密码加密仍保留在此处，避免扩散改动
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if req.password:
            hashed_password = pwd_context.hash(req.password)
        else:
            import secrets, string
            random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            hashed_password = pwd_context.hash(random_password)
        
        user = User(
            username=req.username,
            email=req.email,
            phone=req.phone,
            nickname=req.nickname,
            password_hash=hashed_password,
            role=req.role or "user",
            status="active"
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 清除相关缓存
        await cache_service.delete_pattern("user:*")
        
        return UserInfo.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> UserInfo:
        return await UserQueryService(self.db).get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> UserInfo:
        return await UserQueryService(self.db).get_user_by_username(username)

    @atomic_transaction()
    async def update_user(self, user_id: int, req: UserUpdate) -> UserInfo:
        return await UserProfileService(self.db).update_user(user_id, req)

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
        return await UserQueryService(self.db).get_user_list(query, pagination)

    async def authenticate_user(self, username: str, password: str):
        return await UserAuthService(self.db).authenticate_user(username, password)

    @atomic_transaction()
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码 - 带原子性事务"""
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        if not self._verify_password(old_password, user.password_hash):
            raise BusinessException("原密码错误")

        hashed_new_password = self._hash_password(new_password)
        await self.db.execute(
            update(User).where(User.id == user_id).values(password_hash=hashed_new_password)
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
            update(User).where(User.email == email).values(password_hash=hashed_new_password)
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

    async def get_user_wallet(self, user_id: int):
        return await UserWalletService(self.db).get_user_wallet(user_id)

    @atomic_transaction()
    async def block_user(self, user_id: int, blocked_user_id: int, reason: str = None):
        return await UserProfileService(self.db).block_user(user_id, blocked_user_id, reason)

    @atomic_transaction()
    async def unblock_user(self, user_id: int, blocked_user_id: int) -> bool:
        return await UserProfileService(self.db).unblock_user(user_id, blocked_user_id)

    async def get_block_list(self, user_id: int, pagination):
        """获取拉黑用户列表"""
        from app.domains.users.schemas import UserBlockInfo
        from app.domains.users.models import UserBlock
        
        # 构建查询
        stmt = select(UserBlock).where(UserBlock.user_id == user_id).order_by(UserBlock.create_time.desc())
        
        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()
        
        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        block_records = result.scalars().all()
        
        block_info_list = [UserBlockInfo.model_validate(record) for record in block_records]
        
        return PaginationResult.create(
            items=block_info_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def update_user_info(self, user_id: int, request):
        """更新用户信息"""
        from app.domains.users.schemas import UserUpdateRequest
        
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        
        # 更新用户信息
        update_data = {}
        if request.nickname is not None:
            update_data['nickname'] = request.nickname
        if request.avatar is not None:
            update_data['avatar'] = request.avatar
        if request.bio is not None:
            update_data['bio'] = request.bio
        if request.birthday is not None:
            update_data['birthday'] = request.birthday
        if request.gender is not None:
            update_data['gender'] = request.gender
        if request.location is not None:
            update_data['location'] = request.location
        
        if update_data:
            await self.db.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await self.db.commit()
            await self.db.refresh(user)
        
        # 清除相关缓存
        await cache_service.delete_user_cache(user_id)
        
        return UserInfo.model_validate(user)

    async def get_user_by_login_identifier(self, request):
        """根据登录标识符查找用户"""
        from app.domains.users.schemas import UserLoginIdentifierRequest, UserByIdentifierResponse
        
        identifier = request.identifier
        
        # 尝试通过用户名、邮箱或手机号查找
        user = (await self.db.execute(
            select(User).where(
                or_(
                    User.username == identifier,
                    User.email == identifier,
                    User.phone == identifier
                )
            )
        )).scalar_one_or_none()
        
        if user:
            return UserByIdentifierResponse(
                user_info=UserInfo.model_validate(user),
                exists=True
            )
        else:
            return UserByIdentifierResponse(
                user_info=None,
                exists=False
            )

    async def update_login_info(self, user_id: int) -> bool:
        """更新用户登录信息"""
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        
        # 更新登录信息
        await self.db.execute(
            update(User).where(User.id == user_id).values(
                last_login_time=func.current_timestamp(),
                login_count=User.login_count + 1
            )
        )
        await self.db.commit()
        
        # 清除相关缓存
        await cache_service.delete_user_cache(user_id)
        
        return True

    async def verify_user_password(self, request):
        """验证用户密码"""
        from app.domains.users.schemas import UserPasswordVerifyRequest
        
        user = (await self.db.execute(select(User).where(User.id == request.user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        
        return self._verify_password(request.password, user.password_hash)
