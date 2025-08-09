from typing import Optional, Dict

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.users.models import User, Role, UserRole
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
        # 查询角色列表
        roles_stmt = (
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        roles_result = await self.db.execute(roles_stmt)
        roles = [row[0] for row in roles_result.all()] or ["user"]
        user_dict = UserInfo.model_validate(user).model_dump()
        user_dict["roles"] = roles
        user_info = UserInfo(**user_dict)
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
        # 查询角色列表
        roles_stmt = (
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        roles_result = await self.db.execute(roles_stmt)
        roles = [row[0] for row in roles_result.all()] or ["user"]
        user_dict = UserInfo.model_validate(user).model_dump()
        user_dict["roles"] = roles
        user_info = UserInfo(**user_dict)
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
        # 粉丝数范围
        if getattr(query, "follower_count_min", None) is not None:
            conditions.append(User.follower_count >= query.follower_count_min)
        if getattr(query, "follower_count_max", None) is not None:
            conditions.append(User.follower_count <= query.follower_count_max)
        # 获赞数范围
        if getattr(query, "like_count_min", None) is not None:
            conditions.append(User.like_count >= query.like_count_min)
        if getattr(query, "like_count_max", None) is not None:
            conditions.append(User.like_count <= query.like_count_max)
        # 角色筛选（通过子查询限制 User.id 集合）
        if getattr(query, "role", None):
            role_name = query.role
            role_user_ids_stmt = (
                select(UserRole.user_id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.name == role_name)
            )
            conditions.append(User.id.in_(role_user_ids_stmt))

        stmt = select(User)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(User.create_time.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        result = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        users = result.scalars().all()

        # 批量查询角色，减少N+1
        if users:
            user_ids = [u.id for u in users]
            roles_stmt = (
                select(UserRole.user_id, Role.name)
                .join(Role, Role.id == UserRole.role_id)
                .where(UserRole.user_id.in_(user_ids))
            )
            roles_result = await self.db.execute(roles_stmt)
            user_id_to_roles = {}
            for uid, role_name in roles_result.all():
                user_id_to_roles.setdefault(uid, []).append(role_name)
        else:
            user_id_to_roles = {}

        items = []
        for u in users:
            user_dict = UserInfo.model_validate(u).model_dump()
            user_dict["roles"] = user_id_to_roles.get(u.id, ["user"]) or ["user"]
            items.append(UserInfo(**user_dict))
        pagination_result = PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)
        return pagination_result

