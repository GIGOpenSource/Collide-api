"""
收藏模块异步服务层
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, func

from app.domains.favorite.models import Favorite
from app.domains.favorite.schemas import FavoriteToggleRequest, FavoriteInfo, FavoriteQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class FavoriteAsyncService:
    """收藏异步服务类（支持幂等切换）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def toggle_favorite(self, user_id: int, user_nickname: Optional[str], req: FavoriteToggleRequest) -> Tuple[bool, FavoriteInfo]:
        """收藏/取消收藏切换

        返回 (is_favorited, favorite_info)
        is_favorited=True 表示当前操作后为收藏状态
        """
        favorite = (await self.db.execute(
            select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == req.favorite_type, Favorite.target_id == req.target_id))
        )).scalar_one_or_none()

        if favorite is None:
            # 首次收藏
            await self.db.execute(insert(Favorite).values(
                favorite_type=req.favorite_type,
                target_id=req.target_id,
                user_id=user_id,
                user_nickname=user_nickname,
                status="active",
            ))
            await self.db.commit()
            favorite = (await self.db.execute(
                select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.favorite_type == req.favorite_type, Favorite.target_id == req.target_id))
            )).scalar_one()
            return True, FavoriteInfo.model_validate(favorite)

        # 已存在记录，按状态切换
        new_status = "cancelled" if favorite.status == "active" else "active"
        await self.db.execute(update(Favorite).where(Favorite.id == favorite.id).values(status=new_status))
        await self.db.commit()

        # 刷新
        favorite = (await self.db.execute(select(Favorite).where(Favorite.id == favorite.id))).scalar_one()
        return new_status == "active", FavoriteInfo.model_validate(favorite)

    async def get_favorite_list(self, query: FavoriteQuery, pagination: PaginationParams) -> PaginationResult[FavoriteInfo]:
        """获取收藏列表"""
        conditions = []

        if query.user_id:
            conditions.append(Favorite.user_id == query.user_id)

        if query.favorite_type:
            conditions.append(Favorite.favorite_type == query.favorite_type)

        if query.status:
            conditions.append(Favorite.status == query.status)
        else:
            # 默认只查询活跃状态
            conditions.append(Favorite.status == "active")

        stmt = select(Favorite).where(and_(*conditions)).order_by(Favorite.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        favorites = result.scalars().all()

        favorite_list = [FavoriteInfo.model_validate(favorite) for favorite in favorites]

        return PaginationResult.create(
            items=favorite_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def check_favorite_status(self, user_id: int, favorite_type: str, target_id: int) -> bool:
        """检查收藏状态"""
        favorite = (await self.db.execute(
            select(Favorite).where(and_(
                Favorite.user_id == user_id,
                Favorite.favorite_type == favorite_type,
                Favorite.target_id == target_id,
                Favorite.status == "active"
            ))
        )).scalar_one_or_none()
        return favorite is not None 