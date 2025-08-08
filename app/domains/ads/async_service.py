"""
广告模块异步服务层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.ads.models import Ad
from app.domains.ads.schemas import AdCreate, AdUpdate, AdInfo, AdQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class AdAsyncService:
    """广告异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ad(self, req: AdCreate) -> AdInfo:
        """创建广告"""
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
            sort_order=req.sort_order
        )
        self.db.add(ad)
        await self.db.commit()
        await self.db.refresh(ad)
        return AdInfo.model_validate(ad)

    async def update_ad(self, ad_id: int, req: AdUpdate) -> AdInfo:
        """更新广告"""
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")

        # 更新字段
        update_data = {}
        if req.ad_name is not None:
            update_data["ad_name"] = req.ad_name
        if req.ad_title is not None:
            update_data["ad_title"] = req.ad_title
        if req.ad_description is not None:
            update_data["ad_description"] = req.ad_description
        if req.ad_type is not None:
            update_data["ad_type"] = req.ad_type
        if req.image_url is not None:
            update_data["image_url"] = req.image_url
        if req.click_url is not None:
            update_data["click_url"] = req.click_url
        if req.alt_text is not None:
            update_data["alt_text"] = req.alt_text
        if req.target_type is not None:
            update_data["target_type"] = req.target_type
        if req.is_active is not None:
            update_data["is_active"] = req.is_active
        if req.sort_order is not None:
            update_data["sort_order"] = req.sort_order

        await self.db.execute(update(Ad).where(Ad.id == ad_id).values(**update_data))
        await self.db.commit()

        # 刷新数据
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
        return AdInfo.model_validate(ad)

    async def delete_ad(self, ad_id: int):
        """删除广告"""
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")

        await self.db.execute(delete(Ad).where(Ad.id == ad_id))
        await self.db.commit()

    async def get_ad_by_id(self, ad_id: int) -> AdInfo:
        """根据ID获取广告"""
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")
        return AdInfo.model_validate(ad)

    async def get_ad_list(self, query: AdQuery, pagination: PaginationParams) -> PaginationResult[AdInfo]:
        """获取广告列表"""
        conditions = []

        if query.ad_type:
            conditions.append(Ad.ad_type == query.ad_type)
        if query.is_active is not None:
            conditions.append(Ad.is_active == query.is_active)
        if query.keyword:
            conditions.append(or_(
                Ad.ad_name.contains(query.keyword),
                Ad.ad_title.contains(query.keyword),
                Ad.ad_description.contains(query.keyword)
            ))

        stmt = select(Ad).where(and_(*conditions)).order_by(Ad.sort_order.desc(), Ad.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        ads = result.scalars().all()

        ad_list = [AdInfo.model_validate(ad) for ad in ads]

        return PaginationResult.create(
            items=ad_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def get_active_ads_by_type(self, ad_type: str, limit: int = 10) -> List[AdInfo]:
        """根据类型获取活跃广告"""
        stmt = select(Ad).where(
            and_(Ad.ad_type == ad_type, Ad.is_active == True)
        ).order_by(Ad.sort_order.desc(), Ad.create_time.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        ads = result.scalars().all()

        return [AdInfo.model_validate(ad) for ad in ads]

    async def toggle_ad_status(self, ad_id: int) -> AdInfo:
        """切换广告状态"""
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("广告不存在")

        new_status = not ad.is_active
        await self.db.execute(update(Ad).where(Ad.id == ad_id).values(is_active=new_status))
        await self.db.commit()

        # 刷新数据
        ad = (await self.db.execute(select(Ad).where(Ad.id == ad_id))).scalar_one()
        return AdInfo.model_validate(ad) 