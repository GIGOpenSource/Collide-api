"""
广告模块异步服务层（门面）
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ads.schemas import AdCreate, AdUpdate, AdInfo, AdQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.ads.services.create_service import AdCreateService
from app.domains.ads.services.update_service import AdUpdateService
from app.domains.ads.services.query_service import AdQueryService


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