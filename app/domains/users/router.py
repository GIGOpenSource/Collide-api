"""
用户API路由
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
    db: Session = Depends(get_db)
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
        user_service = UserService(db)
        user_info = user_service.create_user(request)
        return SuccessResponse.create(data=user_info, message="用户创建成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"用户创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户创建失败，请稍后重试")


@router.post("/internal/verify-password", response_model=SuccessResponse[bool], summary="验证用户密码", tags=["内部接口"])
async def verify_user_password_internal(
    request: UserPasswordVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    验证用户密码接口（供认证服务内部调用）
    
    - **user_id**: 用户ID
    - **password**: 密码
    """
    try:
        user_service = UserService(db)
        is_valid = user_service.verify_user_password(request.user_id, request.password)
        return SuccessResponse.create(data=is_valid, message="密码验证完成")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail="密码验证失败")


@router.post("/internal/find-by-identifier", response_model=SuccessResponse[UserByIdentifierResponse], summary="根据登录标识符查找用户", tags=["内部接口"])
async def find_user_by_identifier_internal(
    request: UserLoginIdentifierRequest,
    db: Session = Depends(get_db)
):
    """
    根据登录标识符查找用户（供认证服务内部调用）
    
    - **identifier**: 用户名/邮箱/手机号
    """
    try:
        user_service = UserService(db)
        result = user_service.get_user_by_login_identifier(request)
        return SuccessResponse.create(data=result, message="查询完成")
    
    except Exception as e:
        logger.error(f"查找用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="查找用户失败")


@router.post("/internal/update-login-info/{user_id}", response_model=SuccessResponse[bool], summary="更新登录信息", tags=["内部接口"])
async def update_login_info_internal(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    更新用户登录信息（供认证服务内部调用）
    
    - **user_id**: 用户ID
    """
    try:
        user_service = UserService(db)
        result = user_service.update_login_info(user_id)
        return SuccessResponse.create(data=result, message="登录信息更新成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"更新登录信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新登录信息失败")


# ==================== 用户信息管理 ====================

@router.get("/me", response_model=SuccessResponse[UserInfo], summary="获取当前用户信息")
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取当前登录用户的详细信息"""
    try:
        user_service = UserService(db)
        user_info = user_service.get_user_info(current_user_id)
        return SuccessResponse.create(data=user_info)
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


@router.get("/{user_id}", response_model=SuccessResponse[UserInfo], summary="获取指定用户信息")
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_context: Optional[UserContext] = Depends(get_optional_user_context)
):
    """获取指定用户的公开信息"""
    try:
        user_service = UserService(db)
        user_info = user_service.get_user_info(user_id)
        
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


@router.put("/me", response_model=SuccessResponse[UserInfo], summary="更新用户信息")
async def update_user_info(
    request: UserUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新当前用户的个人信息"""
    try:
        user_service = UserService(db)
        user_info = user_service.update_user_info(current_user_id, request)
        return SuccessResponse.create(data=user_info, message="更新成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新失败，请稍后重试")


@router.put("/password", response_model=SuccessResponse[bool], summary="修改密码")
async def change_password(
    request: PasswordChangeRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """修改用户密码"""
    try:
        user_service = UserService(db)
        result = user_service.change_password(current_user_id, request)
        return SuccessResponse.create(data=result, message="密码修改成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="修改密码失败，请稍后重试")


# ==================== 用户钱包管理 ====================

@router.get("/me/wallet", response_model=SuccessResponse[UserWalletInfo], summary="获取钱包信息")
async def get_user_wallet(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取当前用户的钱包信息"""
    try:
        user_service = UserService(db)
        wallet_info = user_service.get_user_wallet(current_user_id)
        return SuccessResponse.create(data=wallet_info)
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取钱包信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取钱包信息失败")


@router.post("/me/wallet/coin/grant", response_model=SuccessResponse[bool], summary="发放金币奖励")
async def grant_coin_reward(
    amount: int = Query(..., ge=1, description="金币数量"),
    source: str = Query("system", description="奖励来源"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    发放金币奖励（通常由系统调用）
    
    - **amount**: 金币数量（必须大于0）
    - **source**: 奖励来源
    """
    try:
        user_service = UserService(db)
        result = user_service.grant_coin_reward(current_user_id, amount, source)
        return SuccessResponse.create(data=result, message="金币发放成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"发放金币失败: {str(e)}")
        raise HTTPException(status_code=500, detail="发放金币失败")


@router.post("/me/wallet/coin/consume", response_model=SuccessResponse[bool], summary="消费金币")
async def consume_coin(
    amount: int = Query(..., ge=1, description="消费金币数量"),
    reason: str = Query("consumption", description="消费原因"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    消费金币
    
    - **amount**: 消费金币数量（必须大于0）
    - **reason**: 消费原因
    """
    try:
        user_service = UserService(db)
        result = user_service.consume_coin(current_user_id, amount, reason)
        return SuccessResponse.create(data=result, message="金币消费成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"消费金币失败: {str(e)}")
        raise HTTPException(status_code=500, detail="消费金币失败")


# ==================== 用户拉黑管理 ====================

@router.post("/me/blocks", response_model=SuccessResponse[UserBlockInfo], summary="拉黑用户")
async def block_user(
    request: UserBlockRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    拉黑指定用户
    
    - **blocked_user_id**: 被拉黑用户ID
    - **reason**: 拉黑原因（可选）
    """
    try:
        # 不能拉黑自己
        if current_user_id == request.blocked_user_id:
            raise HTTPException(status_code=400, detail="不能拉黑自己")
        
        user_service = UserService(db)
        block_info = user_service.block_user(current_user_id, request)
        return SuccessResponse.create(data=block_info, message="拉黑成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"拉黑用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="拉黑失败，请稍后重试")


@router.delete("/me/blocks/{blocked_user_id}", response_model=SuccessResponse[bool], summary="取消拉黑")
async def unblock_user(
    blocked_user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取消拉黑指定用户"""
    try:
        user_service = UserService(db)
        result = user_service.unblock_user(current_user_id, blocked_user_id)
        return SuccessResponse.create(data=result, message="取消拉黑成功")
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"取消拉黑失败: {str(e)}")
        raise HTTPException(status_code=500, detail="取消拉黑失败")


@router.get("/me/blocks", response_model=PaginationResponse, summary="获取拉黑用户列表")
async def get_blocked_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取当前用户的拉黑用户列表"""
    try:
        user_service = UserService(db)
        pagination = PaginationParams(page=page, page_size=page_size)
        result = user_service.get_blocked_users(current_user_id, pagination)
        
        return PaginationResponse.create(
            datas=result.items,
            total=result.total,
            current_page=result.page,
            page_size=result.page_size,
            message="获取成功"
        )
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取拉黑列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取拉黑列表失败")


# ==================== 用户列表查询 ====================

@router.get("", response_model=PaginationResponse, summary="获取用户列表")
async def get_user_list(
    keyword: str = Query(None, description="搜索关键词（用户名/昵称）"),
    role: str = Query(None, description="用户角色筛选"),
    status: str = Query(None, description="用户状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（支持搜索和筛选）
    
    - **keyword**: 搜索关键词，匹配用户名或昵称
    - **role**: 角色筛选（user/blogger/admin/vip）
    - **status**: 状态筛选（active/inactive/suspended/banned）
    - **page**: 页码
    - **page_size**: 每页大小
    """
    try:
        user_service = UserService(db)
        query_params = UserListQuery(
            keyword=keyword,
            role=role,
            status=status,
            page=page,
            page_size=page_size
        )
        
        result = user_service.get_user_list(query_params)
        
        return PaginationResponse.create(
            datas=result.items,
            total=result.total,
            current_page=result.page,
            page_size=result.page_size,
            message="获取成功"
        )
    
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")