"""
关注状态服务
用于查询用户之间的关注关系
"""
from typing import Dict, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.follow.models import Follow


class FollowStatusService:
    """关注状态服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_follow_status_batch(self, current_user_id: int, target_user_ids: List[int]) -> Dict[int, Dict[str, bool]]:
        """
        批量获取关注状态
        
        Args:
            current_user_id: 当前用户ID
            target_user_ids: 目标用户ID列表
            
        Returns:
            Dict[int, Dict[str, bool]]: 用户ID -> 关注状态字典
        """
        if not target_user_ids:
            return {}
        
        # 查询当前用户关注了哪些人
        following_stmt = select(Follow.followee_id).where(
            and_(
                Follow.follower_id == current_user_id,
                Follow.followee_id.in_(target_user_ids),
                Follow.status == "active"
            )
        )
        following_result = await self.db.execute(following_stmt)
        following_ids = {row[0] for row in following_result.fetchall()}
        
        # 查询哪些人关注了当前用户
        followed_by_stmt = select(Follow.follower_id).where(
            and_(
                Follow.follower_id.in_(target_user_ids),
                Follow.followee_id == current_user_id,
                Follow.status == "active"
            )
        )
        followed_by_result = await self.db.execute(followed_by_stmt)
        followed_by_ids = {row[0] for row in followed_by_result.fetchall()}
        
        # 构建结果
        result = {}
        for user_id in target_user_ids:
            is_following = user_id in following_ids
            is_followed_by = user_id in followed_by_ids
            is_mutual_follow = is_following and is_followed_by
            
            result[user_id] = {
                "is_following": is_following,
                "is_followed_by": is_followed_by,
                "is_mutual_follow": is_mutual_follow
            }
        
        return result

    async def get_follow_status(self, current_user_id: int, target_user_id: int) -> Dict[str, bool]:
        """
        获取单个用户的关注状态
        
        Args:
            current_user_id: 当前用户ID
            target_user_id: 目标用户ID
            
        Returns:
            Dict[str, bool]: 关注状态字典
        """
        if current_user_id == target_user_id:
            return {
                "is_following": False,
                "is_followed_by": False,
                "is_mutual_follow": False
            }
        
        # 查询当前用户是否关注了目标用户
        following_stmt = select(Follow).where(
            and_(
                Follow.follower_id == current_user_id,
                Follow.followee_id == target_user_id,
                Follow.status == "active"
            )
        )
        following_result = await self.db.execute(following_stmt)
        is_following = following_result.scalar_one_or_none() is not None
        
        # 查询目标用户是否关注了当前用户
        followed_by_stmt = select(Follow).where(
            and_(
                Follow.follower_id == target_user_id,
                Follow.followee_id == current_user_id,
                Follow.status == "active"
            )
        )
        followed_by_result = await self.db.execute(followed_by_stmt)
        is_followed_by = followed_by_result.scalar_one_or_none() is not None
        
        return {
            "is_following": is_following,
            "is_followed_by": is_followed_by,
            "is_mutual_follow": is_following and is_followed_by
        } 