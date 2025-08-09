from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.comment.models import Comment
from app.domains.comment.schemas import CommentUpdate, CommentInfo


class CommentUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_comment(self, comment_id: int, user_id: int, data: CommentUpdate) -> CommentInfo:
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
        try:
            result = await self.db.execute(delete(Comment).where(and_(Comment.id == comment_id, Comment.user_id == user_id)))
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除评论失败: {str(e)}")

