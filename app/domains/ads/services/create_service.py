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
            
            # 游戏相关字段
            game_intro=req.game_intro,
            game_detail=req.game_detail,
            game_company=req.game_company,
            game_type=req.game_type,
            game_rating=req.game_rating,
            game_size=req.game_size,
            game_version=req.game_version,
            game_platform=req.game_platform,
            game_tags=req.game_tags,
            game_download_count=req.game_download_count,
            game_rating_count=req.game_rating_count,
            
            # 下载相关字段
            is_free_download=req.is_free_download,
            is_vip_download=req.is_vip_download,
            is_coin_download=req.is_coin_download,
            coin_price=req.coin_price,
            original_coin_price=req.original_coin_price,
            download_url=req.download_url,
            download_platform=req.download_platform,
            download_size=req.download_size,
            download_version=req.download_version,
            download_requirements=req.download_requirements,
        )
        self.db.add(ad)
        await self.db.commit()
        await self.db.refresh(ad)
        return AdInfo.model_validate(ad)

