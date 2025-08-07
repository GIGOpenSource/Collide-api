"""
FastAPI依赖项（微服务版本）
从网关传递的请求头获取用户信息
"""
from typing import Optional
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel

from app.common.config import settings


class UserContext(BaseModel):
    """用户上下文信息"""
    user_id: int
    username: str
    role: str = "user"


async def get_current_user_context(
    header_user_id: Optional[str] = Header(None, alias=settings.user_id_header),
    username: Optional[str] = Header(None, alias=settings.username_header),
    user_role: Optional[str] = Header(None, alias=settings.user_role_header)
) -> UserContext:
    """获取当前用户上下文信息"""
    if not header_user_id:
        raise HTTPException(
            status_code=401, 
            detail="缺少用户身份信息，请检查网关配置"
        )
    
    try:
        user_id_int = int(header_user_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="用户ID格式错误"
        )
    
    return UserContext(
        user_id=user_id_int,
        username=username or f"user_{header_user_id}",
        role=user_role or "user"
    )


async def get_current_user_id(
    user_context: UserContext = Depends(get_current_user_context)
) -> int:
    """获取当前用户ID"""
    return user_context.user_id


async def get_optional_user_context(
    header_user_id: Optional[str] = Header(None, alias=settings.user_id_header),
    username: Optional[str] = Header(None, alias=settings.username_header),
    user_role: Optional[str] = Header(None, alias=settings.user_role_header)
) -> Optional[UserContext]:
    """获取可选的用户上下文（用于可选登录的接口）"""
    if not header_user_id:
        return None
    
    try:
        user_id_int = int(header_user_id)
        return UserContext(
            user_id=user_id_int,
            username=username or f"user_{header_user_id}",
            role=user_role or "user"
        )
    except ValueError:
        return None


async def get_optional_user_id(
    user_context: Optional[UserContext] = Depends(get_optional_user_context)
) -> Optional[int]:
    """获取可选的当前用户ID"""
    return user_context.user_id if user_context else None


async def require_admin(
    user_context: UserContext = Depends(get_current_user_context)
) -> UserContext:
    """要求管理员权限"""
    if user_context.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return user_context