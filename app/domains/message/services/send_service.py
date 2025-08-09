from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.message.models import Message, MessageSession, MessageSetting
from app.domains.message.schemas import MessageCreate, MessageInfo


class MessageSendService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_message(self, sender_id: int, req: MessageCreate) -> MessageInfo:
        from app.domains.users.models import User
        receiver = (await self.db.execute(select(User).where(User.id == req.receiver_id))).scalar_one_or_none()
        if not receiver:
            raise BusinessException("接收者不存在")

        setting = (await self.db.execute(select(MessageSetting).where(MessageSetting.user_id == req.receiver_id))).scalar_one_or_none()
        if setting and not setting.allow_stranger_msg:
            from app.domains.follow.models import Follow
            follow = (await self.db.execute(select(Follow).where(and_(Follow.follower_id == sender_id, Follow.followee_id == req.receiver_id, Follow.status == "active")))).scalar_one_or_none()
            if not follow:
                raise BusinessException("对方不允许陌生人发消息")

        message = Message(
            sender_id=sender_id,
            receiver_id=req.receiver_id,
            content=req.content,
            message_type=req.message_type,
            extra_data=req.extra_data,
            reply_to_id=req.reply_to_id,
            is_pinned=req.is_pinned,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        await self._update_sessions(sender_id, req.receiver_id, message.id)
        return MessageInfo.model_validate(message)

    async def _update_sessions(self, user_id: int, other_user_id: int, message_id: int):
        session = (await self.db.execute(select(MessageSession).where(and_(MessageSession.user_id == user_id, MessageSession.other_user_id == other_user_id)))).scalar_one_or_none()
        if session:
            await self.db.execute(update(MessageSession).where(MessageSession.id == session.id).values(last_message_id=message_id, last_message_time=datetime.now(), unread_count=0))
        else:
            session = MessageSession(user_id=user_id, other_user_id=other_user_id, last_message_id=message_id, last_message_time=datetime.now(), unread_count=0)
            self.db.add(session)

        receiver_session = (await self.db.execute(select(MessageSession).where(and_(MessageSession.user_id == other_user_id, MessageSession.other_user_id == user_id)))).scalar_one_or_none()
        if receiver_session:
            await self.db.execute(update(MessageSession).where(MessageSession.id == receiver_session.id).values(last_message_id=message_id, last_message_time=datetime.now(), unread_count=MessageSession.unread_count + 1))
        else:
            receiver_session = MessageSession(user_id=other_user_id, other_user_id=user_id, last_message_id=message_id, last_message_time=datetime.now(), unread_count=1)
            self.db.add(receiver_session)
        await self.db.commit()

