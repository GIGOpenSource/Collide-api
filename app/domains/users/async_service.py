"""
异步用户服务层
处理用户相关的业务逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, select, update, delete, func
from sqlalchemy.orm import selectinload

from app.domains.users.models import User, UserWallet, UserBlock
from app.domains.users.schemas import (
    UserCreateRequest, UserUpdateRequest, UserPasswordVerifyRequest,
    UserLoginIdentifierRequest, PasswordChangeRequest, UserBlockRequest, UserListQuery,
    UserInfo, UserWalletInfo, UserBlockInfo, UserByIdentifierResponse
)
from app.common.security import security_manager
from app.common.exceptions import (
    UserNotFoundError, UserAlreadyExistsError, InvalidCredentialsError,
    BusinessException
)
from app.common.pagination import PaginationParams, PaginationResult
from app.common.cache_service import get_cache_service
import secrets
import string
import logging

logger = logging.getLogger(__name__)


class AsyncUserService:
    """异步用户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_service = get_cache_service()
    
    # ==================== 用户创建管理 ====================
    
    async def create_user(self, request: UserCreateRequest) -> UserInfo:
        """创建用户（由认证服务调用）"""
        # 检查用户名是否已存在
        if await self._check_username_exists(request.username):
            raise UserAlreadyExistsError("用户名已存在")
        
        # 检查邮箱是否已存在
        if request.email and await self._check_email_exists(request.email):
            raise UserAlreadyExistsError("邮箱已被注册")
        
        # 检查手机号是否已存在
        if request.phone and await self._check_phone_exists(request.phone):
            raise UserAlreadyExistsError("手机号已被注册")
        
        # 验证邀请码（如果提供）
        inviter_id = None
        if request.invite_code:
            inviter = await self._get_user_by_invite_code(request.invite_code)
            if not inviter:
                raise BusinessException("邀请码无效")
            inviter_id = inviter.id
        
        # 加密密码（如果提供）
        password_hash = None
        if request.password:
            password_hash = security_manager.hash_password(request.password)
        
        # 生成邀请码
        invite_code = await self._generate_invite_code()
        
        # 创建用户
        user = User(
            username=request.username,
            nickname=request.nickname,
            email=request.email,
            phone=request.phone,
            password_hash=password_hash,
            invite_code=invite_code,
            inviter_id=inviter_id,
            role=request.role or "user"
        )
        
        self.db.add(user)
        await self.db.flush()  # 获取用户ID
        
        # 创建用户钱包
        wallet = UserWallet(user_id=user.id)
        self.db.add(wallet)
        
        # 如果有邀请人，更新邀请人的邀请数量
        if inviter_id:
            await self._increment_inviter_count(inviter_id)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return UserInfo.model_validate(user)
    
    async def get_user_info(self, user_id: int) -> UserInfo:
        """获取用户信息（带缓存）"""
        # 先尝试从缓存获取
        cached_user = await self.cache_service.get_user_info(user_id)
        if cached_user:
            try:
                return UserInfo.model_validate(cached_user)
            except Exception as e:
                # 如果缓存数据验证失败，清除缓存并从数据库重新加载
                logger.warning(f"缓存用户信息验证失败，清除缓存 user_id={user_id}: {e}")
                await self.cache_service.delete_user_info(user_id)
        
        # 缓存未命中，从数据库查询
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError("用户不存在")
        
        # 记录数据库中的原始用户数据
        logger.info(f"数据库用户数据 user_id={user_id}, gender={user.gender}, type={type(user.gender)}")
        
        user_info = UserInfo.model_validate(user)
        
        # 记录验证后的用户信息
        logger.info(f"验证后用户信息 user_id={user_id}, gender={user_info.gender}")
        
        # 将结果缓存
        await self.cache_service.set_user_info(user_id, user_info.model_dump())
        
        return user_info
    
    async def update_user_info(self, user_id: int, request: UserUpdateRequest) -> UserInfo:
        """更新用户信息"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError("用户不存在")
        
        # 更新字段
        if request.nickname is not None:
            user.nickname = request.nickname
        if request.avatar is not None:
            user.avatar = request.avatar
        if request.bio is not None:
            user.bio = request.bio
        if request.birthday is not None:
            user.birthday = request.birthday
        if request.gender is not None:
            user.gender = request.gender
        
        # 检查邮箱唯一性
        if request.email is not None and request.email != user.email:
            if await self._check_email_exists(request.email):
                raise UserAlreadyExistsError("邮箱已被注册")
            user.email = request.email
        
        # 检查手机号唯一性
        if request.phone is not None and request.phone != user.phone:
            if await self._check_phone_exists(request.phone):
                raise UserAlreadyExistsError("手机号已被注册")
            user.phone = request.phone
        
        user.update_time = datetime.now()
        await self.db.commit()
        await self.db.refresh(user)
        
        # 清理缓存
        await self.cache_service.delete_user_info(user_id)
        
        user_info = UserInfo.model_validate(user)
        
        # 重新缓存
        await self.cache_service.set_user_info(user_id, user_info.model_dump())
        
        return user_info
    
    async def get_user_list(self, query: UserListQuery, pagination: PaginationParams) -> PaginationResult[UserInfo]:
        """获取用户列表"""
        stmt = select(User)
        
        # 应用过滤条件
        if query.keyword:
            stmt = stmt.where(
                or_(
                    User.username.like(f"%{query.keyword}%"),
                    User.nickname.like(f"%{query.keyword}%"),
                    User.email.like(f"%{query.keyword}%")
                )
            )
        
        if query.role:
            stmt = stmt.where(User.role == query.role)
        
        if query.status is not None:
            stmt = stmt.where(User.status == query.status)
        
        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # 应用分页和排序
        stmt = stmt.order_by(User.create_time.desc())
        stmt = stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        user_list = [UserInfo.model_validate(user) for user in users]
        
        return PaginationResult(
            items=user_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    # ==================== 认证相关方法（供认证服务调用） ====================
    
    async def verify_user_password(self, request: UserPasswordVerifyRequest) -> bool:
        """验证用户密码（供认证服务调用）"""
        user = await self._get_user_by_login_identifier(request.login_identifier)
        if not user:
            return False
        
        if not user.password_hash:
            return False
        
        return security_manager.verify_password(request.password, user.password_hash)
    
    async def get_user_by_login_identifier(self, request: UserLoginIdentifierRequest) -> Optional[UserByIdentifierResponse]:
        """根据登录标识获取用户（供认证服务调用）"""
        user = await self._get_user_by_login_identifier(request.login_identifier)
        if not user:
            return None
        
        return UserByIdentifierResponse(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            role=user.role,
            status=user.status,
            password_hash=user.password_hash
        )
    
    async def update_login_info(self, user_id: int) -> bool:
        """更新用户登录信息（供认证服务调用）"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_time=datetime.now(),
                login_count=User.login_count + 1
            )
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    # ==================== 钱包相关方法 ====================
    
    async def get_user_wallet(self, user_id: int) -> UserWalletInfo:
        """获取用户钱包信息"""
        stmt = select(UserWallet).where(UserWallet.user_id == user_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise BusinessException("钱包不存在")
        
        return UserWalletInfo.model_validate(wallet)
    
    # ==================== 私有辅助方法 ====================
    
    async def _check_username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        stmt = select(User.id).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def _check_email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        stmt = select(User.id).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def _check_phone_exists(self, phone: str) -> bool:
        """检查手机号是否存在"""
        stmt = select(User.id).where(User.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def _get_user_by_invite_code(self, invite_code: str) -> Optional[User]:
        """根据邀请码获取用户"""
        stmt = select(User).where(User.invite_code == invite_code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_by_login_identifier(self, identifier: str) -> Optional[User]:
        """根据登录标识获取用户"""
        stmt = select(User).where(
            or_(
                User.username == identifier,
                User.email == identifier,
                User.phone == identifier
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _generate_invite_code(self) -> str:
        """生成唯一的邀请码"""
        while True:
            # 生成8位随机邀请码
            invite_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            
            # 检查是否已存在
            stmt = select(User.id).where(User.invite_code == invite_code)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none() is None:
                return invite_code
    
    async def _increment_inviter_count(self, inviter_id: int):
        """增加邀请人的邀请数量"""
        stmt = (
            update(User)
            .where(User.id == inviter_id)
            .values(invited_count=User.invited_count + 1)
        )
        await self.db.execute(stmt)
