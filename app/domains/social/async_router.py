"""
社交动态模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.pagination import PaginationParams
from app.common.dependencies import get_current_user_context, UserContext, get_pagination, require_vip_or_blogger, require_blogger_for_paid_content
from app.common.exceptions import BusinessException
from app.domains.social.async_service import SocialAsyncService
from app.domains.social.schemas import DynamicCreate, DynamicUpdate, DynamicInfo, DynamicQuery, DynamicReviewStatusInfo, DynamicReviewStatusQuery, DynamicReviewRequest, PaidDynamicCreate, PaidDynamicInfo, DynamicPurchaseRequest, DynamicPurchaseInfo, DynamicWithPaidInfo


router = APIRouter(prefix="/api/v1/social", tags=["社交动态"])


@router.post("/dynamics", response_model=SuccessResponse[DynamicInfo], summary="发布动态")
async def create_dynamic(
    data: DynamicCreate,
    current_user: UserContext = Depends(require_vip_or_blogger),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        info = await service.create_dynamic(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            user_avatar=None,
            data=data,
        )
        return SuccessResponse.create(data=info, message="发布成功，请等待审核通过后显示")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="发布动态失败")


@router.put("/dynamics/{dynamic_id}", response_model=SuccessResponse[DynamicInfo], summary="更新动态")
async def update_dynamic(
    dynamic_id: int,
    data: DynamicUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        info = await service.update_dynamic(dynamic_id, current_user.user_id, data)
        return SuccessResponse.create(data=info, message="更新成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="更新动态失败")


@router.delete("/dynamics/{dynamic_id}", response_model=SuccessResponse[bool], summary="删除动态")
async def delete_dynamic(
    dynamic_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = SocialAsyncService(db)
        ok = await service.delete_dynamic(dynamic_id, current_user.user_id)
        return SuccessResponse.create(data=ok, message="删除成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="删除动态失败")


@router.get("/dynamics/{dynamic_id}", response_model=SuccessResponse[DynamicInfo], summary="获取动态详情")
async def get_dynamic(
    dynamic_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[UserContext] = Depends(get_current_user_context),
):
    try:
        service = SocialAsyncService(db)
        current_user_id = current_user.user_id if current_user else None
        info = await service.get_dynamic_by_id(dynamic_id, current_user_id)
        return SuccessResponse.create(data=info, message="获取成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取动态失败")


@router.get("/dynamics", response_model=PaginationResponse[DynamicInfo], summary="获取动态列表")
async def list_dynamics(
    keyword: Optional[str] = Query(None, description="关键词（内容模糊搜索）"),
    dynamic_type: Optional[str] = Query(None, description="动态类型：text、image、video、share"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤：normal、hidden、deleted"),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[UserContext] = Depends(get_current_user_context),
):
    try:
        service = SocialAsyncService(db)
        query = DynamicQuery(keyword=keyword, dynamic_type=dynamic_type, user_id=user_id, status=status)
        current_user_id = current_user.user_id if current_user else None
        result = await service.list_dynamics(query, pagination, current_user_id)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取动态列表失败")


@router.get("/dynamics/my", response_model=PaginationResponse[DynamicInfo], summary="获取我的动态列表")
async def list_my_dynamics(
    keyword: Optional[str] = Query(None, description="关键词（内容模糊搜索）"),
    dynamic_type: Optional[str] = Query(None, description="动态类型：text、image、video、share"),
    status: Optional[str] = Query(None, description="状态过滤：normal、hidden、deleted"),
    review_status: Optional[str] = Query(None, description="审核状态过滤：PENDING、APPROVED、REJECTED"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取当前用户发布的动态列表
    
    用户可以查看自己发布的所有动态，包括未审核、已审核通过、被拒绝的动态
    """
    try:
        service = SocialAsyncService(db)
        query = DynamicQuery(keyword=keyword, dynamic_type=dynamic_type, user_id=current_user.user_id, status=status)
        result = await service.list_my_dynamics(query, pagination, current_user.user_id, review_status)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取我的动态列表失败")


# ================ 审核状态相关接口 ================

