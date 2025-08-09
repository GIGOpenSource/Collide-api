from typing import Optional, Tuple

from sqlalchemy import select, insert, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.domains.favorite.models import Favorite
from app.domains.favorite.schemas import FavoriteToggleRequest, FavoriteInfo


class FavoriteToggleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle_favorite(self, user_id: int, user_nickname: Optional[str], req: FavoriteToggleRequest) -> Tuple[bool, FavoriteInfo]:
        cached = await cache_service.check_idempotent(user_id, "toggle_favorite", req.favorite_type, req.target_id)
        if cached is not None:
            return cached.get("is_favorited", False), FavoriteInfo.model_validate(cached.get("favorite_info"))
        favorite = (await self.db.execute(select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == req.favorite_type, Favorite.target_id == req.target_id)))).scalar_one_or_none()
        if favorite is None:
            await self.db.execute(insert(Favorite).values(favorite_type=req.favorite_type, target_id=req.target_id, user_id=user_id, user_nickname=user_nickname, status="active"))
            await self.db.commit()
            favorite = (await self.db.execute(select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == req.favorite_type, Favorite.target_id == req.target_id)))).scalar_one()
            is_favorited = True
        else:
            new_status = "cancelled" if favorite.status == "active" else "active"
            await self.db.execute(update(Favorite).where(Favorite.id == favorite.id).values(status=new_status))
            await self.db.commit()
            is_favorited = (new_status == "active")
        favorite = (await self.db.execute(select(Favorite).where(Favorite.id == favorite.id))).scalar_one()
        info = FavoriteInfo.model_validate(favorite)
        await cache_service.delete_pattern("favorite:*")
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("goods:*")
        result = {"is_favorited": is_favorited, "favorite_info": info.model_dump()}
        await cache_service.set_idempotent_result(user_id, "toggle_favorite", result, req.favorite_type, req.target_id)
        return is_favorited, info

