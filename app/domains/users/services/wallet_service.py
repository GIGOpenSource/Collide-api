from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.domains.users.models import UserWallet
from app.domains.users.schemas import UserWalletInfo


class UserWalletService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_wallet(self, user_id: int) -> UserWalletInfo:
        cache_key = f"user:wallet:{user_id}"
        cached_wallet = await cache_service.get(cache_key)
        if cached_wallet:
            return UserWalletInfo.model_validate(cached_wallet)

        wallet = (await self.db.execute(select(UserWallet).where(UserWallet.user_id == user_id))).scalar_one_or_none()
        if not wallet:
            wallet = UserWallet(
                user_id=user_id,
                balance=0.00,
                frozen_amount=0.00,
                coin_balance=0,
                coin_total_earned=0,
                coin_total_spent=0,
                total_income=0.00,
                total_expense=0.00,
                status="active",
            )
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)

        wallet_info = UserWalletInfo.model_validate(wallet)
        await cache_service.set(cache_key, wallet_info.model_dump(), ttl=1800)
        return wallet_info

