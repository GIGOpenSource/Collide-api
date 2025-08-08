"""
评论模块异步服务层
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func

from app.domains.comment.models import Comment
from app.domains.comment.schemas import CommentCreate, CommentUpdate, CommentInfo, CommentQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException


class CommentAsyncService:
    """评论异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(
        self,
        user_id: int,
        user_nickname: Optional[str],
        user_avatar: Optional[str],
        data: CommentCreate,
    ) -> CommentInfo:
        """创建评论"""
        try:
            comment = Comment(
                comment_type=data.comment_type,
                target_id=data.target_id,
                parent_comment_id=data.parent_comment_id,
                content=data.content,
                user_id=user_id,
                user_nickname=user_nickname,
                user_avatar=user_avatar,
                reply_to_user_id=data.reply_to_user_id,
                reply_to_user_nickname=data.reply_to_user_nickname,
                reply_to_user_avatar=data.reply_to_user_avatar,
                status="NORMAL",
            )
            self.db.add(comment)
            await self.db.commit()
            await self.db.refresh(comment)
            return CommentInfo.model_validate(comment)
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建评论失败: {str(e)}")

    async def update_comment(self, comment_id: int, user_id: int, data: CommentUpdate) -> CommentInfo:
        """更新评论（作者可改）"""
        try:
            stmt = select(Comment).where(and_(Comment.id == comment_id, Comment.user_id == user_id))
            comment = (await self.db.execute(stmt)).scalar_one_or_none()
            if not comment:
                raise BusinessException("评论不存在或无权限")

            update_values = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
            if update_values:
                await self.db.execute(update(Comment).where(Comment.id == comment_id).values(**update_values))
                await self.db.commit()
                await self.db.refresh(comment)
            return CommentInfo.model_validate(comment)
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新评论失败: {str(e)}")

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """删除评论（简单硬删，后续可改软删）"""
        try:
            result = await self.db.execute(delete(Comment).where(and_(Comment.id == comment_id, Comment.user_id == user_id)))
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除评论失败: {str(e)}")

    async def get_comment_by_id(self, comment_id: int) -> CommentInfo:
        """评论详情"""
        stmt = select(Comment).where(Comment.id == comment_id)
        comment = (await self.db.execute(stmt)).scalar_one_or_none()
        if not comment:
            raise BusinessException("评论不存在")
        return CommentInfo.model_validate(comment)

    async def list_comments(self, query: CommentQuery, pagination: PaginationParams) -> PaginationResult[CommentInfo]:
        """评论列表（按目标/类型/用户/父评论/状态筛选；按时间倒序；分页）"""
        stmt = select(Comment)
        conditions = []
        if query.comment_type:
            conditions.append(Comment.comment_type == query.comment_type)
        if query.target_id is not None:
            conditions.append(Comment.target_id == query.target_id)
        if query.user_id is not None:
            conditions.append(Comment.user_id == query.user_id)
        if query.parent_comment_id is not None:
            conditions.append(Comment.parent_comment_id == query.parent_comment_id)
        if query.status:
            conditions.append(Comment.status == query.status)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Comment.create_time.desc())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()

        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        items = [CommentInfo.model_validate(r) for r in rows]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

