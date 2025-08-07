"""
异步用户API路由
领域性接口设计，遵循RESTful规范
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.domains.users.async_service import AsyncUserService
from app.domains.users.schemas import (
    UserCreateRequest, UserUpdateRequest, UserPasswordVerifyRequest,
    UserLoginIdentifierRequest, PasswordChangeRequest, UserBlockRequest, UserListQuery,
    UserInfo, UserWalletInfo, UserBlockInfo, UserByIdentifierResponse
)
from app.common.response import SuccessResponse, PaginationResponse, ErrorResponse
from app.common.dependencies import get_current_user_id, get_optional_user_context, UserContext
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
        user_service = AsyncUserService(db)
        user_info = await user_service.create_user(request)
        return SuccessResponse.create(data=user_info, message="用户创建成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"用户创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户创建失败，请稍后重试")


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
        user_service = AsyncUserService(db)
        is_valid = await user_service.verify_user_password(request)
        return SuccessResponse.create(data=is_valid, message="密码验证完成")
    
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail="密码验证失败，请稍后重试")


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
        user_service = AsyncUserService(db)
        user_info = await user_service.get_user_by_login_identifier(request)
        return SuccessResponse.create(data=user_info, message="用户查询完成")
    
    except Exception as e:
        logger.error(f"用户查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户查询失败，请稍后重试")


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
        user_service = AsyncUserService(db)
        success = await user_service.update_login_info(user_id)
        return SuccessResponse.create(data=success, message="登录信息更新完成")
    
    except Exception as e:
        logger.error(f"登录信息更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登录信息更新失败，请稍后重试")


# ==================== 用户信息管理接口 ====================

@router.get("/me", response_model=SuccessResponse[UserInfo], summary="获取当前用户信息")
async def get_current_user_info(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取当前登录用户的详细信息"""
    try:
        user_service = AsyncUserService(db)
        user_info = await user_service.get_user_info(current_user_id)
        return SuccessResponse.create(data=user_info)
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


@router.put("/me", response_model=SuccessResponse[UserInfo], summary="更新当前用户信息")
async def update_current_user_info(
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新当前登录用户的信息"""
    try:
        user_service = AsyncUserService(db)
        user_info = await user_service.update_user_info(current_user_id, request)
        return SuccessResponse.create(data=user_info, message="用户信息更新成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"用户信息更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户信息更新失败")


@router.get("/{user_id}", response_model=SuccessResponse[UserInfo], summary="获取指定用户信息")
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_context: Optional[UserContext] = Depends(get_optional_user_context)
):
    """获取指定用户的公开信息"""
    try:
        user_service = AsyncUserService(db)
        user_info = await user_service.get_user_info(user_id)
        
        # 如果不是本人查看，隐藏部分敏感信息
        current_user_id = current_user_context.user_id if current_user_context else None
        if current_user_id != user_id:
            user_info.email = None
            user_info.phone = None
        
        return SuccessResponse.create(data=user_info)
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


@router.get("", response_model=PaginationResponse[UserInfo], summary="获取用户列表")
async def get_user_list(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id),
    # 查询参数
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/昵称/邮箱）"),
    role: Optional[str] = Query(None, description="用户角色"),
    status: Optional[int] = Query(None, description="用户状态"),
    # 分页参数
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取用户列表（分页）"""
    try:
        pagination = PaginationParams(page=page, page_size=page_size)
        query = UserListQuery(keyword=keyword, role=role, status=status)
        
        user_service = AsyncUserService(db)
        result = await user_service.get_user_list(query, pagination)
        
        return PaginationResponse.create(
            datas=result.items,
            total=result.total,
            current_page=result.page,
            page_size=result.page_size,
            message="获取用户列表成功"
        )
    
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


# ==================== 用户钱包管理接口 ====================

@router.get("/me/wallet", response_model=SuccessResponse[UserWalletInfo], summary="获取当前用户钱包信息")
async def get_current_user_wallet(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取当前用户的钱包信息"""
    try:
        user_service = AsyncUserService(db)
        wallet_info = await user_service.get_user_wallet(current_user_id)
        return SuccessResponse.create(data=wallet_info)
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取钱包信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取钱包信息失败")


@router.get("/{user_id}/wallet", response_model=SuccessResponse[UserWalletInfo], summary="获取指定用户钱包信息")
async def get_user_wallet_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取指定用户的钱包信息（仅限管理员或本人）"""
    try:
        # TODO: 添加权限检查，只有管理员或本人才能查看
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问他人钱包信息")
        
        user_service = AsyncUserService(db)
        wallet_info = await user_service.get_user_wallet(user_id)
        return SuccessResponse.create(data=wallet_info)
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取钱包信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取钱包信息失败")