@router.post("/dynamics/review-status", response_model=SuccessResponse[List[DynamicReviewStatusInfo]], summary="批量查询动态审核状态", description="批量查询多个动态的审核状态")
async def get_dynamic_review_status(
    request: DynamicReviewStatusQuery,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量查询动态审核状态
    
    用于前端批量查询多个动态的审核状态，支持最多100个动态ID
    
    - **dynamic_ids**: 动态ID列表，最多支持100个
    
    返回每个动态的审核状态信息，包括：
    - dynamic_id: 动态ID
    - content: 动态内容
    - dynamic_type: 动态类型
    - status: 动态状态（normal、hidden、deleted）
    - review_status: 审核状态（PENDING、APPROVED、REJECTED）
    - create_time: 创建时间
    - update_time: 更新时间
    """
    try:
        service = SocialAsyncService(db)
        review_status_list = await service.get_dynamic_review_status(request.dynamic_ids)
        return SuccessResponse.create(data=review_status_list, message="获取审核状态成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="查询动态审核状态失败")


@router.post("/dynamics/{dynamic_id}/review", response_model=SuccessResponse[DynamicInfo], summary="审核动态")
async def review_dynamic(
    dynamic_id: int,
    review_data: DynamicReviewRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    审核动态
    
    管理员审核用户发布的动态，可以设置为通过或拒绝
    
    - **review_status**: 审核状态（APPROVED 或 REJECTED）
    - **review_comment**: 审核备注（可选）
    """
    try:
        service = SocialAsyncService(db)
        info = await service.review_dynamic(dynamic_id, review_data)
        status_text = "通过" if review_data.review_status == "APPROVED" else "拒绝"
        return SuccessResponse.create(data=info, message=f"动态审核{status_text}成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="审核动态失败")


# ================ 付费动态相关接口 ================

@router.post("/dynamics/{dynamic_id}/paid", response_model=SuccessResponse[PaidDynamicInfo], summary="创建付费动态")
async def create_paid_dynamic(
    dynamic_id: int,
    data: PaidDynamicCreate,
    current_user: UserContext = Depends(require_blogger_for_paid_content),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建付费动态
    
    只有博主才能将动态设置为付费动态
    
    - **price**: 价格（金币），1-10000
    """
    try:
        service = SocialAsyncService(db)
        paid_info = await service.create_paid_dynamic(dynamic_id, data.price, current_user.user_id)
        return SuccessResponse.create(data=paid_info, message="付费动态创建成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="创建付费动态失败")


@router.post("/dynamics/{dynamic_id}/purchase", response_model=SuccessResponse[DynamicPurchaseInfo], summary="购买动态")
async def purchase_dynamic(
    dynamic_id: int,
    request: DynamicPurchaseRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    购买动态
    
    用户购买付费动态，需要消耗金币
    """
    try:
        service = SocialAsyncService(db)
        purchase_info = await service.purchase_dynamic(dynamic_id, current_user.user_id)
        return SuccessResponse.create(data=purchase_info, message="购买成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="购买动态失败")


@router.get("/dynamics/{dynamic_id}/paid-info", response_model=SuccessResponse[DynamicWithPaidInfo], summary="获取带付费信息的动态详情")
async def get_dynamic_with_paid_info(
    dynamic_id: int,
    current_user: Optional[UserContext] = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取带付费信息的动态详情
    
    返回动态信息，包括是否为付费动态、价格、当前用户是否已购买等信息
    """
    try:
        service = SocialAsyncService(db)
        current_user_id = current_user.user_id if current_user else None
        dynamic_info = await service.get_dynamic_with_paid_info(dynamic_id, current_user_id)
        return SuccessResponse.create(data=dynamic_info, message="获取成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="获取动态详情失败")


@router.get("/dynamics/with-paid-info", response_model=PaginationResponse[DynamicWithPaidInfo], summary="获取带付费信息的动态列表")
async def list_dynamics_with_paid_info(
    keyword: Optional[str] = Query(None, description="关键词（内容模糊搜索）"),
    dynamic_type: Optional[str] = Query(None, description="动态类型：text、image、video、share"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤：normal、hidden、deleted"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: Optional[UserContext] = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取带付费信息的动态列表
    
    返回动态列表，包括付费信息，只有审核通过的动态才会显示
    """
    try:
        service = SocialAsyncService(db)
        query = DynamicQuery(keyword=keyword, dynamic_type=dynamic_type, user_id=user_id, status=status)
        current_user_id = current_user.user_id if current_user else None
        result = await service.list_dynamics_with_paid_info(query, pagination, current_user_id)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取动态列表失败")


@router.get("/dynamics/my-purchases", response_model=SuccessResponse[List[DynamicPurchaseInfo]], summary="获取我的购买记录")
async def get_my_purchases(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取当前用户的购买记录
    """
    try:
        service = SocialAsyncService(db)
        purchases = await service.get_user_purchases(current_user.user_id, limit)
        return SuccessResponse.create(data=purchases, message="获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取购买记录失败")


@router.delete("/dynamics/{dynamic_id}/paid", response_model=SuccessResponse[bool], summary="下架付费动态")
async def deactivate_paid_dynamic(
    dynamic_id: int,
    current_user: UserContext = Depends(require_blogger_for_paid_content),
    db: AsyncSession = Depends(get_async_db),
):
    """
    下架付费动态
    
    只有博主才能下架自己的付费动态
    """
    try:
        service = SocialAsyncService(db)
        success = await service.deactivate_paid_dynamic(dynamic_id, current_user.user_id)
        return SuccessResponse.create(data=success, message="下架成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        raise HTTPException(status_code=500, detail="下架付费动态失败")


@router.get("/dynamics/pending-review", response_model=PaginationResponse[DynamicInfo], summary="获取待审核动态列表")
async def list_pending_review_dynamics(
    keyword: Optional[str] = Query(None, description="关键词（内容模糊搜索）"),
    dynamic_type: Optional[str] = Query(None, description="动态类型：text、image、video、share"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取待审核的动态列表
    
    管理员查看所有待审核的动态，用于批量审核
    """
    try:
        service = SocialAsyncService(db)
        query = DynamicQuery(keyword=keyword, dynamic_type=dynamic_type, user_id=user_id, status="normal")
        result = await service.list_pending_review_dynamics(query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取成功")
    except Exception:
        raise HTTPException(status_code=500, detail="获取待审核动态列表失败")

