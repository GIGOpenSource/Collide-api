"""
消息模块异步服务层
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.message.models import Message, MessageSession, MessageSetting
from app.domains.message.schemas import MessageCreate, MessageUpdate, MessageInfo, MessageSessionInfo, MessageSettingInfo, MessageSettingUpdate, MessageQuery
from app.common.exceptions import BusinessException
from app.common.pagination import PaginationParams, PaginationResult


class MessageAsyncService:
    """消息异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_message(self, sender_id: int, req: MessageCreate) -> MessageInfo:
        """发送消息"""
        # 检查接收者是否存在
        from app.domains.users.models import User
        receiver = (await self.db.execute(select(User).where(User.id == req.receiver_id))).scalar_one_or_none()
        if not receiver:
            raise BusinessException("接收者不存在")

        # 检查接收者的消息设置
        setting = (await self.db.execute(
            select(MessageSetting).where(MessageSetting.user_id == req.receiver_id)
        )).scalar_one_or_none()

        if setting and not setting.allow_stranger_msg:
            # 检查是否有关注关系
            from app.domains.follow.models import Follow
            follow = (await self.db.execute(
                select(Follow).where(and_(
                    Follow.follower_id == sender_id,
                    Follow.followee_id == req.receiver_id,
                    Follow.status == "active"
                ))
            )).scalar_one_or_none()
            
            if not follow:
                raise BusinessException("对方不允许陌生人发消息")

        # 创建消息
        message = Message(
            sender_id=sender_id,
            receiver_id=req.receiver_id,
            content=req.content,
            message_type=req.message_type,
            extra_data=req.extra_data,
            reply_to_id=req.reply_to_id,
            is_pinned=req.is_pinned
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # 更新或创建会话统计
        await self._update_message_session(sender_id, req.receiver_id, message.id)

        return MessageInfo.model_validate(message)

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
        """获取两人之间的消息列表"""
        conditions = [
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
            )
        ]

        if query.message_type:
            conditions.append(Message.message_type == query.message_type)
        if query.status:
            conditions.append(Message.status == query.status)
        if query.is_pinned is not None:
            conditions.append(Message.is_pinned == query.is_pinned)

        stmt = select(Message).where(and_(*conditions)).order_by(Message.create_time.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        message_list = [MessageInfo.model_validate(message) for message in messages]

        # 标记消息为已读
        await self._mark_messages_as_read(user_id, other_user_id)

        return PaginationResult.create(
            items=message_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

    async def _mark_messages_as_read(self, user_id: int, other_user_id: int):
        """标记消息为已读"""
        # 更新消息状态
        await self.db.execute(
            update(Message).where(and_(
                Message.receiver_id == user_id,
                Message.sender_id == other_user_id,
                Message.status != "read"
            )).values(
                status="read",
                read_time=datetime.now()
            )
        )

        # 更新会话未读数
        await self.db.execute(
            update(MessageSession).where(and_(
                MessageSession.user_id == user_id,
                MessageSession.other_user_id == other_user_id
            )).values(unread_count=0)
        )

        await self.db.commit()

    async def get_session_list(self, user_id: int) -> List[MessageSessionInfo]:
        """获取用户会话列表"""
        stmt = select(MessageSession).where(
            and_(MessageSession.user_id == user_id, MessageSession.is_archived == False)
        ).order_by(MessageSession.last_message_time.desc().nullslast())
        
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        return [MessageSessionInfo.model_validate(session) for session in sessions]

    async def get_message_settings(self, user_id: int) -> MessageSettingInfo:
        """获取用户消息设置"""
        setting = (await self.db.execute(
            select(MessageSetting).where(MessageSetting.user_id == user_id)
        )).scalar_one_or_none()

        if not setting:
            # 创建默认设置
            setting = MessageSetting(user_id=user_id)
            self.db.add(setting)
            await self.db.commit()
            await self.db.refresh(setting)

        return MessageSettingInfo.model_validate(setting)

    async def update_message_settings(self, user_id: int, req: MessageSettingUpdate) -> MessageSettingInfo:
        """更新用户消息设置"""
        setting = (await self.db.execute(
            select(MessageSetting).where(MessageSetting.user_id == user_id)
        )).scalar_one_or_none()

        if not setting:
            setting = MessageSetting(user_id=user_id)
            self.db.add(setting)

        # 更新字段
        update_data = {}
        if req.allow_stranger_msg is not None:
            update_data["allow_stranger_msg"] = req.allow_stranger_msg
        if req.auto_read_receipt is not None:
            update_data["auto_read_receipt"] = req.auto_read_receipt
        if req.message_notification is not None:
            update_data["message_notification"] = req.message_notification

        await self.db.execute(
            update(MessageSetting).where(MessageSetting.user_id == user_id).values(**update_data)
        )
        await self.db.commit()

        # 刷新数据
        setting = (await self.db.execute(
            select(MessageSetting).where(MessageSetting.user_id == user_id)
        )).scalar_one()
        
        return MessageSettingInfo.model_validate(setting)

    async def delete_message(self, message_id: int, user_id: int):
        """删除消息"""
        message = (await self.db.execute(
            select(Message).where(and_(Message.id == message_id, Message.sender_id == user_id))
        )).scalar_one_or_none()

        if not message:
            raise BusinessException("消息不存在或无权限删除")

        await self.db.execute(delete(Message).where(Message.id == message_id))
        await self.db.commit()

    async def get_unread_count(self, user_id: int) -> int:
        """获取用户未读消息数"""
        result = (await self.db.execute(
            select(func.sum(MessageSession.unread_count)).where(MessageSession.user_id == user_id)
        )).scalar()
        
        return result or 0 