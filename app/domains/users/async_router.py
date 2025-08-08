"""
异步用户API路由
领域性接口设计，遵循RESTful规范
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.domains.users.async_service import UserAsyncService
from app.domains.users.schemas import (
    UserCreateRequest, UserUpdateRequest, UserPasswordVerifyRequest,
    UserLoginIdentifierRequest, PasswordChangeRequest, UserBlockRequest, UserListQuery,
    UserInfo, UserWalletInfo, UserBlockInfo, UserByIdentifierResponse, UserQuery
)
from app.common.response import SuccessResponse, PaginationResponse, ErrorResponse, handle_business_error, handle_system_error, handle_not_found_error
from app.common.dependencies import get_current_user_id, get_optional_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])


# ==================== 内部服务接口（供认证服务调用） ====================

@router.post("/internal/create", response_model=SuccessResponse[UserInfo], summary="创建用户", tags=["内部接口"])
async def create_user_internal(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建用户接口（供认证服务内部调用）
    
    - **username**: 用户名（3-50位，只能包含字母、数字、下划线）
    - **nickname**: 昵称（1-100位）
    - **password**: 密码（可选，支持第三方登录）
    - **email**: 邮箱（可选）
    - **phone**: 手机号（可选）
    - **role**: 用户角色（可选）
    - **invite_code**: 邀请码（可选）
    """
    try:
        user_service = UserAsyncService(db)
        user_info = await user_service.create_user(request)
        return SuccessResponse.create(data=user_info, message="用户创建成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"用户创建失败: {str(e)}")
        return handle_system_error("用户创建失败，请稍后重试")


@router.post("/internal/verify-password", response_model=SuccessResponse[bool], summary="验证用户密码", tags=["内部接口"])
async def verify_password_internal(
    request: UserPasswordVerifyRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    验证用户密码接口（供认证服务内部调用）
    
    - **login_identifier**: 登录标识（用户名/邮箱/手机号）
    - **password**: 密码
    """
    try:
        user_service = UserAsyncService(db)
        is_valid = await user_service.verify_user_password(request)
        return SuccessResponse.create(data=is_valid, message="密码验证完成")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return handle_system_error("密码验证失败，请稍后重试")


@router.post("/internal/find-by-identifier", response_model=SuccessResponse[Optional[UserByIdentifierResponse]], summary="根据登录标识查找用户", tags=["内部接口"])
async def find_user_by_identifier_internal(
    request: UserLoginIdentifierRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    根据登录标识查找用户接口（供认证服务内部调用）
    
    - **login_identifier**: 登录标识（用户名/邮箱/手机号）
    """
    try:
        user_service = UserAsyncService(db)
        user_info = await user_service.get_user_by_login_identifier(request)
        return SuccessResponse.create(data=user_info, message="用户查询完成")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"用户查询失败: {str(e)}")
        return handle_system_error("用户查询失败，请稍后重试")


@router.post("/internal/update-login-info/{user_id}", response_model=SuccessResponse[bool], summary="更新用户登录信息", tags=["内部接口"])
async def update_login_info_internal(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新用户登录信息接口（供认证服务内部调用）
    
    - **user_id**: 用户ID
    """
    try:
        user_service = UserAsyncService(db)
        success = await user_service.update_login_info(user_id)
        return SuccessResponse.create(data=success, message="登录信息更新完成")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"登录信息更新失败: {str(e)}")
        return handle_system_error("登录信息更新失败，请稍后重试")


# ==================== 调试接口 ====================

@router.get("/debug/headers", summary="调试请求头信息", tags=["调试"])
async def debug_headers(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_username: Optional[str] = Header(None, alias="X-Username"),  
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
):
    """
    调试接口：查看请求头中的用户信息
    """
    headers_info = {
        "X-User-Id": x_user_id,
        "X-Username": x_username,
        "X-User-Role": x_user_role,
        "all_headers": dict(request.headers)
    }
    return SuccessResponse.create(data=headers_info, message="请求头信息")


# ==================== 用户管理接口 ====================

@router.get("/me", response_model=SuccessResponse[UserInfo], summary="获取当前用户信息")
async def get_current_user_info(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取当前用户信息
    
    需要用户登录，从请求头获取用户ID
    """
    try:
        user_service = UserAsyncService(db)
        user_info = await user_service.get_user_by_id(current_user_id)
        return SuccessResponse.create(data=user_info, message="获取用户信息成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return handle_system_error("获取用户信息失败，请稍后重试")


@router.put("/me", response_model=SuccessResponse[UserInfo], summary="更新当前用户信息")
async def update_current_user_info(
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    更新当前用户信息
    
    需要用户登录，从请求头获取用户ID
    """
    try:
        user_service = UserAsyncService(db)
        user_info = await user_service.update_user_info(current_user_id, request)
        return SuccessResponse.create(data=user_info, message="用户信息更新成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        return handle_system_error("更新用户信息失败，请稍后重试")


@router.get("/{user_id}", response_model=SuccessResponse[UserInfo], summary="获取指定用户信息")
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_context: Optional[UserContext] = Depends(get_optional_user_context)
):
    """
    获取指定用户信息
    
    - **user_id**: 用户ID
    """
    try:
        user_service = UserAsyncService(db)
        user_info = await user_service.get_user_by_id(user_id)
        return SuccessResponse.create(data=user_info, message="获取用户信息成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return handle_system_error("获取用户信息失败，请稍后重试")


@router.get("/", response_model=PaginationResponse[UserInfo], summary="获取用户列表")
async def get_user_list(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id),
    # 查询参数
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/昵称/邮箱）"),
    role: Optional[str] = Query(None, description="用户角色"),
    status: Optional[str] = Query(None, description="用户状态"),
    # 分页参数（统一依赖）
    pagination: PaginationParams = Depends(get_pagination)
):
    """
    获取用户列表
    
    需要用户登录，支持分页和筛选
    """
    try:
        user_service = UserAsyncService(db)
        
        # 构建查询参数
        query = UserQuery(
            username=keyword if keyword else None,
            nickname=keyword if keyword else None,
            status=status
        )
        
        result = await user_service.get_user_list(query, pagination)
        return PaginationResponse.create(
            items=result.items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            message="获取用户列表成功"
        )
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return handle_system_error("获取用户列表失败，请稍后重试")


# ==================== 钱包相关接口 ====================

@router.get("/me/wallet", response_model=SuccessResponse[UserWalletInfo], summary="获取当前用户钱包信息")
async def get_current_user_wallet(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取当前用户钱包信息
    
    需要用户登录，从请求头获取用户ID
    """
    try:
        user_service = UserAsyncService(db)
        wallet_info = await user_service.get_user_wallet(current_user_id)
        return SuccessResponse.create(data=wallet_info, message="获取钱包信息成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"获取钱包信息失败: {str(e)}")
        return handle_system_error("获取钱包信息失败，请稍后重试")


@router.get("/{user_id}/wallet", response_model=SuccessResponse[UserWalletInfo], summary="获取指定用户钱包信息")
async def get_user_wallet_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取指定用户钱包信息
    
    - **user_id**: 用户ID
    """
    try:
        user_service = UserAsyncService(db)
        wallet_info = await user_service.get_user_wallet(user_id)
        return SuccessResponse.create(data=wallet_info, message="获取钱包信息成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"获取钱包信息失败: {str(e)}")
        return handle_system_error("获取钱包信息失败，请稍后重试")


# ==================== 用户管理接口 ====================

@router.post("/block", response_model=SuccessResponse[UserBlockInfo], summary="拉黑用户")
async def block_user(
    request: UserBlockRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    拉黑用户
    
    - **blocked_user_id**: 被拉黑用户ID
    - **reason**: 拉黑原因（可选）
    """
    try:
        user_service = UserAsyncService(db)
        block_info = await user_service.block_user(current_user_id, request.blocked_user_id, request.reason)
        return SuccessResponse.create(data=block_info, message="用户拉黑成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"拉黑用户失败: {str(e)}")
        return handle_system_error("拉黑用户失败，请稍后重试")


@router.delete("/block/{blocked_user_id}", response_model=SuccessResponse[bool], summary="取消拉黑用户")
async def unblock_user(
    blocked_user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    取消拉黑用户
    
    - **blocked_user_id**: 被拉黑用户ID
    """
    try:
        user_service = UserAsyncService(db)
        success = await user_service.unblock_user(current_user_id, blocked_user_id)
        return SuccessResponse.create(data=success, message="取消拉黑成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"取消拉黑失败: {str(e)}")
        return handle_system_error("取消拉黑失败，请稍后重试")


@router.get("/block/list", response_model=PaginationResponse[UserBlockInfo], summary="获取拉黑用户列表")
async def get_block_list(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id),
    # 分页参数（统一依赖）
    pagination: PaginationParams = Depends(get_pagination)
):
    """
    获取拉黑用户列表
    
    需要用户登录，支持分页
    """
    try:
        user_service = UserAsyncService(db)
        result = await user_service.get_block_list(current_user_id, pagination)
        return PaginationResponse.create(
            items=result.items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            message="获取拉黑列表成功"
        )
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"获取拉黑列表失败: {str(e)}")
        return handle_system_error("获取拉黑列表失败，请稍后重试")


# ==================== 密码管理接口 ====================

@router.post("/change-password", response_model=SuccessResponse[bool], summary="修改密码")
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    修改密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码
    """
    try:
        user_service = UserAsyncService(db)
        success = await user_service.change_password(current_user_id, request.old_password, request.new_password)
        return SuccessResponse.create(data=success, message="密码修改成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"密码修改失败: {str(e)}")
        return handle_system_error("密码修改失败，请稍后重试")
