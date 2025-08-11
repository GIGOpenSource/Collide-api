from typing import List, Optional
from sqlalchemy import select, and_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
from app.domains.social.models import SocialDynamic
from app.domains.social.schemas import DynamicInfo, DynamicQuery, DynamicReviewStatusInfo, DynamicWithPaidInfo, DynamicWithFollowInfo
from app.domains.social.services.follow_status_service import FollowStatusService


class SocialQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dynamic_by_id(self, dynamic_id: int, current_user_id: Optional[int] = None) -> DynamicInfo:
        dynamic = (await self.db.execute(select(SocialDynamic).where(SocialDynamic.id == dynamic_id))).scalar_one_or_none()
        if not dynamic:
            raise BusinessException("动态不存在")
        
        # 权限检查：只有审核通过的动态才能被普通用户查看
        if dynamic.review_status != "APPROVED" and dynamic.user_id != current_user_id:
            raise BusinessException("动态不存在或无权查看")
        
        return DynamicInfo.model_validate(dynamic)

    async def list_dynamics(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[DynamicInfo]:
        stmt = select(SocialDynamic)
        conditions = []
        
        # 根据用户身份决定 review_status 的过滤策略
        is_owner_query = query.user_id and query.user_id == current_user_id
        if not is_owner_query:
            # 非作者本人查询，强制只看已审核通过的
            conditions.append(SocialDynamic.review_status == "APPROVED")
        
        if query.keyword:
            conditions.append(SocialDynamic.content.contains(query.keyword))
        if query.dynamic_type:
            conditions.append(SocialDynamic.dynamic_type == query.dynamic_type)
        if query.user_id is not None:
            conditions.append(SocialDynamic.user_id == query.user_id)
        if query.status:
            conditions.append(SocialDynamic.status == query.status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(SocialDynamic.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [DynamicInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def list_pending_review_dynamics(self, query: DynamicQuery, pagination: PaginationParams) -> PaginationResult[DynamicInfo]:
        """获取待审核的动态列表"""
        stmt = select(SocialDynamic)
        conditions = []
        
        # 只查询待审核的动态
        conditions.append(SocialDynamic.review_status == "PENDING")
        
        if query.keyword:
            conditions.append(SocialDynamic.content.contains(query.keyword))
        if query.dynamic_type:
            conditions.append(SocialDynamic.dynamic_type == query.dynamic_type)
        if query.user_id is not None:
            conditions.append(SocialDynamic.user_id == query.user_id)
        if query.status:
            conditions.append(SocialDynamic.status == query.status)
        
        stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(SocialDynamic.create_time.asc())  # 按创建时间升序，先审核早的
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [DynamicInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_dynamic_review_status(self, dynamic_ids: List[int]) -> List[DynamicReviewStatusInfo]:
        """批量查询动态审核状态"""
        if not dynamic_ids:
            return []
        
        # 查询指定动态ID的审核状态
        stmt = select(SocialDynamic).where(SocialDynamic.id.in_(dynamic_ids))
        rows = await self.db.execute(stmt)
        dynamics = rows.scalars().all()
        
        # 转换为审核状态信息
        review_status_list = []
        for dynamic in dynamics:
            review_status_info = DynamicReviewStatusInfo(
                dynamic_id=dynamic.id,
                content=dynamic.content,
                dynamic_type=dynamic.dynamic_type,
                status=dynamic.status,
                review_status=dynamic.review_status,
                create_time=dynamic.create_time,
                update_time=dynamic.update_time
            )
            review_status_list.append(review_status_info)
        
        return review_status_list

    async def list_my_dynamics(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: int, review_status: Optional[str] = None) -> PaginationResult[DynamicInfo]:
        """获取用户自己的动态列表（包括所有审核状态）"""
        stmt = select(SocialDynamic)
        conditions = []
        
        # 强制只查询当前用户的动态
        conditions.append(SocialDynamic.user_id == current_user_id)
        
        # 添加审核状态过滤
        if review_status:
            conditions.append(SocialDynamic.review_status == review_status)
        
        if query.keyword:
            conditions.append(SocialDynamic.content.contains(query.keyword))
        if query.dynamic_type:
            conditions.append(SocialDynamic.dynamic_type == query.dynamic_type)
        if query.status:
            conditions.append(SocialDynamic.status == query.status)
        
        stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(SocialDynamic.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        items = [DynamicInfo.model_validate(x) for x in rows.scalars().all()]
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_dynamic_with_paid_info(self, dynamic_id: int, current_user_id: Optional[int] = None) -> DynamicWithPaidInfo:
        """获取带付费信息的动态详情"""
        from app.domains.social.services.paid_dynamic_service import PaidDynamicService
        
        dynamic = await self.db.execute(select(SocialDynamic).where(SocialDynamic.id == dynamic_id))
        dynamic = dynamic.scalar_one_or_none()
        if not dynamic:
            raise BusinessException("动态不存在")
        
        # 权限检查：只有审核通过的动态才能被普通用户查看
        if dynamic.review_status != "APPROVED" and dynamic.user_id != current_user_id:
            raise BusinessException("动态不存在或无权查看")
        
        # 获取带付费信息的动态
        paid_service = PaidDynamicService(self.db)
        return await paid_service.get_dynamic_with_paid_info(dynamic, current_user_id)

    async def list_dynamics_with_paid_info(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[DynamicWithPaidInfo]:
        """获取带付费信息的动态列表"""
        from app.domains.social.services.paid_dynamic_service import PaidDynamicService
        
        stmt = select(SocialDynamic)
        conditions = []
        
        # 根据用户身份决定 review_status 的过滤策略
        is_owner_query = query.user_id and query.user_id == current_user_id
        if not is_owner_query:
            # 非作者本人查询，强制只看已审核通过的
            conditions.append(SocialDynamic.review_status == "APPROVED")
        
        if query.keyword:
            conditions.append(SocialDynamic.content.contains(query.keyword))
        if query.dynamic_type:
            conditions.append(SocialDynamic.dynamic_type == query.dynamic_type)
        if query.user_id is not None:
            conditions.append(SocialDynamic.user_id == query.user_id)
        if query.status:
            conditions.append(SocialDynamic.status == query.status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(SocialDynamic.create_time.desc())
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        dynamics = rows.scalars().all()
        
        # 获取带付费信息的动态列表
        paid_service = PaidDynamicService(self.db)
        items = []
        for dynamic in dynamics:
            dynamic_with_paid = await paid_service.get_dynamic_with_paid_info(dynamic, current_user_id)
            items.append(dynamic_with_paid)
        
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    def _build_sort_clause(self, query: DynamicQuery):
        """构建排序子句"""
        if not query.sort_by:
            return SocialDynamic.create_time.desc()
        
        # 获取排序字段
        sort_field_map = {
            "create_time": SocialDynamic.create_time,
            "like_count": SocialDynamic.like_count,
            "comment_count": SocialDynamic.comment_count,
            "share_count": SocialDynamic.share_count
        }
        
        sort_field = sort_field_map.get(query.sort_by, SocialDynamic.create_time)
        
        # 应用排序方向
        if query.sort_order and query.sort_order.lower() == "asc":
            return sort_field.asc()
        else:
            return sort_field.desc()

    def _build_conditions(self, query: DynamicQuery, current_user_id: Optional[int] = None):
        """构建查询条件"""
        conditions = []
        
        # 根据用户身份决定 review_status 的过滤策略
        is_owner_query = query.user_id and query.user_id == current_user_id
        if not is_owner_query:
            # 非作者本人查询，强制只看已审核通过的
            conditions.append(SocialDynamic.review_status == "APPROVED")
        
        if query.keyword:
            conditions.append(SocialDynamic.content.contains(query.keyword))
        if query.dynamic_type:
            conditions.append(SocialDynamic.dynamic_type == query.dynamic_type)
        if query.user_id is not None:
            conditions.append(SocialDynamic.user_id == query.user_id)
        if query.status:
            conditions.append(SocialDynamic.status == query.status)
        
        # 数值范围筛选
        if query.min_likes is not None:
            conditions.append(SocialDynamic.like_count >= query.min_likes)
        if query.max_likes is not None:
            conditions.append(SocialDynamic.like_count <= query.max_likes)
        if query.min_comments is not None:
            conditions.append(SocialDynamic.comment_count >= query.min_comments)
        if query.max_comments is not None:
            conditions.append(SocialDynamic.comment_count <= query.max_comments)
        if query.min_shares is not None:
            conditions.append(SocialDynamic.share_count >= query.min_shares)
        if query.max_shares is not None:
            conditions.append(SocialDynamic.share_count <= query.max_shares)
        
        return conditions

    async def list_dynamics_with_follow_info(self, query: DynamicQuery, pagination: PaginationParams, current_user_id: Optional[int] = None) -> PaginationResult[DynamicWithFollowInfo]:
        """获取带关注状态信息的动态列表"""
        stmt = select(SocialDynamic)
        
        # 构建查询条件
        conditions = self._build_conditions(query, current_user_id)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 应用排序
        stmt = stmt.order_by(self._build_sort_clause(query))
        
        # 执行查询
        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
        rows = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.limit))
        dynamics = rows.scalars().all()
        
        # 如果没有当前用户，直接返回基础信息
        if not current_user_id:
            items = [DynamicWithFollowInfo.model_validate(dynamic) for dynamic in dynamics]
            return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
        
        # 获取所有动态发布者的用户ID
        user_ids = list(set(dynamic.user_id for dynamic in dynamics))
        
        # 批量获取关注状态
        follow_service = FollowStatusService(self.db)
        follow_status_map = await follow_service.get_follow_status_batch(current_user_id, user_ids)
        
        # 构建结果
        items = []
        for dynamic in dynamics:
            # 获取基础动态信息
            dynamic_info = DynamicInfo.model_validate(dynamic)
            
            # 获取关注状态
            follow_status = follow_status_map.get(dynamic.user_id, {
                "is_following": False,
                "is_followed_by": False,
                "is_mutual_follow": False
            })
            
            # 创建带关注状态的动态信息
            dynamic_with_follow = DynamicWithFollowInfo(
                **dynamic_info.model_dump(),
                **follow_status
            )
            items.append(dynamic_with_follow)
        
        return PaginationResult.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

