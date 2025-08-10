"""
消息模块异步API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.response import SuccessResponse, PaginationResponse
from app.common.dependencies import get_current_user_context, UserContext, get_pagination
from app.common.pagination import PaginationParams
from app.common.exceptions import BusinessException
from app.domains.message.async_service import MessageAsyncService
from app.domains.message.schemas import (
    MessageCreate, MessageUpdate, MessageInfo, MessageSessionInfo, 
    MessageSettingInfo, MessageSettingUpdate, MessageQuery
)


router = APIRouter(prefix="/api/v1/messages", tags=["消息管理"])


@router.post("/send", response_model=SuccessResponse[MessageInfo], summary="发送消息")
async def send_message(
    req: MessageCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """发送消息"""
    try:
        service = MessageAsyncService(db)
        message = await service.send_message(current_user.user_id, req)
        return SuccessResponse.create(data=message, message="发送消息成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="发送消息失败")


@router.get("/conversation/{other_user_id}", response_model=PaginationResponse[MessageInfo], summary="获取对话消息")
async def get_conversation_messages(
    other_user_id: int,
    message_type: Optional[str] = Query(None, description="消息类型：text、image、file、system"),
    status: Optional[str] = Query(None, description="消息状态：sent、delivered、read、deleted"),
    is_pinned: Optional[bool] = Query(None, description="是否置顶"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取与指定用户的对话消息"""
    try:
        service = MessageAsyncService(db)
        query = MessageQuery(
            other_user_id=other_user_id,
            message_type=message_type,
            status=status,
            is_pinned=is_pinned
        )
        result = await service.get_message_list(current_user.user_id, other_user_id, query, pagination)
        return PaginationResponse.from_pagination_result(result, "获取对话消息成功")
    except BusinessException as e:
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message=e.message
        )
    except Exception as e:
        logger.error(f"获取对话消息失败: {str(e)}")
        return PaginationResponse.create(
            datas=[],
            total=0,
            current_page=pagination.page,
            page_size=pagination.page_size,
            message="获取对话消息失败，请稍后重试"
        )


@router.get("/sessions", response_model=SuccessResponse[list[MessageSessionInfo]], summary="获取会话列表")
async def get_session_list(
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户会话列表"""
    try:
        service = MessageAsyncService(db)
        sessions = await service.get_session_list(current_user.user_id)
        return SuccessResponse.create(data=sessions, message="获取会话列表成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@router.get("/settings", response_model=SuccessResponse[MessageSettingInfo], summary="获取消息设置")
async def get_message_settings(
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户消息设置"""
    try:
        service = MessageAsyncService(db)
        settings = await service.get_message_settings(current_user.user_id)
        return SuccessResponse.create(data=settings, message="获取消息设置成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取消息设置失败")


@router.put("/settings", response_model=SuccessResponse[MessageSettingInfo], summary="更新消息设置")
async def update_message_settings(
    req: MessageSettingUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """更新用户消息设置"""
    try:
        service = MessageAsyncService(db)
        settings = await service.update_message_settings(current_user.user_id, req)
        return SuccessResponse.create(data=settings, message="更新消息设置成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新消息设置失败")


@router.delete("/{message_id}", response_model=SuccessResponse[dict], summary="删除消息")
async def delete_message(
    message_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """删除消息"""
    try:
        service = MessageAsyncService(db)
        await service.delete_message(message_id, current_user.user_id)
        return SuccessResponse.create(data={}, message="删除消息成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除消息失败")


@router.get("/unread-count", response_model=SuccessResponse[dict], summary="获取未读消息数")
async def get_unread_count(
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户未读消息数"""
    try:
        service = MessageAsyncService(db)
        count = await service.get_unread_count(current_user.user_id)
        return SuccessResponse.create(data={"unread_count": count}, message="获取未读消息数成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取未读消息数失败") 