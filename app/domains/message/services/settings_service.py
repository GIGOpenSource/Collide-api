from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.message.models import MessageSetting
from app.domains.message.schemas import MessageSettingInfo, MessageSettingUpdate


class MessageSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, user_id: int) -> MessageSettingInfo:
        setting = (await self.db.execute(select(MessageSetting).where(MessageSetting.user_id == user_id))).scalar_one_or_none()
        if not setting:
            setting = MessageSetting(user_id=user_id)
            self.db.add(setting)
            await self.db.commit()
            await self.db.refresh(setting)
        return MessageSettingInfo.model_validate(setting)

    async def update_settings(self, user_id: int, req: MessageSettingUpdate) -> MessageSettingInfo:
        setting = (await self.db.execute(select(MessageSetting).where(MessageSetting.user_id == user_id))).scalar_one_or_none()
        if not setting:
            setting = MessageSetting(user_id=user_id)
            self.db.add(setting)
        update_data = {}
        if req.allow_stranger_msg is not None:
            update_data["allow_stranger_msg"] = req.allow_stranger_msg
        if req.auto_read_receipt is not None:
            update_data["auto_read_receipt"] = req.auto_read_receipt
        if req.message_notification is not None:
            update_data["message_notification"] = req.message_notification
        await self.db.execute(update(MessageSetting).where(MessageSetting.user_id == user_id).values(**update_data))
        await self.db.commit()
        setting = (await self.db.execute(select(MessageSetting).where(MessageSetting.user_id == user_id))).scalar_one()
        return MessageSettingInfo.model_validate(setting)

