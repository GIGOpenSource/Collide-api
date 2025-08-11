from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.ads.models import Ad
from app.domains.ads.schemas import AdInfo, AdQuery


class AdQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ad_by_id(self, ad_id: int) -> AdInfo:
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            from app.common.exceptions import BusinessException
            raise BusinessException("广告不存在")
        return AdInfo.model_validate(ad)

    async def get_ad_list(self, query: AdQuery, pagination: PaginationParams) -> PaginationResult[AdInfo]:
        conditions = []
        if query.ad_type:
            conditions.append(Ad.ad_type == query.ad_type)
        if query.ad_types:
            conditions.append(Ad.ad_type.in_(query.ad_types))
        if query.is_active is not None:
            conditions.append(Ad.is_active == query.is_active)
        # 模糊匹配
        if query.keyword:
            conditions.append(or_(Ad.ad_name.contains(query.keyword), Ad.ad_title.contains(query.keyword), Ad.ad_description.contains(query.keyword)))
        if query.ad_name:
            conditions.append(Ad.ad_name.contains(query.ad_name))
        if query.ad_title:
            conditions.append(Ad.ad_title.contains(query.ad_title))
        if query.target_type:
            conditions.append(Ad.target_type == query.target_type)
        # 范围筛选
        if query.start_time:
            conditions.append(Ad.create_time >= query.start_time)
        if query.end_time:
            conditions.append(Ad.create_time <= query.end_time)
        if query.min_sort is not None:
            conditions.append(Ad.sort_order >= query.min_sort)
        if query.max_sort is not None:
            conditions.append(Ad.sort_order <= query.max_sort)
        
        # 游戏广告查询条件
        if query.game_company:
            conditions.append(Ad.game_company.contains(query.game_company))
        if query.game_type:
            conditions.append(Ad.game_type.contains(query.game_type))
        if query.game_platform:
            conditions.append(Ad.game_platform.contains(query.game_platform))
        if query.min_game_rating is not None:
            conditions.append(Ad.game_rating >= query.min_game_rating)
        if query.max_game_rating is not None:
            conditions.append(Ad.game_rating <= query.max_game_rating)
        if query.min_game_download_count is not None:
            conditions.append(Ad.game_download_count >= query.min_game_download_count)
        if query.max_game_download_count is not None:
            conditions.append(Ad.game_download_count <= query.max_game_download_count)
        
        # 下载相关查询条件
        if query.is_free_download is not None:
            conditions.append(Ad.is_free_download == query.is_free_download)
        if query.is_vip_download is not None:
            conditions.append(Ad.is_vip_download == query.is_vip_download)
        if query.is_coin_download is not None:
            conditions.append(Ad.is_coin_download == query.is_coin_download)
        if query.min_coin_price is not None:
            conditions.append(Ad.coin_price >= query.min_coin_price)
        if query.max_coin_price is not None:
            conditions.append(Ad.coin_price <= query.max_coin_price)
        if query.download_platform:
            conditions.append(Ad.download_platform.contains(query.download_platform))

        stmt = select(Ad)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Ad.sort_order.desc(), Ad.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [AdInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_active_ads_by_type(self, ad_type: str, limit: int = 10) -> list[AdInfo]:
        rows = await self.db.execute(select(Ad).where(and_(Ad.ad_type == ad_type, Ad.is_active == True)).order_by(Ad.sort_order.desc(), Ad.create_time.desc()).limit(limit))
        ads = rows.scalars().all()
        return [AdInfo.model_validate(a) for a in ads]

