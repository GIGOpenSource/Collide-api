from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.social.models import SocialDynamic
from app.domains.social.schemas import DynamicUpdate, DynamicInfo, DynamicReviewRequest


class SocialUpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_dynamic(self, dynamic_id: int, user_id: int, data: DynamicUpdate) -> DynamicInfo:
        try:
            stmt = select(SocialDynamic).where(and_(SocialDynamic.id == dynamic_id, SocialDynamic.user_id == user_id))
            dynamic = (await self.db.execute(stmt)).scalar_one_or_none()
            if not dynamic:
                raise BusinessException("动态不存在或无权限")
            update_values = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
            if update_values:
                await self.db.execute(update(SocialDynamic).where(SocialDynamic.id == dynamic_id).values(**update_values))
                await self.db.commit()
                await self.db.refresh(dynamic)
            return DynamicInfo.model_validate(dynamic)
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新动态失败: {str(e)}")

    async def delete_dynamic(self, dynamic_id: int, user_id: int) -> bool:
        try:
            result = await self.db.execute(delete(SocialDynamic).where(and_(SocialDynamic.id == dynamic_id, SocialDynamic.user_id == user_id)))
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除动态失败: {str(e)}")

    async def review_dynamic(self, dynamic_id: int, review_data: DynamicReviewRequest) -> DynamicInfo:
        """审核动态"""
        try:
            stmt = select(SocialDynamic).where(SocialDynamic.id == dynamic_id)
            dynamic = (await self.db.execute(stmt)).scalar_one_or_none()
            if not dynamic:
                raise BusinessException("动态不存在")
            
            # 更新审核状态
            update_values = {"review_status": review_data.review_status}
            await self.db.execute(update(SocialDynamic).where(SocialDynamic.id == dynamic_id).values(**update_values))
            await self.db.commit()
            await self.db.refresh(dynamic)
            
            return DynamicInfo.model_validate(dynamic)
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"审核动态失败: {str(e)}")

