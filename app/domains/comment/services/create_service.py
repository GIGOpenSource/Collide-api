from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.comment.models import Comment
from app.domains.comment.schemas import CommentCreate, CommentInfo
from app.domains.interaction.services.record_service import InteractionRecordService


class CommentCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.interaction_service = InteractionRecordService(db)

    async def create_comment(self, user_id: int, user_nickname: str | None, user_avatar: str | None, data: CommentCreate) -> CommentInfo:
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
            
            # 记录到互动表
            await self.interaction_service.record_interaction(
                interaction_type="COMMENT",
                target_id=data.target_id,
                user_id=user_id,
                user_nickname=user_nickname or "未知用户",
                user_avatar=user_avatar
            )
            
            return CommentInfo.model_validate(comment)
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建评论失败: {str(e)}")

