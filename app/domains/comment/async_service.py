"""
评论模块异步服务层（门面）
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.comment.schemas import CommentCreate, CommentUpdate, CommentInfo, CommentQuery, CommentTreeInfo
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.comment.services.create_service import CommentCreateService
from app.domains.comment.services.update_service import CommentUpdateService
from app.domains.comment.services.query_service import CommentQueryService


class CommentAsyncService:
    """评论异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], data: CommentCreate) -> CommentInfo:
        return await CommentCreateService(self.db).create_comment(user_id, user_nickname, user_avatar, data)

    async def update_comment(self, comment_id: int, user_id: int, data: CommentUpdate) -> CommentInfo:
        return await CommentUpdateService(self.db).update_comment(comment_id, user_id, data)

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        return await CommentUpdateService(self.db).delete_comment(comment_id, user_id)

    async def get_comment_by_id(self, comment_id: int) -> CommentInfo:
        return await CommentQueryService(self.db).get_comment_by_id(comment_id)

    async def list_comments(self, query: CommentQuery, pagination: PaginationParams) -> PaginationResult[CommentInfo]:
        return await CommentQueryService(self.db).list_comments(query, pagination)

    async def get_comment_tree(self, comment_type: str, target_id: int, max_level: int = 3, max_replies_per_comment: int = 10) -> List[CommentTreeInfo]:
        return await CommentQueryService(self.db).get_comment_tree(comment_type, target_id, max_level, max_replies_per_comment)

    async def get_comment_replies(self, comment_id: int, pagination: PaginationParams) -> PaginationResult[CommentInfo]:
        """获取评论的回复列表"""
        stmt = select(Comment).where(
            and_(
                Comment.parent_comment_id == comment_id,
                Comment.status == "NORMAL"
            )
        ).order_by(Comment.create_time.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()

        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        items = [CommentInfo.model_validate(r) for r in rows]
        
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_comment_count(self, comment_type: str, target_id: int) -> int:
        """获取评论总数"""
        stmt = select(func.count()).select_from(Comment).where(
            and_(
                Comment.comment_type == comment_type,
                Comment.target_id == target_id,
                Comment.status == "NORMAL"
            )
        )
        return (await self.db.execute(stmt)).scalar()

