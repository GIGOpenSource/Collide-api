from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.message.models import Message


class MessageDeleteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_message(self, message_id: int, user_id: int):
        message = (await self.db.execute(select(Message).where(and_(Message.id == message_id, Message.sender_id == user_id)))).scalar_one_or_none()
        if not message:
            raise BusinessException("消息不存在或无权限删除")
        await self.db.execute(delete(Message).where(Message.id == message_id))
        await self.db.commit()

