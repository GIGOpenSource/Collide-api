"""
FastAPI依赖项（微服务版本）
从网关传递的请求头获取用户信息
"""
from typing import Optional
from fastapi import HTTPException, Header, Depends, Query
from pydantic import BaseModel

from app.common.config import settings
from app.common.pagination import PaginationParams


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


async def get_pagination(
    # 页码别名
    page: Optional[int] = Query(None, ge=1, description="页码"),
    current_page: Optional[int] = Query(None, alias="currentPage", ge=1, description="页码(别名)"),
    curret_page: Optional[int] = Query(None, alias="curretPage", ge=1, description="页码(别名: curretPage)"),
    current: Optional[int] = Query(None, alias="current", ge=1, description="页码(别名: current)"),
    page_num: Optional[int] = Query(None, alias="pageNum", ge=1, description="页码(别名: pageNum)"),
    # 偏移量（常见于 offset/limit 风格）
    offset: Optional[int] = Query(None, alias="offset", ge=0, description="偏移量(从0开始)"),
    # 每页大小别名
    size: Optional[int] = Query(None, ge=1, le=100, description="每页数量"),
    page_size: Optional[int] = Query(None, alias="pageSize", ge=1, le=100, description="每页数量(别名: pageSize)"),
    limit: Optional[int] = Query(None, alias="limit", ge=1, le=100, description="每页数量(别名)"),
    per_page: Optional[int] = Query(None, alias="per_page", ge=1, le=100, description="每页数量(别名: per_page)")
) -> PaginationParams:
    """统一分页依赖：兼容多种前端命名，返回 PaginationParams

    支持两种风格：
    - 页码风格：curretPage/currentPage/page/pageNum/current + pageSize/size/limit/per_page
    - 偏移风格：offset + limit/size/pageSize/per_page
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