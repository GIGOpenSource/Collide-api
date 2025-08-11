"""
FastAPI依赖项（微服务版本）
从网关传递的请求头获取用户信息
"""
from typing import Optional, List
from fastapi import HTTPException, Header, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.common.config import settings
from app.common.pagination import PaginationParams
from app.database.connection import get_async_db
from app.domains.users.models import UserRole, Role


class UserContext(BaseModel):
    """用户上下文信息"""
    user_id: int = Field(..., description="当前登录用户ID")
    username: str = Field(..., description="当前登录用户名")
    roles: List[str] = Field(default=["user"], description="用户角色列表")


async def get_roles_for_user(user_id: int, db: AsyncSession) -> List[str]:
    """根据用户ID从数据库查询角色列表"""
    stmt = (
        select(Role.name)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
    )
    result = await db.execute(stmt)
    roles = [row[0] for row in result.all()]
    return roles if roles else ["user"]


async def get_current_user_context(
    header_user_id: Optional[str] = Header(None, alias=settings.user_id_header),
    username: Optional[str] = Header(None, alias=settings.username_header),
    db: AsyncSession = Depends(get_async_db)
) -> UserContext:
    """获取当前用户上下文信息（角色从数据库读取）"""
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
    
    roles = await get_roles_for_user(user_id_int, db)
    
    return UserContext(
        user_id=user_id_int,
        username=username or f"user_{header_user_id}",
        roles=roles
    )


async def get_current_user_id(
    user_context: UserContext = Depends(get_current_user_context)
) -> int:
    """获取当前用户ID"""
    return user_context.user_id


async def get_optional_user_context(
    header_user_id: Optional[str] = Header(None, alias=settings.user_id_header),
    username: Optional[str] = Header(None, alias=settings.username_header),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[UserContext]:
    """获取可选的用户上下文（角色从数据库读取）"""
    if not header_user_id:
        return None
    
    try:
        user_id_int = int(header_user_id)
        roles = await get_roles_for_user(user_id_int, db)
        return UserContext(
            user_id=user_id_int,
            username=username or f"user_{header_user_id}",
            roles=roles
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
    if not any(role in user_context.roles for role in ["admin", "super_admin"]):
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return user_context


async def require_blogger_role(
    user_context: UserContext = Depends(get_current_user_context)
) -> UserContext:
    # """要求Blogger角色权限"""
    # if ["blogger", "user"] not in user_context.roles:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="需要博主权限"
    #     )
    return user_context


async def require_vip_or_blogger(
    user_context: UserContext = Depends(get_current_user_context)
) -> UserContext:
    """要求VIP或Blogger角色权限"""
    # if not any(role in user_context.roles for role in ["vip", "blogger", "admin", "super_admin"]):
    #     raise HTTPException(
    #         status_code=403,
    #         detail="需要VIP或博主权限"
    #     )
    return user_context


async def require_blogger_for_paid_content(
    user_context: UserContext = Depends(get_current_user_context)
) -> UserContext:
    """要求Blogger角色权限（用于付费内容）"""
    if "blogger" not in user_context.roles:
        raise HTTPException(
            status_code=403,
            detail="只有博主才能发布付费内容"
        )
    return user_context


async def get_pagination(
    # 页码别名
    page: Optional[int] = Query(None, ge=1, description="页码（不推荐，推荐使用 curretPage）", deprecated=True),
    current_page: Optional[int] = Query(None, alias="currentPage", ge=1, description="页码(别名: currentPage)（不推荐，推荐使用 curretPage）", deprecated=True),
    curret_page: Optional[int] = Query(None, alias="curretPage", ge=1, description="页码（推荐）", examples={"示例": {"summary": "第2页", "value": 2}}),
    current: Optional[int] = Query(None, alias="current", ge=1, description="页码(别名: current)（不推荐，推荐使用 curretPage）", deprecated=True),
    page_num: Optional[int] = Query(None, alias="pageNum", ge=1, description="页码(别名: pageNum)（不推荐，推荐使用 curretPage）", deprecated=True),
    # 偏移量（常见于 offset/limit 风格）
    offset: Optional[int] = Query(None, alias="offset", ge=0, description="偏移量(从0开始)（兼容参数，推荐使用 curretPage/pageSize）", deprecated=True),
    # 每页大小别名
    size: Optional[int] = Query(None, ge=1, le=100, description="每页数量（不推荐，推荐使用 pageSize）", deprecated=True),
    page_size: Optional[int] = Query(None, alias="pageSize", ge=1, le=100, description="每页数量（推荐）", examples={"示例": {"summary": "每页20条", "value": 20}}),
    limit: Optional[int] = Query(None, alias="limit", ge=1, le=100, description="每页数量(别名: limit)（不推荐，推荐使用 pageSize）", deprecated=True),
    per_page: Optional[int] = Query(None, alias="per_page", ge=1, le=100, description="每页数量(别名: per_page)（不推荐，推荐使用 pageSize）", deprecated=True)
) -> PaginationParams:
    """统一分页依赖：兼容多种前端命名，返回 PaginationParams

    支持两种风格（推荐优先使用前者）：
    - 页码风格（推荐）：curretPage + pageSize
    - 兼容风格：currentPage/page/pageNum/current + pageSize/size/limit/per_page，或 offset + limit
    """
    # 优先前端标准参数 pageSize，其次兼容 size/limit/per_page
    effective_page_size = page_size or size or limit or per_page or 20

    # 优先使用页码类参数
    if (curret_page is not None) or (current_page is not None) or (page is not None) or (page_num is not None) or (current is not None):
        # 优先前端标准参数 curretPage，其次兼容 currentPage/page/pageNum/current
        effective_page = curret_page or current_page or page or page_num or current or 1
    else:
        # 兼容 offset/limit 风格：用 offset 推导 page
        if offset is not None:
            effective_page = (offset // effective_page_size) + 1
        else:
            effective_page = 1

    return PaginationParams(page=effective_page, page_size=effective_page_size)