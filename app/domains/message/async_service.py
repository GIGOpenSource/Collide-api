"""
消息模块异步服务层（门面）
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.message.schemas import MessageCreate, MessageUpdate, MessageInfo, MessageSessionInfo, MessageSettingInfo, MessageSettingUpdate, MessageQuery
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.message.services.send_service import MessageSendService
from app.domains.message.services.query_service import MessageQueryService
from app.domains.message.services.settings_service import MessageSettingsService
from app.domains.message.services.delete_service import MessageDeleteService


class MessageAsyncService:
    """消息异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_message(self, sender_id: int, req: MessageCreate) -> MessageInfo:
        return await MessageSendService(self.db).send_message(sender_id, req)

    async def _update_message_session(self, user_id: int, other_user_id: int, message_id: int):
        """更新消息会话统计"""
        # 查找或创建会话记录
        session = (await self.db.execute(
            select(MessageSession).where(and_(
                MessageSession.user_id == user_id,
                MessageSession.other_user_id == other_user_id
            ))
        )).scalar_one_or_none()

        if session:
            # 更新现有会话
            await self.db.execute(
                update(MessageSession).where(MessageSession.id == session.id).values(
                    last_message_id=message_id,
                    last_message_time=datetime.now(),
                    unread_count=0  # 发送者自己的会话未读数清零
                )
            )
        else:
            # 创建新会话
            session = MessageSession(
                user_id=user_id,
                other_user_id=other_user_id,
                last_message_id=message_id,
                last_message_time=datetime.now(),
                unread_count=0
            )
            self.db.add(session)

        # 为接收者创建或更新会话
        receiver_session = (await self.db.execute(
            select(MessageSession).where(and_(
                MessageSession.user_id == other_user_id,
                MessageSession.other_user_id == user_id
            ))
        )).scalar_one_or_none()

        if receiver_session:
            # 更新接收者会话，增加未读数
            await self.db.execute(
                update(MessageSession).where(MessageSession.id == receiver_session.id).values(
                    last_message_id=message_id,
                    last_message_time=datetime.now(),
                    unread_count=MessageSession.unread_count + 1
                )
            )
        else:
            # 为接收者创建新会话
            receiver_session = MessageSession(
                user_id=other_user_id,
                other_user_id=user_id,
                last_message_id=message_id,
                last_message_time=datetime.now(),
                unread_count=1
            )
            self.db.add(receiver_session)

        await self.db.commit()

    async def get_message_list(self, user_id: int, other_user_id: int, query: MessageQuery, pagination: PaginationParams) -> PaginationResult[MessageInfo]:
        return await MessageQueryService(self.db).get_message_list(user_id, other_user_id, query, pagination)

    # 已下沉至 MessageQueryService

    async def get_session_list(self, user_id: int) -> List[MessageSessionInfo]:
        return await MessageQueryService(self.db).get_session_list(user_id)

    async def get_message_settings(self, user_id: int) -> MessageSettingInfo:
        return await MessageSettingsService(self.db).get_settings(user_id)

    async def update_message_settings(self, user_id: int, req: MessageSettingUpdate) -> MessageSettingInfo:
        return await MessageSettingsService(self.db).update_settings(user_id, req)

    async def delete_message(self, message_id: int, user_id: int):
        return await MessageDeleteService(self.db).delete_message(message_id, user_id)

    async def get_unread_count(self, user_id: int) -> int:
        from sqlalchemy import select, func
        from app.domains.message.models import MessageSession
        result = (await self.db.execute(select(func.sum(MessageSession.unread_count)).where(MessageSession.user_id == user_id))).scalar()
        return result or 0