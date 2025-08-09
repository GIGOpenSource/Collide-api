from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.common.exceptions import BusinessException
from app.domains.users.models import User
from app.domains.users.schemas import UserInfo


class UserAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInfo]:
        user = (await self.db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if not user:
            return None
        if not self._verify_password(password, user.password_hash):
            return None
        return UserInfo.model_validate(user)

