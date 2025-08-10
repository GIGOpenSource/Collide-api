"""
付费动态服务
"""
from typing import Optional, List
from sqlalchemy import select, insert, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.social.models import SocialDynamic, SocialPaidDynamic, SocialDynamicPurchase
from app.domains.social.schemas import PaidDynamicCreate, PaidDynamicInfo, DynamicPurchaseInfo, DynamicWithPaidInfo


class PaidDynamicService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_paid_dynamic(self, dynamic_id: int, price: int, user_id: int) -> PaidDynamicInfo:
        """创建付费动态"""
        try:
            # 检查动态是否存在且属于当前用户
            dynamic = await self.db.execute(
                select(SocialDynamic).where(
                    and_(SocialDynamic.id == dynamic_id, SocialDynamic.user_id == user_id)
                )
            )
            dynamic = dynamic.scalar_one_or_none()
            if not dynamic:
                raise BusinessException("动态不存在或无权限")
            
            # 检查是否已经是付费动态
            existing_paid = await self.db.execute(
                select(SocialPaidDynamic).where(SocialPaidDynamic.dynamic_id == dynamic_id)
            )
            if existing_paid.scalar_one_or_none():
                raise BusinessException("该动态已经是付费动态")
            
            # 创建付费动态
            paid_dynamic = SocialPaidDynamic(
                dynamic_id=dynamic_id,
                price=price
            )
            self.db.add(paid_dynamic)
            await self.db.commit()
            await self.db.refresh(paid_dynamic)
            
            return PaidDynamicInfo.model_validate(paid_dynamic)
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建付费动态失败: {str(e)}")

    async def get_paid_dynamic_info(self, dynamic_id: int) -> Optional[PaidDynamicInfo]:
        """获取付费动态信息"""
        paid_dynamic = await self.db.execute(
            select(SocialPaidDynamic).where(SocialPaidDynamic.dynamic_id == dynamic_id)
        )
        paid_dynamic = paid_dynamic.scalar_one_or_none()
        if not paid_dynamic:
            return None
        return PaidDynamicInfo.model_validate(paid_dynamic)

    async def purchase_dynamic(self, dynamic_id: int, buyer_id: int) -> DynamicPurchaseInfo:
        """购买动态"""
        try:
            # 检查付费动态是否存在
            paid_dynamic = await self.db.execute(
                select(SocialPaidDynamic).where(
                    and_(SocialPaidDynamic.dynamic_id == dynamic_id, SocialPaidDynamic.is_active == True)
                )
            )
            paid_dynamic = paid_dynamic.scalar_one_or_none()
            if not paid_dynamic:
                raise BusinessException("付费动态不存在或已下架")
            
            # 检查是否已经购买过
            existing_purchase = await self.db.execute(
                select(SocialDynamicPurchase).where(
                    and_(SocialDynamicPurchase.dynamic_id == dynamic_id, SocialDynamicPurchase.buyer_id == buyer_id)
                )
            )
            if existing_purchase.scalar_one_or_none():
                raise BusinessException("您已经购买过此动态")
            
            # 检查用户金币余额（这里需要调用用户钱包服务）
            # TODO: 调用用户钱包服务检查余额并扣除金币
            
            # 创建购买记录
            purchase = SocialDynamicPurchase(
                dynamic_id=dynamic_id,
                buyer_id=buyer_id,
                price=paid_dynamic.price
            )
            self.db.add(purchase)
            
            # 更新付费动态统计
            await self.db.execute(
                update(SocialPaidDynamic)
                .where(SocialPaidDynamic.id == paid_dynamic.id)
                .values(
                    purchase_count=SocialPaidDynamic.purchase_count + 1,
                    total_income=SocialPaidDynamic.total_income + paid_dynamic.price
                )
            )
            
            await self.db.commit()
            await self.db.refresh(purchase)
            
            return DynamicPurchaseInfo.model_validate(purchase)
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"购买动态失败: {str(e)}")

    async def check_user_purchased(self, dynamic_id: int, user_id: int) -> bool:
        """检查用户是否已购买动态"""
        purchase = await self.db.execute(
            select(SocialDynamicPurchase).where(
                and_(SocialDynamicPurchase.dynamic_id == dynamic_id, SocialDynamicPurchase.buyer_id == user_id)
            )
        )
        return purchase.scalar_one_or_none() is not None

    async def get_dynamic_with_paid_info(self, dynamic: SocialDynamic, current_user_id: Optional[int] = None) -> DynamicWithPaidInfo:
        """获取带付费信息的动态"""
        # 获取付费动态信息
        paid_info = await self.get_paid_dynamic_info(dynamic.id)
        
        # 检查用户是否已购买
        is_purchased = False
        if current_user_id and paid_info:
            is_purchased = await self.check_user_purchased(dynamic.id, current_user_id)
        
        # 构建带付费信息的动态
        dynamic_with_paid = DynamicWithPaidInfo.model_validate(dynamic)
        dynamic_with_paid.is_paid = paid_info is not None
        dynamic_with_paid.price = paid_info.price if paid_info else None
        dynamic_with_paid.is_purchased = is_purchased
        dynamic_with_paid.purchase_count = paid_info.purchase_count if paid_info else None
        
        return dynamic_with_paid

    async def get_user_purchases(self, user_id: int, limit: int = 20) -> List[DynamicPurchaseInfo]:
        """获取用户的购买记录"""
        purchases = await self.db.execute(
            select(SocialDynamicPurchase)
            .where(SocialDynamicPurchase.buyer_id == user_id)
            .order_by(SocialDynamicPurchase.purchase_time.desc())
            .limit(limit)
        )
        return [DynamicPurchaseInfo.model_validate(p) for p in purchases.scalars().all()]

    async def get_dynamic_purchases(self, dynamic_id: int, limit: int = 20) -> List[DynamicPurchaseInfo]:
        """获取动态的购买记录"""
        purchases = await self.db.execute(
            select(SocialDynamicPurchase)
            .where(SocialDynamicPurchase.dynamic_id == dynamic_id)
            .order_by(SocialDynamicPurchase.purchase_time.desc())
            .limit(limit)
        )
        return [DynamicPurchaseInfo.model_validate(p) for p in purchases.scalars().all()]

    async def deactivate_paid_dynamic(self, dynamic_id: int, user_id: int) -> bool:
        """下架付费动态"""
        try:
            # 检查权限
            paid_dynamic = await self.db.execute(
                select(SocialPaidDynamic)
                .join(SocialDynamic, SocialPaidDynamic.dynamic_id == SocialDynamic.id)
                .where(
                    and_(
                        SocialPaidDynamic.dynamic_id == dynamic_id,
                        SocialDynamic.user_id == user_id
                    )
                )
            )
            paid_dynamic = paid_dynamic.scalar_one_or_none()
            if not paid_dynamic:
                raise BusinessException("付费动态不存在或无权限")
            
            # 下架付费动态
            await self.db.execute(
                update(SocialPaidDynamic)
                .where(SocialPaidDynamic.id == paid_dynamic.id)
                .values(is_active=False)
            )
            await self.db.commit()
            return True
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"下架付费动态失败: {str(e)}") 