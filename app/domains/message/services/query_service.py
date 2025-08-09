from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.domains.message.models import Message, MessageSession
from app.domains.message.schemas import MessageInfo, MessageSessionInfo, MessageQuery


class MessageQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_message_list(self, user_id: int, other_user_id: int, query: MessageQuery, pagination: PaginationParams) -> PaginationResult[MessageInfo]:
        conditions = [
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id),
            )
        ]
        if query.message_type:
            conditions.append(Message.message_type == query.message_type)
        if query.status:
            conditions.append(Message.status == query.status)
        if query.is_pinned is not None:
            conditions.append(Message.is_pinned == query.is_pinned)

        stmt = select(Message).where(and_(*conditions)).order_by(Message.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        messages = rows.scalars().all()
        items = [MessageInfo.model_validate(m) for m in messages]
        await self._mark_messages_as_read(user_id, other_user_id)
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def _mark_messages_as_read(self, user_id: int, other_user_id: int):
        await self.db.execute(update(Message).where(and_(Message.receiver_id == user_id, Message.sender_id == other_user_id, Message.status != "read")).values(status="read", read_time=datetime.now()))
        await self.db.execute(update(MessageSession).where(and_(MessageSession.user_id == user_id, MessageSession.other_user_id == other_user_id)).values(unread_count=0))
        await self.db.commit()

    async def get_session_list(self, user_id: int) -> List[MessageSessionInfo]:
        rows = await self.db.execute(select(MessageSession).where(and_(MessageSession.user_id == user_id, MessageSession.is_archived == False)).order_by(MessageSession.last_message_time.desc().nullslast()))
        sessions = rows.scalars().all()
        return [MessageSessionInfo.model_validate(s) for s in sessions]

