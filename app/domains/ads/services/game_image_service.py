from sqlalchemy import select, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.ads.models import GameImage, Ad
from app.domains.ads.schemas import GameImageCreate, GameImageCreateWithAdId, GameImageUpdate, GameImageInfo, GameImageBatchCreate


class GameImageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_game_image(self, req: GameImageCreateWithAdId) -> GameImageInfo:
        """创建单个游戏图片"""
        # 验证广告是否存在
        ad = (await self.db.execute(select(Ad).where(Ad.id == req.ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("关联的广告不存在")
        
        game_image = GameImage(
            ad_id=req.ad_id,
            image_url=req.image_url,
            image_type=req.image_type,
            image_title=req.image_title,
            image_description=req.image_description,
            alt_text=req.alt_text,
            sort_order=req.sort_order,
            is_active=req.is_active,
        )
        self.db.add(game_image)
        await self.db.commit()
        await self.db.refresh(game_image)
        return GameImageInfo.model_validate(game_image)

    async def batch_create_game_images(self, req: GameImageBatchCreate) -> list[GameImageInfo]:
        """批量创建游戏图片"""
        # 验证广告是否存在
        ad = (await self.db.execute(select(Ad).where(Ad.id == req.ad_id))).scalar_one_or_none()
        if not ad:
            raise BusinessException("关联的广告不存在")
        
        game_images = []
        for image_data in req.images:
            game_image = GameImage(
                ad_id=req.ad_id,
                image_url=image_data.image_url,
                image_type=image_data.image_type,
                image_title=image_data.image_title,
                image_description=image_data.image_description,
                alt_text=image_data.alt_text,
                sort_order=image_data.sort_order,
                is_active=image_data.is_active,
            )
            self.db.add(game_image)
            game_images.append(game_image)
        
        await self.db.commit()
        
        # 刷新所有创建的图片
        for game_image in game_images:
            await self.db.refresh(game_image)
        
        return [GameImageInfo.model_validate(img) for img in game_images]

    async def get_game_image_by_id(self, image_id: int) -> GameImageInfo:
        """根据ID获取游戏图片"""
        game_image = (await self.db.execute(select(GameImage).where(GameImage.id == image_id))).scalar_one_or_none()
        if not game_image:
            raise BusinessException("游戏图片不存在")
        return GameImageInfo.model_validate(game_image)

    async def get_game_images_by_ad_id(self, ad_id: int, pagination: PaginationParams = None) -> PaginationResult[GameImageInfo]:
        """根据广告ID获取游戏图片列表"""
        conditions = [GameImage.ad_id == ad_id]
        
        stmt = select(GameImage).where(and_(*conditions)).order_by(GameImage.sort_order.asc(), GameImage.create_time.desc())
        
        if pagination:
            total = (await self.db.execute(select(GameImage).where(and_(*conditions)))).scalars().all()
            total = len(total)
            rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
            items = [GameImageInfo.model_validate(x) for x in rows.scalars().all()]
            return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        else:
            rows = await self.db.execute(stmt)
            items = [GameImageInfo.model_validate(x) for x in rows.scalars().all()]
            return PaginationResult.create(items=items, total=len(items), page=1, page_size=len(items))

    async def update_game_image(self, image_id: int, req: GameImageUpdate) -> GameImageInfo:
        """更新游戏图片"""
        game_image = (await self.db.execute(select(GameImage).where(GameImage.id == image_id))).scalar_one_or_none()
        if not game_image:
            raise BusinessException("游戏图片不存在")
        
        update_data = {k: v for k, v in req.model_dump(exclude_unset=True).items()}
        if update_data:
            await self.db.execute(update(GameImage).where(GameImage.id == image_id).values(**update_data))
            await self.db.commit()
            await self.db.refresh(game_image)
        
        return GameImageInfo.model_validate(game_image)

    async def delete_game_image(self, image_id: int) -> bool:
        """删除游戏图片"""
        game_image = (await self.db.execute(select(GameImage).where(GameImage.id == image_id))).scalar_one_or_none()
        if not game_image:
            raise BusinessException("游戏图片不存在")
        
        await self.db.execute(delete(GameImage).where(GameImage.id == image_id))
        await self.db.commit()
        return True

    async def toggle_game_image_status(self, image_id: int) -> GameImageInfo:
        """切换游戏图片状态"""
        game_image = (await self.db.execute(select(GameImage).where(GameImage.id == image_id))).scalar_one_or_none()
        if not game_image:
            raise BusinessException("游戏图片不存在")
        
        new_status = not game_image.is_active
        await self.db.execute(update(GameImage).where(GameImage.id == image_id).values(is_active=new_status))
        await self.db.commit()
        
        game_image = (await self.db.execute(select(GameImage).where(GameImage.id == image_id))).scalar_one()
        return GameImageInfo.model_validate(game_image) 