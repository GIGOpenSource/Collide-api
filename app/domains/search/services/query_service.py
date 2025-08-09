from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.content.models import Content
from app.domains.users.models import User


class SearchQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_content(self, keyword: str, pagination: PaginationParams) -> PaginationResult[dict]:
        conditions = [
            Content.status == "PUBLISHED",
            Content.review_status == "APPROVED",
            or_(Content.title.contains(keyword), Content.description.contains(keyword), Content.tags.contains(keyword), Content.author_nickname.contains(keyword)),
        ]
        stmt = select(Content).where(and_(*conditions)).order_by(Content.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        contents = rows.scalars().all()
        items = [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "content_type": c.content_type,
                "author_id": c.author_id,
                "author_nickname": c.author_nickname,
                "cover_url": c.cover_url,
                "view_count": c.view_count,
                "like_count": c.like_count,
                "create_time": c.create_time.isoformat() if c.create_time else None,
            }
            for c in contents
        ]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def search_users(self, keyword: str, pagination: PaginationParams) -> PaginationResult[dict]:
        conditions = [User.status == "active", or_(User.username.contains(keyword), User.nickname.contains(keyword), User.email.contains(keyword))]
        stmt = select(User).where(and_(*conditions)).order_by(User.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        users = rows.scalars().all()
        items = [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "avatar": u.avatar,
                "email": u.email,
                "status": u.status,
                "create_time": u.create_time.isoformat() if u.create_time else None,
            }
            for u in users
        ]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

