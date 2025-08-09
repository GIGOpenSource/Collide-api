from typing import List, Dict

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
from app.domains.comment.models import Comment
from app.domains.comment.schemas import CommentInfo, CommentQuery, CommentTreeInfo


class CommentQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_comment_by_id(self, comment_id: int) -> CommentInfo:
        stmt = select(Comment).where(Comment.id == comment_id)
        comment = (await self.db.execute(stmt)).scalar_one_or_none()
        if not comment:
            raise BusinessException("评论不存在")
        return CommentInfo.model_validate(comment)

    async def list_comments(self, query: CommentQuery, pagination: PaginationParams) -> PaginationResult[CommentInfo]:
        stmt = select(Comment)
        conditions = [
            Comment.status == "NORMAL" # 强制只查询NORMAL状态
        ]
        if query.comment_type:
            conditions.append(Comment.comment_type == query.comment_type)
        if query.target_id is not None:
            conditions.append(Comment.target_id == query.target_id)
        if query.user_id is not None:
            conditions.append(Comment.user_id == query.user_id)
        if query.parent_comment_id is not None:
            conditions.append(Comment.parent_comment_id == query.parent_comment_id)
        # if query.status:  # 移除
        #     conditions.append(Comment.status == query.status)
        
        stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Comment.create_time.desc())
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar()
        rows = (await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))).scalars().all()
        items = [CommentInfo.model_validate(r) for r in rows]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_comment_tree(self, comment_type: str, target_id: int, max_level: int = 3, max_replies_per_comment: int = 10) -> List[CommentTreeInfo]:
        stmt = select(Comment).where(and_(Comment.comment_type == comment_type, Comment.target_id == target_id, Comment.status == "NORMAL")).order_by(Comment.create_time.desc())
        all_comments = (await self.db.execute(stmt)).scalars().all()
        comment_dict: Dict[int, CommentTreeInfo] = {}
        root_comments: List[CommentTreeInfo] = []
        for c in all_comments:
            node = CommentTreeInfo.model_validate(c)
            node.children = []
            comment_dict[c.id] = node
        for c in all_comments:
            node = comment_dict[c.id]
            if c.parent_comment_id == 0:
                node.level = 0
                root_comments.append(node)
            else:
                parent = comment_dict.get(c.parent_comment_id)
                if parent and parent.level < max_level:
                    node.level = parent.level + 1
                    parent.children.append(node)
        for node in comment_dict.values():
            if len(node.children) > max_replies_per_comment:
                node.has_more_replies = True
                node.children = node.children[:max_replies_per_comment]
        return root_comments

