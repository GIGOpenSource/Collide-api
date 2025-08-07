"""
异步用户服务层
处理用户相关的业务逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, select, update, delete
from sqlalchemy.orm import selectinload

from app.database.models import User, UserWallet, UserBlock
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
import secrets
import string


class UserService:
    """异步用户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 用户创建管理 ====================
    
    async def create_user(self, request: UserCreateRequest) -> UserInfo:
        """创建用户（由认证服务调用）"""
        # 检查用户名是否已存在
        if self._check_username_exists(request.username):
            raise UserAlreadyExistsError("用户名已存在")
        
        # 检查邮箱是否已存在
        if request.email and self._check_email_exists(request.email):
            raise UserAlreadyExistsError("邮箱已被注册")
        
        # 检查手机号是否已存在
        if request.phone and self._check_phone_exists(request.phone):
            raise UserAlreadyExistsError("手机号已被注册")
        
        # 验证邀请码（如果提供）
        inviter_id = None
        if request.invite_code:
            inviter = self._get_user_by_invite_code(request.invite_code)
            if not inviter:
                raise BusinessException("邀请码无效")
            inviter_id = inviter.id
        
        # 加密密码（如果提供）
        password_hash = None
        if request.password:
            password_hash = security_manager.hash_password(request.password)
        
        # 生成邀请码
        invite_code = self._generate_invite_code()
        
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
        self.db.flush()  # 获取用户ID
        
        # 创建用户钱包
        wallet = UserWallet(user_id=user.id)
        self.db.add(wallet)
        
        # 如果有邀请人，更新邀请人的邀请数量
        if inviter_id:
            self._update_inviter_count(inviter_id)
        
        self.db.commit()
        self.db.refresh(user)
        
        return UserInfo.model_validate(user)
    
    def verify_user_password(self, user_id: int, password: str) -> bool:
        """验证用户密码（供认证服务调用）"""
        user = self._get_user_by_id(user_id)
        
        if not user.password_hash:
            return False
        
        return security_manager.verify_password(password, user.password_hash)
    
    def update_login_info(self, user_id: int) -> bool:
        """更新用户登录信息（供认证服务调用）"""
        user = self._get_user_by_id(user_id)
        
        user.last_login_time = datetime.utcnow()
        user.login_count += 1
        
        self.db.commit()
        return True
    
    def get_user_by_login_identifier(self, request: UserLoginIdentifierRequest) -> UserByIdentifierResponse:
        """根据登录标识符查找用户（供认证服务调用）"""
        user = self._get_user_by_login_identifier(request.identifier)
        
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
    
    # ==================== 用户信息管理 ====================
    
    def get_user_info(self, user_id: int) -> UserInfo:
        """获取用户信息"""
        user = self._get_user_by_id(user_id)
        return UserInfo.model_validate(user)
    
    def update_user_info(self, user_id: int, request: UserUpdateRequest) -> UserInfo:
        """更新用户信息"""
        user = self._get_user_by_id(user_id)
        
        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return UserInfo.model_validate(user)
    
    def change_password(self, user_id: int, request: PasswordChangeRequest) -> bool:
        """修改密码"""
        user = self._get_user_by_id(user_id)
        
        # 验证原密码
        if not security_manager.verify_password(request.old_password, user.password_hash):
            raise InvalidCredentialsError("原密码错误")
        
        # 更新密码
        user.password_hash = security_manager.hash_password(request.new_password)
        self.db.commit()
        
        return True
    
    # ==================== 用户钱包管理 ====================
    
    def get_user_wallet(self, user_id: int) -> UserWalletInfo:
        """获取用户钱包信息"""
        wallet = self.db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
        if not wallet:
            # 如果钱包不存在，创建一个
            wallet = UserWallet(user_id=user_id)
            self.db.add(wallet)
            self.db.commit()
            self.db.refresh(wallet)
        
        return UserWalletInfo.model_validate(wallet)
    
    def grant_coin_reward(self, user_id: int, amount: int, source: str = "system") -> bool:
        """发放金币奖励"""
        # 确保用户存在
        self._get_user_by_id(user_id)
        
        # 获取或创建钱包
        wallet = self.db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
        if not wallet:
            wallet = UserWallet(user_id=user_id)
            self.db.add(wallet)
            self.db.flush()
        
        # 更新金币余额
        wallet.coin_balance += amount
        wallet.coin_total_earned += amount
        
        self.db.commit()
        return True
    
    def consume_coin(self, user_id: int, amount: int, reason: str = "consumption") -> bool:
        """消费金币"""
        wallet = self.db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
        if not wallet:
            raise BusinessException("用户钱包不存在")
        
        if wallet.coin_balance < amount:
            raise BusinessException("金币余额不足")
        
        # 扣减金币
        wallet.coin_balance -= amount
        wallet.coin_total_spent += amount
        
        self.db.commit()
        return True
    
    # ==================== 用户拉黑管理 ====================
    
    def block_user(self, user_id: int, request: UserBlockRequest) -> UserBlockInfo:
        """拉黑用户"""
        # 检查是否已经拉黑
        existing_block = self.db.query(UserBlock).filter(
            and_(
                UserBlock.user_id == user_id,
                UserBlock.blocked_user_id == request.blocked_user_id,
                UserBlock.status == 'active'
            )
        ).first()
        
        if existing_block:
            raise BusinessException("该用户已被拉黑")
        
        # 获取用户信息
        user = self._get_user_by_id(user_id)
        blocked_user = self._get_user_by_id(request.blocked_user_id)
        
        # 创建拉黑记录
        user_block = UserBlock(
            user_id=user_id,
            blocked_user_id=request.blocked_user_id,
            user_username=user.username,
            blocked_username=blocked_user.username,
            reason=request.reason
        )
        
        self.db.add(user_block)
        self.db.commit()
        self.db.refresh(user_block)
        
        return UserBlockInfo.model_validate(user_block)
    
    def unblock_user(self, user_id: int, blocked_user_id: int) -> bool:
        """取消拉黑"""
        user_block = self.db.query(UserBlock).filter(
            and_(
                UserBlock.user_id == user_id,
                UserBlock.blocked_user_id == blocked_user_id,
                UserBlock.status == 'active'
            )
        ).first()
        
        if not user_block:
            raise BusinessException("拉黑记录不存在")
        
        user_block.status = 'cancelled'
        self.db.commit()
        
        return True
    
    def get_blocked_users(self, user_id: int, pagination: PaginationParams) -> PaginationResult[UserBlockInfo]:
        """获取拉黑用户列表"""
        query = self.db.query(UserBlock).filter(
            and_(UserBlock.user_id == user_id, UserBlock.status == 'active')
        ).order_by(UserBlock.create_time.desc())
        
        total = query.count()
        items = query.offset(pagination.offset).limit(pagination.limit).all()
        
        block_infos = [UserBlockInfo.model_validate(item) for item in items]
        
        return PaginationResult.create(
            items=block_infos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    # ==================== 用户列表查询 ====================
    
    def get_user_list(self, query_params: UserListQuery) -> PaginationResult[UserInfo]:
        """获取用户列表"""
        query = self.db.query(User)
        
        # 关键词搜索
        if query_params.keyword:
            keyword = f"%{query_params.keyword}%"
            query = query.filter(
                or_(
                    User.username.like(keyword),
                    User.nickname.like(keyword)
                )
            )
        
        # 角色筛选
        if query_params.role:
            query = query.filter(User.role == query_params.role)
        
        # 状态筛选
        if query_params.status:
            query = query.filter(User.status == query_params.status)
        
        # 排序
        query = query.order_by(User.create_time.desc())
        
        # 分页
        total = query.count()
        pagination = PaginationParams(page=query_params.page, page_size=query_params.page_size)
        items = query.offset(pagination.offset).limit(pagination.limit).all()
        
        user_infos = [UserInfo.model_validate(item) for item in items]
        
        return PaginationResult.create(
            items=user_infos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    
    # ==================== 私有辅助方法 ====================
    
    def _get_user_by_id(self, user_id: int) -> User:
        """根据ID获取用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError()
        return user
    
    def _check_username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        return self.db.query(User).filter(User.username == username).first() is not None
    
    def _check_email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def _check_phone_exists(self, phone: str) -> bool:
        """检查手机号是否存在"""
        return self.db.query(User).filter(User.phone == phone).first() is not None
    
    def _get_user_by_login_identifier(self, identifier: str) -> Optional[User]:
        """根据登录标识符获取用户（用户名/邮箱/手机号）"""
        return self.db.query(User).filter(
            or_(
                User.username == identifier,
                User.email == identifier,
                User.phone == identifier
            )
        ).first()
    
    def _get_user_by_invite_code(self, invite_code: str) -> Optional[User]:
        """根据邀请码获取用户"""
        return self.db.query(User).filter(User.invite_code == invite_code).first()
    
    def _generate_invite_code(self) -> str:
        """生成唯一邀请码"""
        while True:
            # 生成8位随机字符串（字母和数字）
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            
            # 检查是否已存在
            if not self.db.query(User).filter(User.invite_code == code).first():
                return code
    
    def _update_inviter_count(self, inviter_id: int) -> None:
        """更新邀请人的邀请数量"""
        inviter = self.db.query(User).filter(User.id == inviter_id).first()
        if inviter:
            inviter.invited_count += 1