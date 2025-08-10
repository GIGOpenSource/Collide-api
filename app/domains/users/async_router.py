"""
异步用户API路由（精简版）
仅保留：当前用户信息（查/改）、用户列表筛选（含粉丝/点赞范围）、当前钱包、拉黑/取消拉黑/拉黑列表、修改密码
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.domains.users.async_service import UserAsyncService
from app.domains.users.services.blogger_service import BloggerService
from app.domains.users.schemas import (
    UserUpdateRequest, PasswordChangeRequest, UserBlockRequest,
    UserInfo, UserWalletInfo, UserBlockInfo, UserQuery,
    BloggerApplicationCreate, BloggerApplicationInfo
)
from app.common.response import SuccessResponse, PaginationResponse, handle_business_error, handle_system_error
from app.common.dependencies import get_current_user_id, get_pagination, get_current_user_context, UserContext
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])


# 移除内部/调试接口


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


@router.get("/me/roles", response_model=SuccessResponse[List[str]], summary="获取当前用户角色")
async def get_current_user_roles(
    current_user: UserContext = Depends(get_current_user_context)
):
    """
    获取当前用户的角色列表
    """
    return SuccessResponse.create(data=current_user.roles, message="获取角色成功")


# 移除按ID查询接口（不需要）


@router.get("/", response_model=PaginationResponse[UserInfo], summary="获取用户列表")
async def get_user_list(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id),
    # 查询参数
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/昵称/邮箱）"),
    role: Optional[str] = Query(None, description="用户角色"),
    follower_min: Optional[int] = Query(None, alias="followerMin", ge=0, description="最小粉丝数"),
    follower_max: Optional[int] = Query(None, alias="followerMax", ge=0, description="最大粉丝数"),
    like_min: Optional[int] = Query(None, alias="likeMin", ge=0, description="最小获赞数"),
    like_max: Optional[int] = Query(None, alias="likeMax", ge=0, description="最大获赞数"),
    status: Optional[str] = Query(None, description="用户状态"),
    # 分页参数（统一依赖）
    pagination: PaginationParams = Depends(get_pagination)
):
    """
    获取用户列表
    
    支持按关键词搜索、角色筛选、粉丝数范围、获赞数范围等条件筛选
    需要用户登录，支持分页
    """
    try:
        user_service = UserAsyncService(db)
        # 构建查询参数
        query = UserQuery(
            username=keyword,  # 关键词搜索用户名
            nickname=keyword,  # 关键词搜索昵称
            role=role,
            follower_count_min=follower_min,
            follower_count_max=follower_max,
            like_count_min=like_min,
            like_count_max=like_max,
            status=status
        )
        result = await user_service.get_user_list(query, pagination)
        return PaginationResponse.create(
            datas=result.items,
            total=result.total,
            current_page=result.page,
            page_size=result.page_size,
            message="获取用户列表成功"
        )
    
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取用户列表失败，请稍后重试"
        )


# ==================== 钱包管理接口 ====================

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


# ==================== 拉黑管理接口 ====================

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
            datas=result.items,
            total=result.total,
            current_page=result.page,
            page_size=result.page_size,
            message="获取拉黑列表成功"
        )
    
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取拉黑列表失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取拉黑列表失败，请稍后重试"
        )


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


# ==================== Blogger申请相关接口 ====================

@router.post("/blogger/apply", response_model=SuccessResponse[BloggerApplicationInfo], summary="申请Blogger权限")
async def apply_for_blogger(
    request: BloggerApplicationCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    申请Blogger权限
    
    用户申请成为内容创作者，需要审核通过后才能获得Blogger角色
    """
    try:
        blogger_service = BloggerService(db)
        application = await blogger_service.apply_for_blogger(current_user_id)
        return SuccessResponse.create(data=application, message="Blogger申请提交成功，请等待审核")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"申请Blogger权限失败: {str(e)}")
        return handle_system_error("申请Blogger权限失败，请稍后重试")


@router.get("/blogger/status", response_model=SuccessResponse[BloggerApplicationInfo], summary="查询Blogger申请状态")
async def get_blogger_application_status(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    查询Blogger申请状态
    
    返回当前用户的Blogger申请状态信息
    """
    try:
        blogger_service = BloggerService(db)
        application = await blogger_service.get_application_status(current_user_id)
        return SuccessResponse.create(data=application, message="获取申请状态成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"查询Blogger申请状态失败: {str(e)}")
        return handle_system_error("查询Blogger申请状态失败，请稍后重试")


@router.get("/blogger/check", response_model=SuccessResponse[dict], summary="检查Blogger状态")
async def check_blogger_status(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    检查Blogger状态
    
    返回用户的Blogger状态信息，包括：
    - is_blogger: 是否已经是Blogger
    - application_status: 申请状态（PENDING/APPROVED/REJECTED/null）
    - can_apply: 是否可以申请
    """
    try:
        blogger_service = BloggerService(db)
        status_info = await blogger_service.check_blogger_status(current_user_id)
        return SuccessResponse.create(data=status_info, message="获取Blogger状态成功")
    
    except BusinessException as e:
        return handle_business_error(e.message, e.code)
    except Exception as e:
        logger.error(f"检查Blogger状态失败: {str(e)}")
        return handle_system_error("检查Blogger状态失败，请稍后重试")
