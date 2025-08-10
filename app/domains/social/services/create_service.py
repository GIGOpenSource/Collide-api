from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.social.models import SocialDynamic
from app.domains.social.schemas import DynamicCreate, DynamicInfo


class SocialCreateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dynamic(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], data: DynamicCreate) -> DynamicInfo:
        try:
            dynamic = SocialDynamic(
                content=data.content,
                dynamic_type=data.dynamic_type,
                images=data.images,
                video_url=data.video_url,
                share_target_type=data.share_target_type,
                share_target_id=data.share_target_id,
                share_target_title=data.share_target_title,
                user_id=user_id,
                user_nickname=user_nickname,
                user_avatar=user_avatar,
                status="normal",
            )
            self.db.add(dynamic)
            await self.db.commit()
            await self.db.refresh(dynamic)
            return DynamicInfo.model_validate(dynamic)
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"发布动态失败: {str(e)}")

