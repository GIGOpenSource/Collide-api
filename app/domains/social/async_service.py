"""
社交动态模块异步服务层（门面）
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social.schemas import DynamicCreate, DynamicUpdate, DynamicInfo, DynamicQuery, DynamicReviewStatusInfo, DynamicReviewStatusQuery, DynamicReviewRequest, PaidDynamicCreate, PaidDynamicInfo, DynamicPurchaseRequest, DynamicPurchaseInfo, DynamicWithPaidInfo, DynamicWithFollowInfo
from app.common.pagination import PaginationParams, PaginationResult
from app.domains.social.services.create_service import SocialCreateService
from app.domains.social.services.update_service import SocialUpdateService
from app.domains.social.services.query_service import SocialQueryService
from app.domains.users.async_service import UserAsyncService


class SocialAsyncService:
    """社交动态异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dynamic(self, user_id: int, user_nickname: Optional[str], user_avatar: Optional[str], data: DynamicCreate) -> DynamicInfo:
        return await SocialCreateService(self.db).create_dynamic(user_id, user_nickname, user_avatar, data)

    async def update_dynamic(self, dynamic_id: int, user_id: int, data: DynamicUpdate) -> DynamicInfo:
        return await SocialUpdateService(self.db).update_dynamic(dynamic_id, user_id, data)

    async def delete_dynamic(self, dynamic_id: int, user_id: int) -> bool:
        return await SocialUpdateService(self.db).delete_dynamic(dynamic_id, user_id)

    async def get_dynamic_by_id(self, dynamic_id: int, current_user_id: Optional[int] = None) -> DynamicInfo:
        return await SocialQueryService(self.db).get_dynamic_by_id(dynamic_id, current_user_id)

    async def list_dynamics(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[DynamicInfo]:
        return await SocialQueryService(self.db).list_dynamics(query, pagination, current_user_id)

    # ================ 审核状态相关方法 ================

    async def get_dynamic_review_status(self, dynamic_ids: List[int]) -> List[DynamicReviewStatusInfo]:
        """批量查询动态审核状态"""
        return await SocialQueryService(self.db).get_dynamic_review_status(dynamic_ids)

    async def list_my_dynamics(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: int, review_status: Optional[str] = None) -> PaginationResult[DynamicInfo]:
        """获取用户自己的动态列表（包括所有审核状态）"""
        return await SocialQueryService(self.db).list_my_dynamics(query, pagination, current_user_id, review_status)

    async def review_dynamic(self, dynamic_id: int, review_data: DynamicReviewRequest) -> DynamicInfo:
        """审核动态"""
        from app.domains.social.services.update_service import SocialUpdateService
        return await SocialUpdateService(self.db).review_dynamic(dynamic_id, review_data)

    async def list_pending_review_dynamics(self, query: DynamicQuery, pagination: PaginationParams) -> PaginationResult[DynamicInfo]:
        """获取待审核的动态列表"""
        return await SocialQueryService(self.db).list_pending_review_dynamics(query, pagination)

    # ================ 付费动态相关方法 ================

    async def create_paid_dynamic(self, dynamic_id: int, price: int, user_id: int) -> PaidDynamicInfo:
        """创建付费动态"""
        from app.domains.social.services.paid_dynamic_service import PaidDynamicService
        return await PaidDynamicService(self.db).create_paid_dynamic(dynamic_id, price, user_id)

    async def purchase_dynamic(self, dynamic_id: int, buyer_id: int) -> DynamicPurchaseInfo:
        """购买动态（使用金币）"""
        # 获取付费动态信息
        from app.domains.social.services.paid_dynamic_service import PaidDynamicService
        paid_dynamic_service = PaidDynamicService(self.db)
        paid_dynamic = await paid_dynamic_service.get_paid_dynamic_by_id(dynamic_id)
        if not paid_dynamic:
            from app.common.exceptions import BusinessException
            raise BusinessException("付费动态不存在")
        
        # 使用用户钱包服务购买
        user_service = UserAsyncService(self.db)
        result = await user_service.purchase_social_dynamic_with_coins(buyer_id, dynamic_id, paid_dynamic.coin_price)
        
        if result["success"]:
            # 创建购买记录
            purchase_info = DynamicPurchaseInfo(
                id=result["purchase_id"],
                user_id=buyer_id,
                dynamic_id=dynamic_id,
                coin_amount=paid_dynamic.coin_price,
                purchase_time=datetime.now(),
                status="ACTIVE"
            )
            return purchase_info
        else:
            from app.common.exceptions import BusinessException
            raise BusinessException(result.get("message", "购买失败"))

    async def get_dynamic_with_paid_info(self, dynamic_id: int, current_user_id: Optional[int] = None) -> DynamicWithPaidInfo:
        """获取带付费信息的动态详情"""
        return await SocialQueryService(self.db).get_dynamic_with_paid_info(dynamic_id, current_user_id)

    async def list_dynamics_with_paid_info(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[DynamicWithPaidInfo]:
        """获取带付费信息的动态列表"""
        return await SocialQueryService(self.db).list_dynamics_with_paid_info(query, pagination, current_user_id)

    async def list_dynamics_with_follow_info(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[DynamicWithFollowInfo]:
        """获取带关注状态信息的动态列表"""
        return await SocialQueryService(self.db).list_dynamics_with_follow_info(query, pagination, current_user_id)

    async def get_user_purchases(self, user_id: int, limit: int = 20) -> List[DynamicPurchaseInfo]:
        """获取用户的购买记录"""
        from app.domains.social.services.paid_dynamic_service import PaidDynamicService
        return await PaidDynamicService(self.db).get_user_purchases(user_id, limit)

    async def deactivate_paid_dynamic(self, dynamic_id: int, user_id: int) -> bool:
        """下架付费动态"""
        from app.domains.social.services.paid_dynamic_service import PaidDynamicService
        return await PaidDynamicService(self.db).deactivate_paid_dynamic(dynamic_id, user_id)

    # ================ 动态购买状态检查 ================
    
    async def check_dynamic_purchase_status(self, user_id: int, dynamic_id: int):
        """检查动态购买状态"""
        user_service = UserAsyncService(self.db)
        return await user_service.check_dynamic_purchase_status(user_id, dynamic_id)
    
    async def get_user_dynamic_purchases(self, user_id: int, limit: int = 20):
        """获取用户动态购买记录"""
        user_service = UserAsyncService(self.db)
        return await user_service.get_user_purchases(user_id, "dynamic", limit)

