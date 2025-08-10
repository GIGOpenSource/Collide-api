from typing import Optional
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.domains.users.models import User, UserBlock
from app.domains.users.schemas import UserInfo, UserUpdate


class UserProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_user(self, user_id: int, req: UserUpdate) -> UserInfo:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")

        update_data = {}
        from sqlalchemy import and_
        if req.username is not None:
            existing_user = (await self.db.execute(select(User).where(and_(User.username == req.username, User.id != user_id)))).scalar_one_or_none()
            if existing_user:
                raise BusinessException("用户名已被使用")
            update_data["username"] = req.username
        if req.email is not None:
            existing_email = (await self.db.execute(select(User).where(and_(User.email == req.email, User.id != user_id)))).scalar_one_or_none()
            if existing_email:
                raise BusinessException("邮箱已被使用")
            update_data["email"] = req.email
        if req.nickname is not None:
            update_data["nickname"] = req.nickname
        if req.avatar is not None:
            update_data["avatar"] = req.avatar
        if req.bio is not None:
            update_data["bio"] = req.bio
        if req.status is not None:
            update_data["status"] = req.status

        if update_data:
            await self.db.execute(update(User).where(User.id == user_id).values(**update_data))
            await self.db.commit()

        await cache_service.delete_user_cache(user_id)
        await cache_service.delete_pattern("user:username:*")
        return await self._get_user_info(user_id)

    async def _get_user_info(self, user_id: int) -> UserInfo:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        return UserInfo.model_validate(user)

    async def block_user(self, user_id: int, blocked_user_id: int, reason: Optional[str] = None):
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        blocked_user = (await self.db.execute(select(User).where(User.id == blocked_user_id))).scalar_one_or_none()
        if not user or not blocked_user:
            raise BusinessException("用户不存在")
        if user_id == blocked_user_id:
            raise BusinessException("不能拉黑自己")
        existing_block = (await self.db.execute(select(UserBlock).where(and_(UserBlock.user_id == user_id, UserBlock.blocked_user_id == blocked_user_id)))).scalar_one_or_none()
        if existing_block:
            raise BusinessException("已经拉黑该用户")
        record = UserBlock(
            user_id=user_id,
            blocked_user_id=blocked_user_id,
            user_username=user.username,
            blocked_username=blocked_user.username,
            status="active",
            reason=reason,
        )
        self.db.add(record)
        await self.db.commit()
        await cache_service.delete_pattern("user:block:*")
        from app.domains.users.schemas import UserBlockInfo
        return UserBlockInfo.model_validate(record)

    async def unblock_user(self, user_id: int, blocked_user_id: int) -> bool:
        block_record = (await self.db.execute(select(UserBlock).where(and_(UserBlock.user_id == user_id, UserBlock.blocked_user_id == blocked_user_id)))).scalar_one_or_none()
        if not block_record:
            raise BusinessException("未找到拉黑记录")
        await self.db.execute(delete(UserBlock).where(UserBlock.id == block_record.id))
        await self.db.commit()
        await cache_service.delete_pattern("user:block:*")
        return True

