from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_service import cache_service
from app.common.exceptions import BusinessException
from app.domains.content.models import Content, ContentPayment
from app.domains.content.schemas import ContentPaymentCreate, ContentPaymentInfo


class ContentPaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_content_payment(self, content_id: int, payment_data: ContentPaymentCreate, user_id: int) -> ContentPaymentInfo:
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if content.author_id != user_id:
            raise BusinessException("无权限为此内容创建付费配置")
        existing = (await self.db.execute(select(ContentPayment).where(ContentPayment.content_id == content_id))).scalar_one_or_none()
        if existing:
            raise BusinessException("该内容已有付费配置")
        payment = ContentPayment(
            content_id=content_id,
            payment_type=payment_data.payment_type,
            coin_price=payment_data.coin_price,
            original_price=payment_data.original_price,
            vip_free=payment_data.vip_free,
            vip_only=payment_data.vip_only,
            trial_enabled=payment_data.trial_enabled,
            trial_content=payment_data.trial_content,
            trial_word_count=payment_data.trial_word_count,
            is_permanent=payment_data.is_permanent,
            valid_days=payment_data.valid_days,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        await cache_service.delete_pattern("payment:*")
        await cache_service.delete_content_cache(content_id)
        return ContentPaymentInfo.model_validate(payment)

    async def get_content_payment(self, content_id: int):
        cache_key = f"payment:content:{content_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            return ContentPaymentInfo.model_validate(cached)
        payment = (await self.db.execute(select(ContentPayment).where(ContentPayment.content_id == content_id))).scalar_one_or_none()
        if payment:
            info = ContentPaymentInfo.model_validate(payment)
            await cache_service.set(cache_key, info.model_dump(), ttl=3600)
            return info
        return None

