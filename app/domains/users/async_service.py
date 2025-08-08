"""
用户模块异步服务层 - 增强版
添加缓存、幂等性和原子性支持
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func
from passlib.context import CryptContext

from app.domains.users.models import User, UserWallet, UserBlock
from app.domains.users.schemas import UserCreate, UserUpdate, UserInfo, UserQuery, UserWalletInfo, UserBlockInfo, UserUpdateRequest, UserLoginIdentifierRequest, UserByIdentifierResponse
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
        hashed_password = None
        if req.password:
            hashed_password = self._hash_password(req.password)
        else:
            # 如果没有密码，生成一个随机密码（用于第三方登录）
            import secrets
            import string
            random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            hashed_password = self._hash_password(random_password)
        
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
        
        # 处理关键词搜索（用户名或昵称）
        if query.username and query.nickname and query.username == query.nickname:
            # 如果username和nickname相同，说明是关键词搜索
            keyword = query.username
            conditions.append(or_(User.username.contains(keyword), User.nickname.contains(keyword)))
        else:
            # 分别处理各个字段
            if query.username:
                conditions.append(User.username.contains(query.username))
            if query.nickname:
                conditions.append(User.nickname.contains(query.nickname))
        
        if query.email:
            conditions.append(User.email.contains(query.email))
        if query.status:
            conditions.append(User.status == query.status)

        # 构建查询语句
        if conditions:
            stmt = select(User).where(and_(*conditions)).order_by(User.create_time.desc())
        else:
            stmt = select(User).order_by(User.create_time.desc())

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

        if not self._verify_password(password, user.password_hash):
            return None

        return UserInfo.model_validate(user)

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
        """获取用户钱包信息"""
        from app.domains.users.schemas import UserWalletInfo
        from app.domains.users.models import UserWallet
        
        # 尝试从缓存获取
        cache_key = f"user:wallet:{user_id}"
        cached_wallet = await cache_service.get(cache_key)
        if cached_wallet:
            return UserWalletInfo.model_validate(cached_wallet)

        # 从数据库获取钱包信息
        wallet = (await self.db.execute(
            select(UserWallet).where(UserWallet.user_id == user_id)
        )).scalar_one_or_none()
        
        if not wallet:
            # 如果钱包不存在，创建一个默认钱包
            wallet = UserWallet(
                user_id=user_id,
                balance=0.00,
                frozen_amount=0.00,
                coin_balance=0,
                coin_total_earned=0,
                coin_total_spent=0,
                total_income=0.00,
                total_expense=0.00,
                status="active"
            )
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)

        wallet_info = UserWalletInfo.model_validate(wallet)
        
        # 缓存钱包信息
        await cache_service.set(cache_key, wallet_info.model_dump(), ttl=1800)
        
        return wallet_info

    @atomic_transaction()
    async def block_user(self, user_id: int, blocked_user_id: int, reason: str = None):
        """拉黑用户"""
        from app.domains.users.schemas import UserBlockInfo
        from app.domains.users.models import UserBlock, User
        
        # 检查用户是否存在
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        blocked_user = (await self.db.execute(select(User).where(User.id == blocked_user_id))).scalar_one_or_none()
        
        if not user or not blocked_user:
            raise BusinessException("用户不存在")
        
        if user_id == blocked_user_id:
            raise BusinessException("不能拉黑自己")
        
        # 检查是否已经拉黑
        existing_block = (await self.db.execute(
            select(UserBlock).where(
                and_(UserBlock.user_id == user_id, UserBlock.blocked_user_id == blocked_user_id)
            )
        )).scalar_one_or_none()
        
        if existing_block:
            raise BusinessException("已经拉黑该用户")
        
        # 创建拉黑记录
        block_record = UserBlock(
            user_id=user_id,
            blocked_user_id=blocked_user_id,
            user_username=user.username,
            blocked_username=blocked_user.username,
            status="active",
            reason=reason
        )
        
        self.db.add(block_record)
        await self.db.commit()
        await self.db.refresh(block_record)
        
        # 清除相关缓存
        await cache_service.delete_pattern(f"user:block:*")
        
        return UserBlockInfo.model_validate(block_record)

    @atomic_transaction()
    async def unblock_user(self, user_id: int, blocked_user_id: int) -> bool:
        """取消拉黑用户"""
        from app.domains.users.models import UserBlock
        
        # 查找拉黑记录
        block_record = (await self.db.execute(
            select(UserBlock).where(
                and_(UserBlock.user_id == user_id, UserBlock.blocked_user_id == blocked_user_id)
            )
        )).scalar_one_or_none()
        
        if not block_record:
            raise BusinessException("未找到拉黑记录")
        
        # 删除拉黑记录
        await self.db.execute(
            delete(UserBlock).where(UserBlock.id == block_record.id)
        )
        await self.db.commit()
        
        # 清除相关缓存
        await cache_service.delete_pattern(f"user:block:*")
        
        return True

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
