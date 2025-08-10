"""
内容模块测试数据生成器
生成内容、章节、付费配置等测试数据
"""
import random
import asyncio
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

# 添加项目路径
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.config import settings
from app.domains.content.models import Content, ContentChapter, ContentPayment, UserContentPurchase
from app.domains.users.models import User

fake = Faker('zh_CN')


class ContentDataGenerator:
    """内容数据生成器"""
    
    def __init__(self):
        # 创建异步数据库连接
        async_database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        self.engine = create_async_engine(async_database_url)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession)
        
        self.content_types = ["NOVEL", "COMIC", "LONG_VIDEO", "SHORT_VIDEO", "ARTICLE", "AUDIO"]
        self.content_statuses = ["DRAFT", "PUBLISHED", "OFFLINE"]
        self.review_statuses = ["PENDING", "APPROVED", "REJECTED"]
        self.payment_types = ["FREE", "COIN_PAY", "VIP_FREE", "TIME_LIMITED"]
    
    async def get_users(self, limit: int = 50) -> list:
        """获取用户列表用于生成内容"""
        async with self.AsyncSessionLocal() as session:
            stmt = select(User).limit(limit)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return [(user.id, user.nickname or user.username, user.avatar) for user in users]
    
    async def generate_content(self, users: list, count: int = 100) -> list:
        """生成内容数据"""
        print(f"正在生成 {count} 个内容...")
        contents = []
        
        categories = [
            (1, "玄幻小说"), (2, "都市小说"), (3, "科幻小说"), (4, "历史小说"),
            (5, "漫画"), (6, "动画"), (7, "科技文章"), (8, "生活文章"),
            (9, "音乐"), (10, "播客")
        ]
        
        async with self.AsyncSessionLocal() as session:
            for i in range(count):
                user_id, author_nickname, author_avatar = random.choice(users)
                content_type = random.choice(self.content_types)
                category_id, category_name = random.choice(categories)
                
                # 根据内容类型生成不同的标题
                if content_type == "NOVEL":
                    title = fake.catch_phrase() + "传奇"
                elif content_type == "COMIC":
                    title = fake.word() + "漫画"
                elif content_type == "LONG_VIDEO":
                    title = fake.sentence(nb_words=4) + "（长视频）"
                elif content_type == "SHORT_VIDEO":
                    title = fake.sentence(nb_words=3) + "（短视频）"
                elif content_type == "ARTICLE":
                    title = fake.sentence(nb_words=6)
                else:  # AUDIO
                    title = fake.word() + "音频"
                
                content = Content(
                    title=title,
                    description=fake.text(max_nb_chars=300),
                    content_type=content_type,
                    content_data=f"https://cdn.example.com/{content_type.lower()}/{fake.uuid4()}.{self._get_file_extension(content_type)}",
                    content_data_time=str(random.randint(60, 7200)),  # 1分钟到2小时
                    cover_url=fake.image_url(width=400, height=600),
                    tags=",".join(fake.words(nb=random.randint(3, 8))),
                    author_id=user_id,
                    author_nickname=author_nickname,
                    author_avatar=author_avatar,
                    category_id=category_id,
                    category_name=category_name,
                    status=random.choices(self.content_statuses, weights=[20, 70, 10])[0],
                    review_status=random.choices(self.review_statuses, weights=[10, 80, 10])[0],
                    
                    # 随机统计数据
                    view_count=random.randint(0, 50000),
                    like_count=random.randint(0, 5000),
                    comment_count=random.randint(0, 1000),
                    share_count=random.randint(0, 500),
                    favorite_count=random.randint(0, 2000),
                    score_count=random.randint(0, 1000),
                    score_total=0,  # 稍后计算
                    
                    publish_time=fake.date_time_between(start_date='-1y', end_date='now') if random.choice([True, False]) else None
                )
                
                # 计算总评分
                if content.score_count > 0:
                    content.score_total = content.score_count * random.randint(3, 5)
                
                session.add(content)
                contents.append(content)
            
            await session.commit()
            
            # 刷新以获取ID
            for content in contents:
                await session.refresh(content)
        
        print(f"✅ 成功生成 {len(contents)} 个内容")
        return contents
    
    async def generate_chapters(self, contents: list, chapters_per_content: int = 5) -> list:
        """为小说和漫画生成章节"""
        print(f"正在生成章节数据...")
        chapters = []
        
        # 筛选小说和漫画
        novel_comic_contents = [c for c in contents if c.content_type in ["NOVEL", "COMIC"]]
        
        async with self.AsyncSessionLocal() as session:
            for content in novel_comic_contents:
                chapter_count = random.randint(1, chapters_per_content)
                
                for chapter_num in range(1, chapter_count + 1):
                    chapter_title = f"第{chapter_num}章 {fake.sentence(nb_words=3)}"
                    
                    # 生成章节内容
                    if content.content_type == "NOVEL":
                        chapter_content = "\n\n".join([fake.paragraph(nb_sentences=5) for _ in range(random.randint(3, 8))])
                        word_count = len(chapter_content)
                    else:  # COMIC
                        chapter_content = f"漫画第{chapter_num}话内容，共{random.randint(10, 30)}页"
                        word_count = random.randint(100, 500)
                    
                    chapter = ContentChapter(
                        content_id=content.id,
                        chapter_num=chapter_num,
                        title=chapter_title,
                        content=chapter_content,
                        word_count=word_count,
                        status=random.choices(["DRAFT", "PUBLISHED"], weights=[20, 80])[0]
                    )
                    
                    session.add(chapter)
                    chapters.append(chapter)
            
            await session.commit()
        
        print(f"✅ 成功生成 {len(chapters)} 个章节")
        return chapters
    
    async def generate_payment_configs(self, contents: list) -> list:
        """生成付费配置"""
        print(f"正在生成付费配置...")
        payments = []
        
        # 随机选择一部分内容设置付费
        paid_contents = random.sample(contents, min(len(contents) // 2, 50))
        
        async with self.AsyncSessionLocal() as session:
            for content in paid_contents:
                payment_type = random.choice(self.payment_types)
                
                payment = ContentPayment(
                    content_id=content.id,
                    payment_type=payment_type,
                    coin_price=random.randint(10, 1000) if payment_type == "COIN_PAY" else 0,
                    original_price=random.randint(50, 2000) if random.choice([True, False]) else None,
                    vip_free=random.choice([0, 1]) if payment_type in ["COIN_PAY", "TIME_LIMITED"] else 0,
                    vip_only=random.choice([0, 1]) if payment_type == "COIN_PAY" else 0,
                    trial_enabled=random.choice([0, 1]) if content.content_type in ["NOVEL", "ARTICLE"] else 0,
                    trial_content=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                    trial_word_count=random.randint(100, 1000) if random.choice([True, False]) else 0,
                    is_permanent=random.choice([0, 1]),
                    valid_days=random.randint(30, 365) if random.choice([True, False]) else None,
                    total_sales=random.randint(0, 10000),
                    total_revenue=random.randint(0, 100000),
                    status="ACTIVE"
                )
                
                session.add(payment)
                payments.append(payment)
            
            await session.commit()
        
        print(f"✅ 成功生成 {len(payments)} 个付费配置")
        return payments
    
    async def generate_purchase_records(self, users: list, contents: list, count: int = 200) -> list:
        """生成购买记录"""
        print(f"正在生成 {count} 个购买记录...")
        purchases = []
        
        async with self.AsyncSessionLocal() as session:
            for i in range(count):
                user_id, _, _ = random.choice(users)
                content = random.choice(contents)
                
                # 检查是否已购买
                stmt = select(UserContentPurchase).where(
                    UserContentPurchase.user_id == user_id,
                    UserContentPurchase.content_id == content.id
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    continue
                
                coin_amount = random.randint(10, 500)
                
                purchase = UserContentPurchase(
                    user_id=user_id,
                    content_id=content.id,
                    content_title=content.title,
                    content_type=content.content_type,
                    content_cover_url=content.cover_url,
                    author_id=content.author_id,
                    author_nickname=content.author_nickname,
                    order_id=random.randint(100000, 999999),
                    order_no=f"ORD{fake.date_time_between(start_date='-1y').strftime('%Y%m%d')}{random.randint(100000, 999999)}",
                    coin_amount=coin_amount,
                    original_price=coin_amount + random.randint(0, 100),
                    discount_amount=random.randint(0, 50),
                    status=random.choices(["ACTIVE", "EXPIRED", "REFUNDED"], weights=[85, 10, 5])[0],
                    purchase_time=fake.date_time_between(start_date='-1y', end_date='now'),
                    expire_time=fake.date_time_between(start_date='now', end_date='+1y') if random.choice([True, False]) else None,
                    access_count=random.randint(0, 100),
                    last_access_time=fake.date_time_between(start_date='-30d', end_date='now') if random.choice([True, False]) else None
                )
                
                session.add(purchase)
                purchases.append(purchase)
            
            await session.commit()
        
        print(f"✅ 成功生成 {len(purchases)} 个购买记录")
        return purchases
    
    def _get_file_extension(self, content_type: str) -> str:
        """根据内容类型获取文件扩展名"""
        extensions = {
            "NOVEL": "txt",
            "COMIC": "cbz",
            "LONG_VIDEO": "mp4",
            "SHORT_VIDEO": "mp4",
            "ARTICLE": "html",
            "AUDIO": "mp3"
        }
        return extensions.get(content_type, "bin")
    
    async def generate_all_data(self, content_count: int = 100, chapters_per_content: int = 5, purchase_count: int = 200):
        """生成所有测试数据"""
        print("🚀 开始生成内容模块测试数据...")
        print("=" * 50)
        
        try:
            # 获取用户列表
            users = await self.get_users()
            if not users:
                print("❌ 没有找到用户数据，请先运行用户数据生成器")
                return
            
            print(f"📋 找到 {len(users)} 个用户")
            
            # 生成内容
            contents = await self.generate_content(users, content_count)
            
            # 生成章节
            await self.generate_chapters(contents, chapters_per_content)
            
            # 生成付费配置
            await self.generate_payment_configs(contents)
            
            # 生成购买记录
            await self.generate_purchase_records(users, contents, purchase_count)
            
            print("=" * 50)
            print("🎉 内容模块测试数据生成完成！")
            print(f"📊 生成统计:")
            print(f"   - 内容: {len(contents)} 个")
            print(f"   - 章节: 预计 {len([c for c in contents if c.content_type in ['NOVEL', 'COMIC']]) * chapters_per_content // 2} 个")
            print(f"   - 付费配置: 预计 {len(contents) // 2} 个")
            print(f"   - 购买记录: 预计 {purchase_count} 个")
            
        except Exception as e:
            print(f"❌ 生成测试数据时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    generator = ContentDataGenerator()
    await generator.generate_all_data(
        content_count=100,
        chapters_per_content=8,
        purchase_count=300
    )


if __name__ == "__main__":
    asyncio.run(main())
