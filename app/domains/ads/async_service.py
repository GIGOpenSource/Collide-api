"""
广告模块异步服务层（门面）
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ads.schemas import AdCreate, AdUpdate, AdInfo, AdQuery, GameImageCreate, GameImageCreateWithAdId, GameImageUpdate, GameImageInfo, GameImageBatchCreate, GameAdInfo
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.ads.services.create_service import AdCreateService
from app.domains.ads.services.update_service import AdUpdateService
from app.domains.ads.services.query_service import AdQueryService
from app.domains.ads.services.game_image_service import GameImageService


class AdAsyncService:
    """广告异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ad(self, req: AdCreate) -> AdInfo:
        return await AdCreateService(self.db).create_ad(req)

    async def update_ad(self, ad_id: int, req: AdUpdate) -> AdInfo:
        return await AdUpdateService(self.db).update_ad(ad_id, req)

    async def delete_ad(self, ad_id: int):
        from sqlalchemy import select, delete
        from app.domains.ads.models import Ad
        from app.common.exceptions import BusinessException
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")
        await self.db.execute(delete(Ad).where(Ad.id == ad_id))
        await self.db.commit()

    async def get_ad_by_id(self, ad_id: int) -> AdInfo:
        return await AdQueryService(self.db).get_ad_by_id(ad_id)

    async def get_ad_list(self, query: AdQuery, pagination: PaginationParams) -> PaginationResult[AdInfo]:
        return await AdQueryService(self.db).get_ad_list(query, pagination)

    async def get_active_ads_by_type(self, ad_type: str, limit: int = 10) -> List[AdInfo]:
        return await AdQueryService(self.db).get_active_ads_by_type(ad_type, limit)

    async def toggle_ad_status(self, ad_id: int) -> AdInfo:
        return await AdUpdateService(self.db).toggle_ad_status(ad_id)

    # ================ 游戏图片相关方法 ================
    
    async def create_game_image(self, req: GameImageCreateWithAdId) -> GameImageInfo:
        return await GameImageService(self.db).create_game_image(req)

    async def batch_create_game_images(self, req: GameImageBatchCreate) -> list[GameImageInfo]:
        return await GameImageService(self.db).batch_create_game_images(req)

    async def get_game_image_by_id(self, image_id: int) -> GameImageInfo:
        return await GameImageService(self.db).get_game_image_by_id(image_id)

    async def get_game_images_by_ad_id(self, ad_id: int, pagination: PaginationParams = None) -> PaginationResult[GameImageInfo]:
        return await GameImageService(self.db).get_game_images_by_ad_id(ad_id, pagination)

    async def update_game_image(self, image_id: int, req: GameImageUpdate) -> GameImageInfo:
        return await GameImageService(self.db).update_game_image(image_id, req)

    async def delete_game_image(self, image_id: int) -> bool:
        return await GameImageService(self.db).delete_game_image(image_id)

    async def toggle_game_image_status(self, image_id: int) -> GameImageInfo:
        return await GameImageService(self.db).toggle_game_image_status(image_id)

    async def get_game_ad_with_images(self, ad_id: int) -> GameAdInfo:
        """获取包含图片列表的游戏广告信息"""
        ad_info = await AdQueryService(self.db).get_ad_by_id(ad_id)
        images_result = await GameImageService(self.db).get_game_images_by_ad_id(ad_id)
        
        return GameAdInfo(
            **ad_info.model_dump(),
            game_images=images_result.items
        )