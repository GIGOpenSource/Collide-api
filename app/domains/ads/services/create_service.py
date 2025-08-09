from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ads.models import Ad
from app.domains.ads.schemas import AdCreate, AdInfo


class AdCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ad(self, req: AdCreate) -> AdInfo:
        ad = Ad(
            ad_name=req.ad_name,
            ad_title=req.ad_title,
            ad_description=req.ad_description,
            ad_type=req.ad_type,
            image_url=req.image_url,
            click_url=req.click_url,
            alt_text=req.alt_text,
            target_type=req.target_type,
            is_active=req.is_active,
            sort_order=req.sort_order,
        )
        self.db.add(ad)
        await self.db.commit()
        await self.db.refresh(ad)
        return AdInfo.model_validate(ad)

