"""
金币购买处理服务
处理内容购买、社交动态购买等金币消费业务
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.users.models import UserWallet
from app.domains.content.models import UserContentPurchase, Content
from app.domains.social.models import SocialDynamicPurchase, SocialPaidDynamic
import logging

logger = logging.getLogger(__name__)


class CoinPurchaseService:
    """金币购买处理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def purchase_content(self, user_id: int, content_id: int, coin_cost: int) -> Dict[str, Any]:
        """
        购买内容
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            coin_cost: 消耗金币数
            
        Returns:
            Dict: 购买结果
        """
        try:
            # 检查用户钱包余额
            wallet = await self._get_user_wallet(user_id)
            if wallet.coin_balance < coin_cost:
                raise BusinessException("金币余额不足")
            
            # 获取内容信息
            content = await self._get_content_by_id(content_id)
            if not content:
                raise BusinessException("内容不存在")
            
            # 检查是否已经购买过
            existing_purchase = await self._check_content_purchase(user_id, content_id)
            if existing_purchase:
                return {
                    "success": True,
                    "message": "您已购买过此内容",
                    "purchase_id": existing_purchase.id
                }
            
            # 扣除金币
            await self._deduct_coins(user_id, coin_cost)
            
            # 创建购买记录
            purchase_record = UserContentPurchase(
                user_id=user_id,
                content_id=content_id,
                content_title=content.title,
                content_type=content.content_type,
                content_cover_url=content.cover_url,
                author_id=content.author_id,
                author_nickname=content.author_nickname,
                coin_amount=coin_cost,
                status="ACTIVE",
                expire_time=None  # 内容购买默认永久有效
            )
            
            self.db.add(purchase_record)
            await self.db.commit()
            
            logger.info(f"用户 {user_id} 购买内容成功: {content.title}, 消耗金币: {coin_cost}")
            
            return {
                "success": True,
                "message": "购买成功",
                "purchase_id": purchase_record.id,
                "content_title": content.title,
                "coin_cost": coin_cost
            }
            
        except Exception as e:
            logger.error(f"购买内容失败: {str(e)}", exc_info=True)
            raise
    
    async def purchase_social_dynamic(self, user_id: int, dynamic_id: int, coin_cost: int) -> Dict[str, Any]:
        """
        购买社交动态
        
        Args:
            user_id: 用户ID
            dynamic_id: 动态ID
            coin_cost: 消耗金币数
            
        Returns:
            Dict: 购买结果
        """
        try:
            # 检查用户钱包余额
            wallet = await self._get_user_wallet(user_id)
            if wallet.coin_balance < coin_cost:
                raise BusinessException("金币余额不足")
            
            # 获取付费动态信息
            paid_dynamic = await self._get_paid_dynamic_by_id(dynamic_id)
            if not paid_dynamic:
                raise BusinessException("付费动态不存在")
            
            # 检查是否已经购买过
            existing_purchase = await self._check_dynamic_purchase(user_id, dynamic_id)
            if existing_purchase:
                return {
                    "success": True,
                    "message": "您已购买过此动态",
                    "purchase_id": existing_purchase.id
                }
            
            # 扣除金币
            await self._deduct_coins(user_id, coin_cost)
            
            # 创建购买记录
            purchase_record = SocialDynamicPurchase(
                user_id=user_id,
                dynamic_id=dynamic_id,
                coin_amount=coin_cost,
                status="ACTIVE",
                purchase_time=datetime.now()
            )
            
            self.db.add(purchase_record)
            await self.db.commit()
            
            logger.info(f"用户 {user_id} 购买动态成功: 动态ID {dynamic_id}, 消耗金币: {coin_cost}")
            
            return {
                "success": True,
                "message": "购买成功",
                "purchase_id": purchase_record.id,
                "coin_cost": coin_cost
            }
            
        except Exception as e:
            logger.error(f"购买动态失败: {str(e)}", exc_info=True)
            raise
    
    async def check_content_purchase_status(self, user_id: int, content_id: int) -> Dict[str, Any]:
        """
        检查内容购买状态
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            Dict: 购买状态信息
        """
        purchase = await self._check_content_purchase(user_id, content_id)
        if purchase:
            return {
                "has_purchased": True,
                "purchase_time": purchase.purchase_time,
                "expire_time": purchase.expire_time,
                "is_valid": purchase.status == "ACTIVE" and 
                           (purchase.expire_time is None or purchase.expire_time > datetime.now())
            }
        else:
            return {
                "has_purchased": False,
                "purchase_time": None,
                "expire_time": None,
                "is_valid": False
            }
    
    async def check_dynamic_purchase_status(self, user_id: int, dynamic_id: int) -> Dict[str, Any]:
        """
        检查动态购买状态
        
        Args:
            user_id: 用户ID
            dynamic_id: 动态ID
            
        Returns:
            Dict: 购买状态信息
        """
        purchase = await self._check_dynamic_purchase(user_id, dynamic_id)
        if purchase:
            return {
                "has_purchased": True,
                "purchase_time": purchase.purchase_time,
                "is_valid": purchase.status == "ACTIVE"
            }
        else:
            return {
                "has_purchased": False,
                "purchase_time": None,
                "is_valid": False
            }
    
    async def get_user_purchases(self, user_id: int, purchase_type: str = "content", limit: int = 20) -> list:
        """
        获取用户购买记录
        
        Args:
            user_id: 用户ID
            purchase_type: 购买类型 (content/dynamic)
            limit: 返回数量限制
            
        Returns:
            list: 购买记录列表
        """
        if purchase_type == "content":
            result = await self.db.execute(
                select(UserContentPurchase)
                .where(UserContentPurchase.user_id == user_id)
                .order_by(UserContentPurchase.purchase_time.desc())
                .limit(limit)
            )
            return result.scalars().all()
        elif purchase_type == "dynamic":
            result = await self.db.execute(
                select(SocialDynamicPurchase)
                .where(SocialDynamicPurchase.user_id == user_id)
                .order_by(SocialDynamicPurchase.purchase_time.desc())
                .limit(limit)
            )
            return result.scalars().all()
        else:
            raise BusinessException("不支持的购买类型")
    
    async def _get_user_wallet(self, user_id: int) -> UserWallet:
        """获取用户钱包"""
        result = await self.db.execute(
            select(UserWallet).where(UserWallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            # 如果钱包不存在，创建一个
            wallet = UserWallet(
                user_id=user_id,
                balance=0.00,
                frozen_amount=0.00,
                coin_balance=0,
                coin_total_earned=0,
                coin_total_spent=0,
                total_income=0.00,
                total_expense=0.00,
                status="active"
            )
            self.db.add(wallet)
            await self.db.flush()
        
        return wallet
    
    async def _deduct_coins(self, user_id: int, coin_amount: int):
        """扣除用户金币"""
        await self.db.execute(
            update(UserWallet)
            .where(UserWallet.user_id == user_id)
            .values(
                coin_balance=UserWallet.coin_balance - coin_amount,
                coin_total_spent=UserWallet.coin_total_spent + coin_amount
            )
        )
    
    async def _get_content_by_id(self, content_id: int) -> Optional[Content]:
        """根据ID获取内容"""
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_paid_dynamic_by_id(self, dynamic_id: int) -> Optional[SocialPaidDynamic]:
        """根据ID获取付费动态"""
        result = await self.db.execute(
            select(SocialPaidDynamic).where(SocialPaidDynamic.dynamic_id == dynamic_id)
        )
        return result.scalar_one_or_none()
    
    async def _check_content_purchase(self, user_id: int, content_id: int):
        """检查内容购买记录"""
        result = await self.db.execute(
            select(UserContentPurchase).where(
                and_(
                    UserContentPurchase.user_id == user_id,
                    UserContentPurchase.content_id == content_id,
                    UserContentPurchase.status == "ACTIVE"
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _check_dynamic_purchase(self, user_id: int, dynamic_id: int):
        """检查动态购买记录"""
        result = await self.db.execute(
            select(SocialDynamicPurchase).where(
                and_(
                    SocialDynamicPurchase.user_id == user_id,
                    SocialDynamicPurchase.dynamic_id == dynamic_id,
                    SocialDynamicPurchase.status == "ACTIVE"
                )
            )
        )
        return result.scalar_one_or_none() 