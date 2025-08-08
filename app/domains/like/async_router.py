"""
点赞模块异步API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse
from app.common.dependencies import get_current_user_context, UserContext
from app.common.exceptions import BusinessException
from app.domains.like.async_service import LikeAsyncService
from app.domains.like.schemas import LikeToggleRequest, LikeInfo


router = APIRouter(prefix="/api/v1/likes", tags=["点赞管理"])


@router.post("/toggle", response_model=SuccessResponse[dict], summary="点赞/取消点赞切换")
async def toggle_like(
    req: LikeToggleRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = LikeAsyncService(db)
        is_liked, like_info = await service.toggle_like(
            user_id=current_user.user_id,
            user_nickname=current_user.username,
            user_avatar=None,
            req=req,
        )
        return SuccessResponse.create(data={"isLiked": is_liked, "like": like_info.model_dump()}, message="操作成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="点赞操作失败")

