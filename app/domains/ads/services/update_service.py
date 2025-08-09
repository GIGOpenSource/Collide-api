from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.ads.models import Ad
from app.domains.ads.schemas import AdUpdate, AdInfo


class AdUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_ad(self, ad_id: int, req: AdUpdate) -> AdInfo:
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")
        update_data = {k: v for k, v in req.model_dump(exclude_unset=True).items()}
        if update_data:
            await self.db.execute(update(Ad).where(Ad.id == ad_id).values(**update_data))
            await self.db.commit()
            await self.db.refresh(ad)
        return AdInfo.model_validate(ad)

    async def toggle_ad_status(self, ad_id: int) -> AdInfo:
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")
        new_status = not ad.is_active
        await self.db.execute(update(Ad).where(Ad.id == ad_id).values(is_active=new_status))
        await self.db.commit()
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
        return AdInfo.model_validate(ad)

