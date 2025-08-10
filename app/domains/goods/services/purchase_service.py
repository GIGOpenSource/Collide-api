"""
商品购买成功后的处理服务
处理VIP订阅、金币充值等商品购买后的业务逻辑
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.order.models import Order
from app.domains.users.models import User, UserRole, UserWallet, Role
from app.domains.goods.models import Goods
from app.domains.content.models import UserContentPurchase, Content


class GoodsPurchaseService:
    """商品购买处理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_purchase_success(self, order_no: str) -> dict:
        """
        处理商品购买成功后的业务逻辑
        
        Args:
            order_no: 订单号
            
        Returns:
            dict: 处理结果信息
        """
        # 获取订单信息
        order = await self._get_order_by_no(order_no)
        if not order:
            raise BusinessException("订单不存在")
        
        if order.pay_status != "paid":
            raise BusinessException("订单未支付，无法处理")
        
        # 获取商品信息
        goods = await self._get_goods_by_id(order.goods_id)
        if not goods:
            raise BusinessException("商品不存在")
        
        result = {
            "order_no": order_no,
            "user_id": order.user_id,
            "goods_id": order.goods_id,
            "goods_type": order.goods_type,
            "processed_items": []
        }
        
        # 根据商品类型处理不同的业务逻辑
        if order.goods_type == "subscription":
            # 处理订阅商品（VIP等）
            await self._process_subscription_purchase(order, goods)
            result["processed_items"].append("subscription")
            
        elif order.goods_type == "coin":
            # 处理金币商品
            await self._process_coin_purchase(order, goods)
            result["processed_items"].append("coin")
            
        elif order.goods_type == "content":
            # 处理内容商品（购买内容）
            await self._process_content_purchase(order, goods)
            result["processed_items"].append("content")
            
        elif order.goods_type == "goods":
            # 处理普通商品（实物商品）
            await self._process_goods_purchase(order, goods)
            result["processed_items"].append("goods")
        
        # 更新商品销量
        await self._update_goods_sales_count(goods.id, order.quantity)
        
        return result
    
    async def _get_order_by_no(self, order_no: str) -> Optional[Order]:
        """根据订单号获取订单"""
        result = await self.db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        return result.scalar_one_or_none()
    
    async def _get_goods_by_id(self, goods_id: int) -> Optional[Goods]:
        """根据商品ID获取商品"""
        result = await self.db.execute(
            select(Goods).where(Goods.id == goods_id)
        )
        return result.scalar_one_or_none()
    
    async def _process_subscription_purchase(self, order: Order, goods: Goods):
        """处理订阅商品购买"""
        if not goods.subscription_type or not goods.subscription_duration:
            raise BusinessException("订阅商品配置错误")
        
        # 获取用户信息
        user_result = await self.db.execute(
            select(User).where(User.id == order.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise BusinessException("用户不存在")
        
        # 计算新的VIP过期时间
        current_time = datetime.now()
        if user.vip_expire_time and user.vip_expire_time > current_time:
            # 如果VIP未过期，在现有时间基础上延长
            new_expire_time = user.vip_expire_time + timedelta(days=goods.subscription_duration)
        else:
            # 如果VIP已过期或从未购买过，从当前时间开始计算
            new_expire_time = current_time + timedelta(days=goods.subscription_duration)
        
        # 更新用户VIP过期时间
        await self.db.execute(
            update(User)
            .where(User.id == order.user_id)
            .values(vip_expire_time=new_expire_time)
        )
        
        # 获取或创建VIP角色
        vip_role = await self._get_or_create_role(goods.subscription_type.upper())
        
        # 确保用户拥有VIP角色
        await self._ensure_user_role(order.user_id, vip_role.id)
        
        await self.db.commit()
    
    async def _process_coin_purchase(self, order: Order, goods: Goods):
        """处理金币商品购买"""
        if not goods.coin_amount:
            raise BusinessException("金币商品配置错误")
        
        # 获取用户钱包
        wallet_result = await self.db.execute(
            select(UserWallet).where(UserWallet.user_id == order.user_id)
        )
        wallet = wallet_result.scalar_one_or_none()
        
        if not wallet:
            # 如果钱包不存在，创建一个
            wallet = UserWallet(
                user_id=order.user_id,
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
        
        # 计算获得的金币数量（考虑购买数量）
        earned_coins = goods.coin_amount * order.quantity
        
        # 更新钱包金币余额
        new_coin_balance = wallet.coin_balance + earned_coins
        new_coin_total_earned = wallet.coin_total_earned + earned_coins
        
        await self.db.execute(
            update(UserWallet)
            .where(UserWallet.user_id == order.user_id)
            .values(
                coin_balance=new_coin_balance,
                coin_total_earned=new_coin_total_earned
            )
        )
        
        await self.db.commit()
    
    async def _process_content_purchase(self, order: Order, goods: Goods):
        """处理内容商品购买"""
        if not goods.content_id:
            raise BusinessException("内容商品配置错误")
        
        # 获取内容信息
        content_result = await self.db.execute(
            select(Content).where(Content.id == goods.content_id)
        )
        content = content_result.scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        
        # 检查用户是否已经购买过该内容
        existing_purchase = await self.db.execute(
            select(UserContentPurchase).where(
                and_(
                    UserContentPurchase.user_id == order.user_id,
                    UserContentPurchase.content_id == goods.content_id,
                    UserContentPurchase.status == "ACTIVE"
                )
            )
        )
        if existing_purchase.scalar_one_or_none():
            # 用户已经购买过该内容，不需要重复创建记录
            return
        
        # 创建内容购买记录
        purchase_record = UserContentPurchase(
            user_id=order.user_id,
            content_id=goods.content_id,
            content_title=content.title,
            content_type=content.content_type,
            content_cover_url=content.cover_url,
            author_id=content.author_id,
            author_nickname=content.author_nickname,
            order_id=order.id,
            order_no=order.order_no,
            coin_amount=order.coin_cost,
            original_price=goods.coin_price,
            discount_amount=goods.coin_price - order.coin_cost if goods.coin_price > order.coin_cost else 0,
            status="ACTIVE",
            # 内容购买默认永久有效，除非商品配置了有效期
            expire_time=None if goods.subscription_duration is None else 
                datetime.now() + timedelta(days=goods.subscription_duration)
        )
        
        self.db.add(purchase_record)
        await self.db.commit()
    
    async def _process_goods_purchase(self, order: Order, goods: Goods):
        """处理普通商品购买"""
        # 对于普通商品，主要是库存管理
        # 库存更新已经在订单创建时处理，这里可以添加其他逻辑
        # 例如：发送通知、记录购买历史等
        pass
    
    async def _get_or_create_role(self, role_name: str) -> Role:
        """获取或创建角色"""
        # 先查找现有角色
        role_result = await self.db.execute(
            select(Role).where(Role.name == role_name)
        )
        role = role_result.scalar_one_or_none()
        
        if not role:
            # 如果角色不存在，创建一个
            role = Role(
                name=role_name,
                description=f"{role_name}用户角色"
            )
            self.db.add(role)
            await self.db.flush()
        
        return role
    
    async def _ensure_user_role(self, user_id: int, role_id: int):
        """确保用户拥有指定角色"""
        # 检查用户是否已有该角色
        user_role_result = await self.db.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            )
        )
        user_role = user_role_result.scalar_one_or_none()
        
        if not user_role:
            # 如果用户没有该角色，添加角色
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id
            )
            self.db.add(user_role)
    
    async def _update_goods_sales_count(self, goods_id: int, quantity: int):
        """更新商品销量"""
        await self.db.execute(
            update(Goods)
            .where(Goods.id == goods_id)
            .values(sales_count=Goods.sales_count + quantity)
        ) 