from typing import Optional, Dict

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.users.models import User
from app.domains.users.schemas import UserInfo, UserQuery


class UserQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> UserInfo:
        cached_user = await cache_service.get_user_cache(user_id)
        if cached_user:
            return UserInfo.model_validate(cached_user)
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        user_info = UserInfo.model_validate(user)
        await cache_service.set_user_cache(user_id, user_info.model_dump())
        return user_info

    async def get_user_by_username(self, username: str) -> UserInfo:
        cache_key = f"user:username:{username}"
        cached_user = await cache_service.get(cache_key)
        if cached_user:
            return UserInfo.model_validate(cached_user)
        user = (await self.db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        user_info = UserInfo.model_validate(user)
        await cache_service.set(cache_key, user_info.model_dump(), ttl=3600)
        return user_info

    async def get_user_list(self, query: UserQuery, pagination: PaginationParams) -> PaginationResult[UserInfo]:
        cache_key = f"user:list:{hash(str(query.model_dump()) + str(pagination.model_dump()))}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.model_validate(cached_result)

        conditions = []
        if query.username and query.nickname and query.username == query.nickname:
            keyword = query.username
            conditions.append(or_(User.username.contains(keyword), User.nickname.contains(keyword)))
        else:
            if query.username:
                conditions.append(User.username.contains(query.username))
            if query.nickname:
                conditions.append(User.nickname.contains(query.nickname))
        if query.email:
            conditions.append(User.email.contains(query.email))
        if query.status:
            conditions.append(User.status == query.status)

        stmt = select(User)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(User.create_time.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        result = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        users = result.scalars().all()
        items = [UserInfo.model_validate(u) for u in users]
        pagination_result = PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)
        return pagination_result

