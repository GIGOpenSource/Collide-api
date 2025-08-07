"""
用户相关的Pydantic模型
定义请求体、响应体、DTO等
"""
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, validator
import re


# ==================== 基础用户模型 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    nickname: str = Field(..., min_length=1, max_length=100, description="昵称")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    bio: Optional[str] = Field(None, description="个人简介")
    birthday: Optional[date] = Field(None, description="生日")
    gender: Optional[str] = Field("unknown", description="性别")
    location: Optional[str] = Field(None, max_length=100, description="所在地")
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v not in ['male', 'female', 'unknown']:
            raise ValueError('性别只能是male、female或unknown')
        return v


# ==================== 请求模型 ====================

class UserCreateRequest(BaseModel):
    """用户创建请求（供认证服务调用）"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    nickname: str = Field(..., min_length=1, max_length=100, description="昵称")
    password: Optional[str] = Field(None, min_length=6, max_length=20, description="密码（可选，支持第三方登录）")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    role: Optional[str] = Field("user", description="用户角色")
    invite_code: Optional[str] = Field(None, description="邀请码")
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'blogger', 'admin', 'vip']:
            raise ValueError('用户角色只能是user、blogger、admin或vip')
        return v


class UserPasswordVerifyRequest(BaseModel):
    """用户密码验证请求（供认证服务调用）"""
    user_id: int = Field(..., description="用户ID")
    password: str = Field(..., description="密码")


class UserLoginIdentifierRequest(BaseModel):
    """根据登录标识符查找用户请求"""
    identifier: str = Field(..., description="用户名/邮箱/手机号")


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=100, description="昵称")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    birthday: Optional[date] = Field(None, description="生日")
    gender: Optional[str] = Field(None, description="性别")
    location: Optional[str] = Field(None, max_length=100, description="所在地")
    
    @validator('gender')
    def validate_gender(cls, v):
        if v and v not in ['male', 'female', 'unknown']:
            raise ValueError('性别只能是male、female或unknown')
        return v


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


class UserBlockRequest(BaseModel):
    """用户拉黑请求"""
    blocked_user_id: int = Field(..., description="被拉黑用户ID")
    reason: Optional[str] = Field(None, max_length=200, description="拉黑原因")


# ==================== 响应模型 ====================

class UserInfo(BaseModel):
    """用户信息响应"""
    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    nickname: str = Field(description="昵称")
    avatar: Optional[str] = Field(description="头像URL")
    email: Optional[str] = Field(description="邮箱")
    phone: Optional[str] = Field(description="手机号")
    role: str = Field(description="用户角色")
    status: str = Field(description="用户状态")
    bio: Optional[str] = Field(description="个人简介")
    birthday: Optional[date] = Field(description="生日")
    gender: str = Field(description="性别")
    location: Optional[str] = Field(description="所在地")
    
    # 统计字段
    follower_count: int = Field(description="粉丝数")
    following_count: int = Field(description="关注数")
    content_count: int = Field(description="内容数")
    like_count: int = Field(description="获得点赞数")
    
    # VIP相关
    vip_expire_time: Optional[datetime] = Field(description="VIP过期时间")
    
    # 登录相关
    last_login_time: Optional[datetime] = Field(description="最后登录时间")
    login_count: int = Field(description="登录次数")
    
    # 邀请相关
    invite_code: Optional[str] = Field(description="邀请码")
    invited_count: int = Field(description="邀请人数")
    
    create_time: datetime = Field(description="创建时间")
    
    model_config = {"from_attributes": True}


class UserByIdentifierResponse(BaseModel):
    """根据登录标识符查找用户响应"""
    user_info: Optional[UserInfo] = Field(description="用户信息")
    exists: bool = Field(description="用户是否存在")


class UserWalletInfo(BaseModel):
    """用户钱包信息"""
    user_id: int = Field(description="用户ID")
    balance: Decimal = Field(description="现金余额")
    frozen_amount: Decimal = Field(description="冻结金额")
    coin_balance: int = Field(description="金币余额")
    coin_total_earned: int = Field(description="累计获得金币")
    coin_total_spent: int = Field(description="累计消费金币")
    total_income: Decimal = Field(description="总收入")
    total_expense: Decimal = Field(description="总支出")
    status: str = Field(description="钱包状态")
    
    model_config = {"from_attributes": True}


class UserBlockInfo(BaseModel):
    """用户拉黑信息"""
    id: int = Field(description="拉黑记录ID")
    user_id: int = Field(description="拉黑者用户ID")
    blocked_user_id: int = Field(description="被拉黑用户ID")
    user_username: str = Field(description="拉黑者用户名")
    blocked_username: str = Field(description="被拉黑用户名")
    status: str = Field(description="拉黑状态")
    reason: Optional[str] = Field(description="拉黑原因")
    create_time: datetime = Field(description="拉黑时间")
    
    model_config = {"from_attributes": True}


# ==================== 查询参数模型 ====================

class UserListQuery(BaseModel):
    """用户列表查询参数"""
    keyword: Optional[str] = Field(None, description="搜索关键词（用户名/昵称）")
    role: Optional[str] = Field(None, description="用户角色筛选")
    status: Optional[str] = Field(None, description="用户状态筛选")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")