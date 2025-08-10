#!/usr/bin/env python3
"""
社交动态数据生成脚本
生成包含审核状态的测试数据
"""
import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, and_, func

from app.database.connection import get_async_db
from app.domains.social.models import SocialDynamic, SocialPaidDynamic, SocialDynamicPurchase

fake = Faker(['zh_CN'])


class SocialDataGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dynamic_types = ["text", "image", "video", "share"]
        self.review_statuses = ["PENDING", "APPROVED", "REJECTED"]
        self.statuses = ["normal", "hidden", "deleted"]

    def _generate_dynamic_content(self, dynamic_type: str) -> str:
        """根据动态类型生成内容"""
        if dynamic_type == "text":
            return fake.text(max_nb_chars=200)
        elif dynamic_type == "image":
            return fake.text(max_nb_chars=100) + " [图片]"
        elif dynamic_type == "video":
            return fake.text(max_nb_chars=100) + " [视频]"
        elif dynamic_type == "share":
            return fake.text(max_nb_chars=150) + " [分享]"
        return fake.text(max_nb_chars=200)

    def _generate_images(self, dynamic_type: str) -> str:
        """生成图片列表"""
        if dynamic_type == "image":
            image_count = random.randint(1, 6)
            images = [fake.image_url(width=400, height=300) for _ in range(image_count)]
            return str(images)
        return None

    def _generate_video_url(self, dynamic_type: str) -> str:
        """生成视频URL"""
        if dynamic_type == "video":
            return fake.url(schemes=['https']) + "/video.mp4"
        return None

    def _generate_share_info(self, dynamic_type: str) -> tuple:
        """生成分享信息"""
        if dynamic_type == "share":
            share_types = ["content", "goods"]
            share_type = random.choice(share_types)
            share_id = random.randint(1, 1000)
            share_title = fake.sentence(nb_words=6)
            return share_type, share_id, share_title
        return None, None, None

    async def generate_social_dynamics(self, user_count: int = 100, dynamic_count: int = 500):
        """生成社交动态数据"""
        print(f"开始生成 {dynamic_count} 条社交动态数据...")
        
        dynamics = []
        for i in range(dynamic_count):
            dynamic_type = random.choice(self.dynamic_types)
            user_id = random.randint(1, user_count)
            
            # 生成基础信息
            content = self._generate_dynamic_content(dynamic_type)
            images = self._generate_images(dynamic_type)
            video_url = self._generate_video_url(dynamic_type)
            share_type, share_id, share_title = self._generate_share_info(dynamic_type)
            
            # 生成用户信息
            user_nickname = fake.name()
            user_avatar = fake.image_url(width=100, height=100)
            
            # 生成统计信息
            like_count = random.randint(0, 1000)
            comment_count = random.randint(0, 200)
            share_count = random.randint(0, 50)
            
            # 生成状态信息
            status = random.choice(self.statuses)
            review_status = random.choice(self.review_statuses)
            
            # 生成时间（最近30天内）
            create_time = fake.date_time_between(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now()
            )
            update_time = create_time + timedelta(minutes=random.randint(0, 1440))
            
            dynamic = {
                "content": content,
                "dynamic_type": dynamic_type,
                "images": images,
                "video_url": video_url,
                "share_target_type": share_type,
                "share_target_id": share_id,
                "share_target_title": share_title,
                "user_id": user_id,
                "user_nickname": user_nickname,
                "user_avatar": user_avatar,
                "like_count": like_count,
                "comment_count": comment_count,
                "share_count": share_count,
                "status": status,
                "review_status": review_status,
                "create_time": create_time,
                "update_time": update_time
            }
            dynamics.append(dynamic)
            
            if (i + 1) % 100 == 0:
                print(f"已生成 {i + 1} 条动态数据")
        
        # 批量插入数据
        try:
            await self.db.execute(insert(SocialDynamic), dynamics)
            await self.db.commit()
            print(f"成功生成 {len(dynamics)} 条社交动态数据")
        except Exception as e:
            await self.db.rollback()
            print(f"生成社交动态数据失败: {e}")
            raise

    async def generate_pending_review_dynamics(self, user_count: int = 100, count: int = 50):
        """生成待审核的动态数据"""
        print(f"开始生成 {count} 条待审核动态数据...")
        
        dynamics = []
        for i in range(count):
            dynamic_type = random.choice(self.dynamic_types)
            user_id = random.randint(1, user_count)
            
            # 生成基础信息
            content = self._generate_dynamic_content(dynamic_type)
            images = self._generate_images(dynamic_type)
            video_url = self._generate_video_url(dynamic_type)
            share_type, share_id, share_title = self._generate_share_info(dynamic_type)
            
            # 生成用户信息
            user_nickname = fake.name()
            user_avatar = fake.image_url(width=100, height=100)
            
            # 生成时间（最近7天内）
            create_time = fake.date_time_between(
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now()
            )
            update_time = create_time
            
            dynamic = {
                "content": content,
                "dynamic_type": dynamic_type,
                "images": images,
                "video_url": video_url,
                "share_target_type": share_type,
                "share_target_id": share_id,
                "share_target_title": share_title,
                "user_id": user_id,
                "user_nickname": user_nickname,
                "user_avatar": user_avatar,
                "like_count": 0,
                "comment_count": 0,
                "share_count": 0,
                "status": "normal",
                "review_status": "PENDING",  # 待审核
                "create_time": create_time,
                "update_time": update_time
            }
            dynamics.append(dynamic)
        
        # 批量插入数据
        try:
            await self.db.execute(insert(SocialDynamic), dynamics)
            await self.db.commit()
            print(f"成功生成 {len(dynamics)} 条待审核动态数据")
        except Exception as e:
            await self.db.rollback()
            print(f"生成待审核动态数据失败: {e}")
            raise

    async def generate_paid_dynamics(self, dynamic_count: int = 50, paid_ratio: float = 0.1):
        """生成付费动态数据"""
        print(f"开始生成付费动态数据，付费比例: {paid_ratio}")
        
        # 获取已审核通过的动态
        approved_dynamics = await self.db.execute(
            select(SocialDynamic)
            .where(SocialDynamic.review_status == "APPROVED")
            .order_by(SocialDynamic.create_time.desc())
            .limit(int(dynamic_count / paid_ratio))
        )
        dynamics = approved_dynamics.scalars().all()
        
        if not dynamics:
            print("没有找到已审核通过的动态，跳过付费动态生成")
            return
        
        paid_count = min(len(dynamics), dynamic_count)
        selected_dynamics = random.sample(dynamics, paid_count)
        
        paid_dynamics = []
        for dynamic in selected_dynamics:
            # 检查是否已经是付费动态
            existing = await self.db.execute(
                select(SocialPaidDynamic).where(SocialPaidDynamic.dynamic_id == dynamic.id)
            )
            if existing.scalar_one_or_none():
                continue
            
            price = random.randint(10, 500)  # 10-500金币
            paid_dynamic = {
                "dynamic_id": dynamic.id,
                "price": price,
                "purchase_count": 0,
                "total_income": 0,
                "is_active": True,
                "create_time": dynamic.create_time,
                "update_time": dynamic.create_time
            }
            paid_dynamics.append(paid_dynamic)
        
        if paid_dynamics:
            try:
                await self.db.execute(insert(SocialPaidDynamic), paid_dynamics)
                await self.db.commit()
                print(f"成功生成 {len(paid_dynamics)} 条付费动态数据")
            except Exception as e:
                await self.db.rollback()
                print(f"生成付费动态数据失败: {e}")

    async def generate_purchase_records(self, user_count: int = 100, purchase_count: int = 200):
        """生成购买记录数据"""
        print(f"开始生成 {purchase_count} 条购买记录数据...")
        
        # 获取活跃的付费动态
        paid_dynamics = await self.db.execute(
            select(SocialPaidDynamic).where(SocialPaidDynamic.is_active == True)
        )
        paid_dynamics = paid_dynamics.scalars().all()
        
        if not paid_dynamics:
            print("没有找到付费动态，跳过购买记录生成")
            return
        
        purchases = []
        for i in range(purchase_count):
            paid_dynamic = random.choice(paid_dynamics)
            buyer_id = random.randint(1, user_count)
            
            # 检查是否已经购买过
            existing = await self.db.execute(
                select(SocialDynamicPurchase).where(
                    and_(SocialDynamicPurchase.dynamic_id == paid_dynamic.dynamic_id, 
                         SocialDynamicPurchase.buyer_id == buyer_id)
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            # 生成购买时间（最近30天内）
            purchase_time = fake.date_time_between(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now()
            )
            
            purchase = {
                "dynamic_id": paid_dynamic.dynamic_id,
                "buyer_id": buyer_id,
                "price": paid_dynamic.price,
                "purchase_time": purchase_time
            }
            purchases.append(purchase)
            
            if (i + 1) % 50 == 0:
                print(f"已生成 {i + 1} 条购买记录")
        
        if purchases:
            try:
                await self.db.execute(insert(SocialDynamicPurchase), purchases)
                await self.db.commit()
                print(f"成功生成 {len(purchases)} 条购买记录数据")
                
                # 更新付费动态的统计信息
                await self._update_paid_dynamic_stats()
                
            except Exception as e:
                await self.db.rollback()
                print(f"生成购买记录数据失败: {e}")

    async def _update_paid_dynamic_stats(self):
        """更新付费动态的统计信息"""
        try:
            # 获取所有付费动态的购买统计
            stats = await self.db.execute(
                select(
                    SocialDynamicPurchase.dynamic_id,
                    func.count(SocialDynamicPurchase.id).label('purchase_count'),
                    func.sum(SocialDynamicPurchase.price).label('total_income')
                )
                .group_by(SocialDynamicPurchase.dynamic_id)
            )
            
            for dynamic_id, purchase_count, total_income in stats:
                await self.db.execute(
                    update(SocialPaidDynamic)
                    .where(SocialPaidDynamic.dynamic_id == dynamic_id)
                    .values(
                        purchase_count=purchase_count,
                        total_income=total_income or 0
                    )
                )
            
            await self.db.commit()
            print("付费动态统计信息更新完成")
            
        except Exception as e:
            await self.db.rollback()
            print(f"更新付费动态统计信息失败: {e}")


async def main():
    """主函数"""
    print("=== 社交动态数据生成器 ===")
    
    # 获取数据库连接
    async for db in get_async_db():
        generator = SocialDataGenerator(db)
        
        try:
            # 生成普通动态数据
            await generator.generate_social_dynamics(user_count=100, dynamic_count=300)
            
            # 生成待审核动态数据
            await generator.generate_pending_review_dynamics(user_count=100, count=30)
            
            print("社交动态数据生成完成！")
            
            # 生成付费动态数据
            await generator.generate_paid_dynamics(dynamic_count=50, paid_ratio=0.1)
            
            # 生成购买记录数据
            await generator.generate_purchase_records(user_count=100, purchase_count=200)
            
            print("付费动态数据生成完成！")
            break
            
        except Exception as e:
            print(f"数据生成失败: {e}")
            break


if __name__ == "__main__":
    asyncio.run(main()) 