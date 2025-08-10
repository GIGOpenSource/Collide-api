"""
综合假数据生成器
为所有模块生成关联的假数据，确保数据之间的关联性和一致性
"""
import os
import sys
import random
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import OperationalError

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 设置工作目录为项目根目录，确保能找到.env文件
os.chdir(project_root)

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, insert, and_, text
from passlib.context import CryptContext

from app.common.config import settings
from app.domains.users.models import User, UserWallet, UserBlock, Role, UserRole, BloggerApplication
from app.domains.content.models import Content, ContentChapter, ContentPayment, UserContentPurchase
from app.domains.category.models import Category
from app.domains.comment.models import Comment
from app.domains.like.models import Like
from app.domains.follow.models import Follow
from app.domains.favorite.models import Favorite
from app.domains.tag.models import Tag, ContentTag, UserInterestTag
from app.domains.goods.models import Goods
from app.domains.social.models import SocialDynamic, SocialPaidDynamic, SocialDynamicPurchase
from app.domains.message.models import Message, MessageSession, MessageSetting
from app.domains.order.models import Order
from app.domains.payment.models import PaymentChannel, PaymentOrder, PaymentNotifyLog, PaymentStatistics
from app.domains.payment.request_log_models import PaymentRequestLog
from app.domains.search.models import SearchHistory, HotSearch
from app.domains.task.models import TaskTemplate, TaskReward, UserTaskRecord, UserRewardRecord
from app.domains.ads.models import Ad

# 初始化Faker，使用中文本地化
fake = Faker(['zh_CN', 'en_US'])
Faker.seed(42)  # 设置随机种子，确保可重现的数据

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ComprehensiveDataGenerator:
    """综合假数据生成器"""
    
    def __init__(self):
        # 创建异步数据库连接
        async_database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        self.async_database_url = async_database_url
        self._create_engine()
        
        # 数据存储
        self.users: List[User] = []
        self.categories: List[Category] = []
        self.contents: List[Content] = []
        self.chapters: List[ContentChapter] = []
        self.comments: List[Comment] = []
        self.likes: List[Like] = []
        self.follows: List[Follow] = []
        self.favorites: List[Favorite] = []
        self.tags: List[Tag] = []
        self.goods: List[Goods] = []
        self.roles: Dict[str, Role] = {}
        self.social_dynamics: List[SocialDynamic] = [] # 新增：用于点赞动态
    
    def _create_engine(self):
        """创建或重建引擎，启用连接健康检查与回收"""
        self.engine = create_async_engine(
            self.async_database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 10},
        )
        self.AsyncSessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def _commit_with_retry(self, session: AsyncSession, max_retries: int = 3):
        """提交带重试，处理网络抖动导致的断线"""
        attempt = 0
        while True:
            try:
                await session.commit()
                return
            except OperationalError as e:
                attempt += 1
                message = str(e)
                if attempt <= max_retries and ("(2013," in message or "server has gone away" in message or "Lost connection" in message):
                    try:
                        await self.engine.dispose()
                    except Exception:
                        pass
                    # 重建引擎与会话工厂
                    self._create_engine()
                    await asyncio.sleep(0.5 * attempt)
                    continue
                raise

    async def _execute_with_retry(self, sql: str, max_retries: int = 3):
        """使用独立会话执行SQL，支持断线重试"""
        attempt = 0
        while True:
            try:
                async with self.AsyncSessionLocal() as session:
                    await session.execute(text(sql))
                    await self._commit_with_retry(session)
                return
            except OperationalError as e:
                attempt += 1
                message = str(e)
                if attempt <= max_retries and ("(2013," in message or "server has gone away" in message or "Lost connection" in message):
                    try:
                        await self.engine.dispose()
                    except Exception:
                        pass
                    self._create_engine()
                    await asyncio.sleep(0.5 * attempt)
                    continue
                raise

    def _hash_password(self, password: str) -> str:
        """密码加密"""
        return pwd_context.hash(password)
    
    def _generate_invite_code(self) -> str:
        """生成唯一邀请码"""
        import string
        import secrets
        
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            return code
    
    async def clear_database(self):
        """清空数据库中的所有数据"""
        print("正在清空数据库...")
        try:
            await self._execute_with_retry("SET FOREIGN_KEY_CHECKS=0")
            tables_to_clear = [
                # 业务表（按依赖从子到父）
                't_user_content_purchase', 't_content_payment', 't_content_chapter',
                't_like', 't_favorite', 't_follow', 't_comment',
                't_content_tag', 't_user_interest_tag', 't_tag',
                't_goods',
                't_social_dynamic_purchase', 't_social_paid_dynamic', 't_social_dynamic',
                't_message_session', 't_message_setting', 't_message',
                't_order',
                't_payment_notify_log', 't_payment_request_log', 't_payment_statistics', 't_payment_order', 't_payment_channel',
                't_search_history', 't_hot_search',
                't_user_reward_record', 't_task_reward', 't_user_task_record', 't_task_template',
                't_ad',
                't_content', 't_category',
                't_blogger_application', 't_user_role', 't_user_block', 't_user_wallet', 't_user', 't_role'
            ]
            for table in tables_to_clear:
                try:
                    await self._execute_with_retry(f"TRUNCATE TABLE {table}")
                    print(f"已清空表: {table}")
                except Exception as e:
                    print(f"清空表 {table} 时出错: {e}")
        except Exception as e:
            print(f"清库过程中出错: {e}")
        finally:
            try:
                await self._execute_with_retry("SET FOREIGN_KEY_CHECKS=1")
            except Exception:
                pass
    
    async def _ensure_roles_exist(self, session: AsyncSession):
        """确保角色存在于数据库中，如果不存在则创建"""
        if self.roles:
            return

        print("正在检查并创建角色...")
        role_definitions = [
            {'name': 'user', 'description': '普通用户'},
            {'name': 'blogger', 'description': '博主/内容创作者'},
            {'name': 'admin', 'description': '管理员'},
            {'name': 'vip', 'description': '会员用户'}
        ]
        
        existing_roles = (await session.execute(select(Role))).scalars().all()
        existing_role_map = {role.name: role for role in existing_roles}
        
        new_roles = []
        for role_def in role_definitions:
            if role_def['name'] not in existing_role_map:
                new_roles.append(Role(name=role_def['name'], description=role_def['description']))

        if new_roles:
            session.add_all(new_roles)
            await self._commit_with_retry(session)
            print(f"成功创建 {len(new_roles)} 个新角色。")
        
        # 重新加载所有角色到内存
        all_roles = (await session.execute(select(Role))).scalars().all()
        self.roles = {role.name: role for role in all_roles}
        print("角色加载完成。")

    async def generate_users(self, count: int = 100) -> List[User]:
        """生成用户数据，并关联钱包、角色、申请等"""
        print(f"正在生成 {count} 个用户...")
        
        users = []
        role_names = ['user', 'blogger', 'admin', 'vip']
        statuses = ['active', 'inactive', 'suspended', 'banned']
        genders = ['male', 'female', 'unknown']
        
        async with self.AsyncSessionLocal() as session:
            await self._ensure_roles_exist(session)
            
            for i in range(count):
                username = f"user_{fake.user_name()}_{random.randint(1000, 9999)}_{i}"
                email = f"{fake.user_name()}_{random.randint(1000, 9999)}_{i}@example.com"
                phone = f"1{random.randint(3, 9):01d}{random.randint(10000000, 99999999):08d}"
                user_role_name = random.choices(role_names, weights=[70, 20, 5, 5])[0]
                user_status = random.choices(statuses, weights=[85, 5, 5, 5])[0]

                user = User(
                    username=username,
                    nickname=fake.name(),
                    avatar=fake.image_url(width=200, height=200) if random.choice([True, False]) else None,
                    email=email,
                    phone=phone,
                    password_hash=self._hash_password("123456"),
                    status=user_status,
                    bio=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                    birthday=fake.date_of_birth(minimum_age=16, maximum_age=80) if random.choice([True, False]) else None,
                    gender=random.choice(genders),
                    location=fake.city() if random.choice([True, False]) else None,
                    follower_count=random.randint(0, 10000),
                    following_count=random.randint(0, 1000),
                    content_count=random.randint(0, 500),
                    like_count=random.randint(0, 5000),
                    vip_expire_time=(
                        datetime.now() + timedelta(days=random.randint(30, 365))
                        if user_role_name == 'vip'
                        else None
                    ),
                    last_login_time=fake.date_time_between(start_date='-30d', end_date='now'),
                    login_count=random.randint(1, 1000),
                    invite_code=self._generate_invite_code(),
                    inviter_id=random.choice(self.users).id if self.users and random.choice([True, False]) else None,
                    invited_count=random.randint(0, 50),
                    create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                    update_time=datetime.now()
                )
                session.add(user)
                users.append(user)

            await self._commit_with_retry(session)

            # Refresh users to get IDs and create related data
            for user in users:
                await session.refresh(user)

                wallet = UserWallet(user_id=user.id, balance=Decimal(random.uniform(0, 1000)).quantize(Decimal("0.01")))
                session.add(wallet)

                role = self.roles.get(user_role_name)
                if role:
                    user_role_assoc = UserRole(user_id=user.id, role_id=role.id)
                    session.add(user_role_assoc)

                if user_role_name == 'blogger' and random.choice([True, False]):
                    application = BloggerApplication(user_id=user.id, status=random.choice(['PENDING', 'APPROVED', 'REJECTED']))
                    session.add(application)

            await self._commit_with_retry(session)

        self.users = users
        print(f"成功生成 {len(users)} 个用户及其关联数据")
        return users
    
    async def generate_categories(self, count: int = 20) -> List[Category]:
        """生成分类数据"""
        print(f"正在生成 {count} 个分类...")
        
        categories = []
        category_names = [
            "玄幻小说", "都市小说", "科幻小说", "历史小说", "武侠小说",
            "漫画", "动画", "科技文章", "生活文章", "音乐",
            "播客", "游戏", "美食", "旅游", "时尚",
            "健康", "教育", "娱乐", "体育", "财经"
        ]
        
        async with self.AsyncSessionLocal() as session:
            for i in range(min(count, len(category_names))):
                category = Category(
                    name=category_names[i],
                    description=fake.text(max_nb_chars=200),
                    parent_id=0,  # 假设都是顶级分类
                    icon_url=fake.image_url(width=100, height=100),
                    sort=random.randint(1, 100),
                    content_count=random.randint(0, 1000),
                    status=random.choices(['active', 'inactive'], weights=[80, 20])[0],
                    create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                    update_time=datetime.now()
                )
                categories.append(category)
            
            session.add_all(categories)
            await self._commit_with_retry(session)
            
            
            self.categories = categories
            print(f"成功生成 {len(categories)} 个分类")
            return categories
    
    async def generate_contents(self, count: int = 200) -> List[Content]:
        """生成内容数据，并关联付费配置"""
        print(f"正在生成 {count} 个内容...")
        
        if not self.users or not self.categories or not self.tags:
            raise ValueError("请先生成用户、分类和标签数据")
        
        contents = []
        content_types = ["NOVEL", "COMIC", "LONG_VIDEO", "SHORT_VIDEO", "ARTICLE", "AUDIO"]
        content_statuses = ["DRAFT", "PUBLISHED", "OFFLINE"]
        review_statuses = ["PENDING", "APPROVED", "REJECTED"]
        payment_types = ['FREE', 'COIN_PAY', 'VIP_FREE']

        async with self.AsyncSessionLocal() as session:
            for i in range(count):
                user = random.choice(self.users)
                category = random.choice(self.categories)
                content_type = random.choice(content_types)
                
                # 根据内容类型生成标题
                if content_type == "NOVEL":
                    title = fake.catch_phrase() + "传奇"
                elif content_type == "COMIC":
                    title = fake.word() + "漫画"
                else:
                    title = fake.sentence(nb_words=6)

                content = Content(
                    title=title,
                    description=fake.text(max_nb_chars=300),
                    content_type=content_type,
                    content_data=f"https://cdn.example.com/{content_type.lower()}/{fake.uuid4()}",
                    content_data_time=str(random.randint(30, 7200)) if content_type in ['LONG_VIDEO', 'SHORT_VIDEO', 'AUDIO'] else None,  # 添加缺失的content_data_time字段
                    cover_url=fake.image_url(width=400, height=600),
                    tags=",".join(t.name for t in random.sample(self.tags, random.randint(1, 5))),
                    author_id=user.id,
                    author_nickname=user.nickname,
                    author_avatar=user.avatar,
                    category_id=category.id,
                    category_name=category.name,
                    status=random.choices(content_statuses, weights=[20, 70, 10])[0],
                    review_status=random.choices(review_statuses, weights=[10, 80, 10])[0],
                    view_count=random.randint(0, 50000),
                    like_count=random.randint(0, 5000),
                    comment_count=random.randint(0, 1000),
                    share_count=random.randint(0, 500),
                    favorite_count=random.randint(0, 2000),
                    publish_time=fake.date_time_between(start_date='-180d', end_date='now') if random.choice([True, False]) else None,
                )
                
                session.add(content)
                await session.flush()
                await session.refresh(content)

                # 创建付费配置
                payment_type = random.choice(payment_types)
                coin_price = 0
                if payment_type == 'COIN_PAY':
                    coin_price = random.randint(10, 500)

                payment_config = ContentPayment(
                    content_id=content.id,
                    payment_type=payment_type,
                    coin_price=coin_price,
                    original_price=coin_price + random.randint(0, 50) if coin_price > 0 else None,  # 添加缺失的original_price字段
                    vip_free=1 if payment_type == 'VIP_FREE' else 0,
                    trial_enabled=1 if content_type in ['NOVEL', 'ARTICLE'] else 0,
                )
                session.add(payment_config)
                contents.append(content)
            
            await self._commit_with_retry(session)
            
            self.contents = contents
            print(f"成功生成 {len(contents)} 个内容及其付费配置")
            return contents
    
    async def generate_chapters(self, chapters_per_content: int = 5) -> List[ContentChapter]:
        """生成章节数据"""
        print(f"正在为每个内容生成 {chapters_per_content} 个章节...")
        
        if not self.contents:
            raise ValueError("请先生成内容数据")
        
        chapters = []
        chapter_statuses = ["DRAFT", "PUBLISHED"]
        
        async with self.AsyncSessionLocal() as session:
            for content in self.contents:
                if content.content_type in ["NOVEL", "COMIC"]:
                    for i in range(chapters_per_content):
                        word_count = random.randint(1000, 5000)
                        chapter = ContentChapter(
                            content_id=content.id,
                            chapter_num=i + 1,
                            title=f"第{i + 1}章 {fake.sentence(nb_words=4)}",
                            content=fake.text(max_nb_chars=word_count),
                            word_count=word_count,
                            status=random.choices(chapter_statuses, weights=[20, 80])[0],
                        )
                        chapters.append(chapter)
            
            if chapters:
                session.add_all(chapters)
                await self._commit_with_retry(session)
            
            self.chapters = chapters
            print(f"成功生成 {len(chapters)} 个章节")
            return chapters
    
    async def generate_comments(self, count: int = 500) -> List[Comment]:
        """生成评论数据"""
        print(f"正在生成 {count} 个评论...")
        
        if not self.users or not self.contents:
            raise ValueError("请先生成用户和内容数据")
        
        comments = []
        comment_types = ["content", "dynamic"]
        
        async with self.AsyncSessionLocal() as session:
            for i in range(count):
                user = random.choice(self.users)
                comment_type_choice = random.choice(comment_types)
                
                target_id = None
                parent_id = 0
                reply_to_user_id = None
                reply_to_user_nickname = None
                reply_to_user_avatar = None

                if comment_type_choice == "content":
                    target = random.choice(self.contents)
                    target_id = target.id
                elif comment_type_choice == "dynamic" and hasattr(self, 'social_dynamics') and self.social_dynamics:
                    target = random.choice(self.social_dynamics)
                    target_id = target.id
                else:
                    continue # Skip if no target available

                # Decide if it's a reply
                if self.comments and random.random() < 0.3: # 30% chance to be a reply
                    parent_comment = random.choice([c for c in self.comments if c.target_id == target_id])
                    if parent_comment:
                        parent_id = parent_comment.id
                        reply_to_user = next((u for u in self.users if u.id == parent_comment.user_id), None)
                        if reply_to_user:
                            reply_to_user_id = reply_to_user.id
                            reply_to_user_nickname = reply_to_user.nickname
                            reply_to_user_avatar = reply_to_user.avatar

                comment = Comment(
                    user_id=user.id,
                    user_nickname=user.nickname,
                    user_avatar=user.avatar,
                    comment_type=comment_type_choice.upper(),
                    target_id=target_id,
                    parent_comment_id=parent_id,
                    reply_to_user_id=reply_to_user_id,
                    reply_to_user_nickname=reply_to_user_nickname,
                    reply_to_user_avatar=reply_to_user_avatar,
                    content=fake.text(max_nb_chars=200),
                    like_count=random.randint(0, 100),
                    reply_count=random.randint(0, 20),
                    status=random.choices(['NORMAL', 'HIDDEN', 'DELETED'], weights=[95, 3, 2])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                comments.append(comment)
            
            if comments:
                session.add_all(comments)
                await self._commit_with_retry(session)
            
            self.comments = comments
            print(f"成功生成 {len(comments)} 个评论")
            return comments
    
    async def generate_likes(self, count: int = 1000) -> List[Like]:
        """生成点赞数据"""
        print(f"正在生成 {count} 个点赞...")
        
        if not self.users or not self.contents:
            raise ValueError("请先生成用户和内容数据")
        
        likes = []
        like_types = ["content", "comment", "dynamic"]
        
        async with self.AsyncSessionLocal() as session:
            # 创建所有可能的点赞组合
            all_like_combinations = []
            
            # 内容点赞组合
            for user in self.users:
                for content in self.contents:
                    all_like_combinations.append((user.id, "content", content.id, content.title, content.author_id))
            
            # 评论点赞组合
            if self.comments:
                for user in self.users:
                    for comment in self.comments:
                        all_like_combinations.append((user.id, "comment", comment.id, comment.content[:50], comment.user_id))

            # 动态点赞组合
            if hasattr(self, 'social_dynamics') and self.social_dynamics:
                for user in self.users:
                    for dynamic in self.social_dynamics:
                        all_like_combinations.append((user.id, "dynamic", dynamic.id, dynamic.content[:50], dynamic.user_id))
            
            # 随机选择指定数量的点赞
            if len(all_like_combinations) > count:
                selected_combinations = random.sample(all_like_combinations, count)
            else:
                selected_combinations = all_like_combinations
            
            for user_id, like_type, target_id, target_title, target_author_id in selected_combinations:
                user = next((u for u in self.users if u.id == user_id), None)
                if not user: continue
                
                like = Like(
                    user_id=user_id,
                    user_nickname=user.nickname,
                    user_avatar=user.avatar,
                    like_type=like_type.upper(),
                    target_id=target_id,
                    target_title=target_title,
                    target_author_id=target_author_id,
                    status=random.choices(['active', 'cancelled'], weights=[90, 10])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                likes.append(like)
            
            if likes:
                session.add_all(likes)
                await self._commit_with_retry(session)
            
            
            self.likes = likes
            print(f"成功生成 {len(likes)} 个点赞")
            return likes
    
    async def generate_follows(self, count: int = 800) -> List[Follow]:
        """生成关注数据"""
        print(f"正在生成 {count} 个关注...")
        
        if not self.users:
            raise ValueError("请先生成用户数据")
        
        follows = []
        
        async with self.AsyncSessionLocal() as session:
            # 创建所有可能的关注组合（排除自己关注自己）
            all_follow_combinations = []
            for follower in self.users:
                for followee in self.users:
                    if follower.id != followee.id:
                        all_follow_combinations.append((follower.id, followee.id))
            
            # 随机选择指定数量的关注
            if len(all_follow_combinations) > count:
                selected_combinations = random.sample(all_follow_combinations, count)
            else:
                selected_combinations = all_follow_combinations
            
            for follower_id, followee_id in selected_combinations:
                follower = next(u for u in self.users if u.id == follower_id)
                followee = next(u for u in self.users if u.id == followee_id)
                
                follow = Follow(
                    follower_id=follower_id,
                    follower_nickname=follower.nickname,
                    follower_avatar=follower.avatar,
                    followee_id=followee_id,
                    followee_nickname=followee.nickname,
                    followee_avatar=followee.avatar,
                    status=random.choices(['active', 'cancelled'], weights=[90, 10])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                follows.append(follow)
            
            session.add_all(follows)
            await self._commit_with_retry(session)
            
            
            self.follows = follows
            print(f"成功生成 {len(follows)} 个关注")
            return follows
    
    async def generate_favorites(self, count: int = 600) -> List[Favorite]:
        """生成收藏数据"""
        print(f"正在生成 {count} 个收藏...")
        
        if not self.users or not self.contents:
            raise ValueError("请先生成用户和内容数据")
        
        favorites = []
        favorite_types = ["content", "goods"]
        
        async with self.AsyncSessionLocal() as session:
            # 创建所有可能的收藏组合
            all_favorite_combinations = []
            
            # 内容收藏组合
            for user in self.users:
                for content in self.contents:
                    all_favorite_combinations.append((user.id, "content", content.id, content.title, content.cover_url, content.author_id))
            
            # 商品收藏组合
            if self.goods:
                for user in self.users:
                    for good in self.goods:
                        all_favorite_combinations.append((user.id, "goods", good.id, good.name, good.cover_url, good.seller_id))

            # 随机选择指定数量的收藏
            if len(all_favorite_combinations) > count:
                selected_combinations = random.sample(all_favorite_combinations, count)
            else:
                selected_combinations = all_favorite_combinations
            
            for user_id, favorite_type, target_id, target_title, target_cover, target_author_id in selected_combinations:
                user = next((u for u in self.users if u.id == user_id), None)
                if not user: continue
                
                favorite = Favorite(
                    user_id=user_id,
                    user_nickname=user.nickname,
                    favorite_type=favorite_type.upper(),
                    target_id=target_id,
                    target_title=target_title,
                    target_cover=target_cover,
                    target_author_id=target_author_id,
                    status=random.choices(['active', 'cancelled'], weights=[90, 10])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                favorites.append(favorite)
            
            if favorites:
                session.add_all(favorites)
                await self._commit_with_retry(session)
            
            
            self.favorites = favorites
            print(f"成功生成 {len(favorites)} 个收藏")
            return favorites
    
    async def generate_tags(self, count: int = 50) -> List[Tag]:
        """生成标签数据"""
        print(f"正在生成 {count} 个标签...")
        
        tags = []
        tag_names = [
            "热门", "推荐", "精选", "新作", "完结", "连载", "免费", "付费",
            "玄幻", "都市", "科幻", "历史", "武侠", "仙侠", "游戏", "现实",
            "爱情", "友情", "亲情", "职场", "校园", "古代", "现代", "未来",
            "冒险", "悬疑", "恐怖", "喜剧", "悲剧", "励志", "治愈", "热血",
            "萌系", "御姐", "萝莉", "正太", "大叔", "女王", "王子", "公主",
            "机甲", "魔法", "修仙", "异能", "重生", "穿越", "系统", "无限"
        ]
        tag_types = ["content", "interest", "system"]
        
        async with self.AsyncSessionLocal() as session:
            for i in range(min(count, len(tag_names))):
                name = tag_names[i]
                tag_type = random.choice(tag_types)
                category = random.choice(self.categories) if self.categories else None
                
                tag = Tag(
                    name=name,
                    description=fake.text(max_nb_chars=100),
                    tag_type=tag_type,
                    category_id=category.id if category else None,
                    usage_count=random.randint(0, 1000),
                    status=random.choices(['active', 'inactive'], weights=[80, 20])[0],
                    create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                    update_time=datetime.now()
                )
                tags.append(tag)
            
            if tags:
                session.add_all(tags)
                await self._commit_with_retry(session)
            
            
            self.tags = tags
            print(f"成功生成 {len(tags)} 个标签")
            return tags
    
    async def generate_content_tags(self):
        """为内容随机关联标签"""
        print("正在为内容关联标签...")
        if not self.contents or not self.tags:
            print("缺少内容或标签数据，跳过关联。")
            return

        content_tags = []
        content_tag_set = set()

        async with self.AsyncSessionLocal() as session:
            for content in self.contents:
                # 为每篇内容关联1-5个标签
                selected_tags = random.sample(self.tags, random.randint(1, 5))
                for tag in selected_tags:
                    if (content.id, tag.id) not in content_tag_set:
                        content_tags.append(ContentTag(content_id=content.id, tag_id=tag.id))
                        content_tag_set.add((content.id, tag.id))
            
            if content_tags:
                session.add_all(content_tags)
                await self._commit_with_retry(session)
            
            print(f"成功关联 {len(content_tags)} 个内容标签。")

    async def generate_user_interest_tags(self):
        """为用户随机关联兴趣标签"""
        print("正在为用户关联兴趣标签...")
        if not self.users or not self.tags:
            print("缺少用户或标签数据，跳过关联。")
            return

        user_tags = []
        user_tag_set = set()

        async with self.AsyncSessionLocal() as session:
            for user in self.users:
                # 为每个用户关联3-10个兴趣标签
                selected_tags = random.sample(self.tags, random.randint(3, 10))
                for tag in selected_tags:
                    if (user.id, tag.id) not in user_tag_set:
                        user_tags.append(UserInterestTag(
                            user_id=user.id, 
                            tag_id=tag.id,
                            interest_score=Decimal(random.uniform(30, 100)).quantize(Decimal("0.01"))
                        ))
                        user_tag_set.add((user.id, tag.id))

            if user_tags:
                session.add_all(user_tags)
                await self._commit_with_retry(session)

            print(f"成功关联 {len(user_tags)} 个用户兴趣标签。")

    async def generate_goods(self, count: int = 100) -> List[Goods]:
        """生成商品数据"""
        print(f"正在生成 {count} 个商品...")
        
        if not self.categories:
            raise ValueError("请先生成分类数据")
        
        goods = []
        goods_types = ["coin", "content", "subscription", "goods"]
        goods_names = [
            "金币包", "VIP会员", "高级内容", "限定商品", "新手礼包", "成长基金",
            "月卡", "季卡", "年卡", "永久会员", "专属头像", "专属背景",
            "加速卡", "经验卡", "道具包", "皮肤包", "表情包", "音效包"
        ]
        
        async with self.AsyncSessionLocal() as session:
            for i in range(count):
                category = random.choice(self.categories)
                goods_type = random.choice(goods_types)
                goods_name = random.choice(goods_names)
                
                price = Decimal(random.uniform(1, 1000)).quantize(Decimal("0.01"))
                original_price = price + Decimal(random.uniform(0, 200)).quantize(Decimal("0.01"))
                coin_price = 0
                
                # 关联一个卖家（随机选择一个用户作为商家）
                seller = random.choice(self.users) if self.users else None

                # 不同类型的字段填充
                coin_amount = None
                content_id = None
                content_title = None
                subscription_duration = None
                subscription_type = None
                
                if goods_type == "coin":
                    coin_amount = random.randint(10, 10000)
                    price = Decimal(random.uniform(1, 100)).quantize(Decimal("0.01"))
                    original_price = price + Decimal(random.uniform(0, 20)).quantize(Decimal("0.01"))
                elif goods_type == "content" and self.contents:
                    linked = random.choice(self.contents)
                    content_id = linked.id
                    content_title = linked.title
                    coin_price = random.randint(10, 500)
                    price = Decimal(0)
                    original_price = Decimal(0)
                elif goods_type == "subscription":
                    subscription_duration = random.choice([7, 30, 90, 180, 365])
                    subscription_type = random.choice(["VIP", "PREMIUM"])
                    price = Decimal(random.uniform(10, 100)).quantize(Decimal("0.01"))
                    original_price = price + Decimal(random.uniform(0, 50)).quantize(Decimal("0.01"))

                goods_item = Goods(
                    name=goods_name,
                    description=fake.text(max_nb_chars=200),
                    goods_type=goods_type,
                    category_id=category.id,
                    category_name=category.name,
                    price=price,
                    original_price=original_price,
                    coin_price=coin_price,
                    coin_amount=coin_amount,
                    content_id=content_id,
                    content_title=content_title,
                    subscription_duration=subscription_duration,
                    subscription_type=subscription_type,
                    stock=random.randint(0, 1000) if goods_type == 'goods' else -1,
                    cover_url=fake.image_url(width=300, height=300),
                    images=None, # TBD
                    seller_id=seller.id if seller else 1,
                    seller_name=seller.nickname if seller else "官方",
                    sales_count=random.randint(0, 500),
                    view_count=random.randint(0, 2000),
                    status=random.choices(['active', 'inactive'], weights=[80, 20])[0],
                    create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                    update_time=datetime.now()
                )
                goods.append(goods_item)
            
            session.add_all(goods)
            await self._commit_with_retry(session)
            
            
            self.goods = goods
            print(f"成功生成 {len(goods)} 个商品")
            return goods
    
    async def generate_social_dynamics(self, count: int = 150):
        """生成社交动态数据"""
        print(f"正在生成 {count} 个社交动态...")
        if not self.users:
            print("缺少用户数据，跳过社交动态生成。")
            return

        dynamics = []
        dynamic_types = ['text', 'image', 'video', 'share']
        
        async with self.AsyncSessionLocal() as session:
            for _ in range(count):
                user = random.choice(self.users)
                dynamic_type = random.choice(dynamic_types)
                
                content = fake.text(max_nb_chars=500)
                images = None
                video_url = None
                share_target_type = None
                share_target_id = None
                share_target_title = None

                if dynamic_type == 'image':
                    images = [fake.image_url() for _ in range(random.randint(1, 9))]
                elif dynamic_type == 'video':
                    video_url = f"https://cdn.example.com/videos/{fake.uuid4()}.mp4"
                elif dynamic_type == 'share':
                    if random.choice([True, False]) and self.contents:
                        target = random.choice(self.contents)
                        share_target_type = 'content'
                        share_target_id = target.id
                        share_target_title = target.title
                    elif self.goods:
                        target = random.choice(self.goods)
                        share_target_type = 'goods'
                        share_target_id = target.id
                        share_target_title = target.name

                dynamic = SocialDynamic(
                    content=content,
                    dynamic_type=dynamic_type,
                    images=str(images) if images else None,
                    video_url=video_url,
                    user_id=user.id,
                    user_nickname=user.nickname,
                    user_avatar=user.avatar,
                    share_target_type=share_target_type,
                    share_target_id=share_target_id,
                    share_target_title=share_target_title,
                    like_count=random.randint(0, 1000),
                    comment_count=random.randint(0, 200),
                    share_count=random.randint(0, 50),
                    status=random.choices(['normal', 'hidden', 'deleted'], weights=[90, 5, 5])[0],
                    review_status=random.choices(['PENDING', 'APPROVED', 'REJECTED'], weights=[10, 80, 10])[0]
                )
                dynamics.append(dynamic)
            
            if dynamics:
                session.add_all(dynamics)
                await self._commit_with_retry(session)

            self.social_dynamics = dynamics
            print(f"成功生成 {len(dynamics)} 个社交动态。")
    
    async def generate_messages(self, count: int = 1000):
        """生成私信数据"""
        print(f"正在生成 {count} 个私信...")
        if len(self.users) < 2:
            print("用户数量不足，无法生成私信。")
            return

        messages = []
        sessions = {} # To track conversation sessions
        message_types = ['text', 'image']

        async with self.AsyncSessionLocal() as session:
            for _ in range(count):
                sender, receiver = random.sample(self.users, 2)
                
                # Create or update session
                session_key = tuple(sorted((sender.id, receiver.id)))
                if session_key not in sessions:
                    sessions[session_key] = MessageSession(
                        user_id=sender.id,
                        other_user_id=receiver.id,
                        unread_count=0
                    )
                    sessions[tuple(reversed(session_key))] = MessageSession(
                        user_id=receiver.id,
                        other_user_id=sender.id,
                        unread_count=0
                    )

                msg = Message(
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    content=fake.sentence(),
                    message_type=random.choice(message_types),
                    status='sent'
                )
                messages.append(msg)
                
                # Update session info
                sessions[session_key].last_message_time = msg.create_time
                sessions[tuple(reversed(session_key))].last_message_time = msg.create_time
                sessions[tuple(reversed(session_key))].unread_count += 1
            
            if messages:
                session.add_all(messages)
                await session.flush()
                # Update last_message_id for sessions
                for msg in messages:
                    session_key = tuple(sorted((msg.sender_id, msg.receiver_id)))
                    sessions[session_key].last_message_id = msg.id
                    sessions[tuple(reversed(session_key))].last_message_id = msg.id

                session.add_all(sessions.values())
                await self._commit_with_retry(session)

            print(f"成功生成 {len(messages)} 条私信和 {len(sessions)} 个会话。")

    async def generate_orders_and_payments(self, count: int = 200):
        """生成订单和支付数据"""
        print(f"正在生成 {count} 个订单和支付记录...")
        if not self.users or not self.goods:
            print("缺少用户或商品数据，跳过订单生成。")
            return

        orders = []
        payment_orders = []
        payment_channels = [PaymentChannel(
            channel_code='shark_pay', 
            channel_name='大白鲨支付', 
            provider='shark', 
            channel_type='H5',  # 渠道类型：H5、APP、PC
            merchant_id='test_id', 
            app_secret='test_secret', 
            api_gateway='http://example.com/api'
        )]

        async with self.AsyncSessionLocal() as session:
            session.add_all(payment_channels)
            await self._commit_with_retry(session)

            for _ in range(count):
                user = random.choice(self.users)
                good = random.choice(self.goods)
                payment_mode = random.choice(['cash', 'coin'])
                
                order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                
                final_amount = good.price if payment_mode == 'cash' else Decimal(0)
                coin_cost = good.coin_price if payment_mode == 'coin' else 0

                order = Order(
                    order_no=order_no,
                    user_id=user.id,
                    user_nickname=user.nickname,
                    goods_id=good.id,
                    goods_name=good.name,
                    goods_type=good.goods_type,
                    goods_cover=good.cover_url,
                    payment_mode=payment_mode,
                    cash_amount=good.price,
                    coin_cost=coin_cost,
                    total_amount=good.price,  # 添加缺失的total_amount字段
                    final_amount=final_amount,
                    status='completed' if random.random() > 0.2 else 'pending',
                    pay_status='paid' if random.random() > 0.3 else 'unpaid',
                )
                orders.append(order)

                if order.pay_status == 'paid' and payment_mode == 'cash':
                    payment_order = PaymentOrder(
                        order_no=order_no,
                        user_id=user.id,
                        channel_code='shark_pay',
                        pay_type='alipay',
                        amount=order.final_amount,
                        status='paid',
                        pay_time=datetime.now()
                    )
                    payment_orders.append(payment_order)
            
            if orders:
                session.add_all(orders)
            if payment_orders:
                session.add_all(payment_orders)
            await self._commit_with_retry(session)

        print(f"成功生成 {len(orders)} 个订单和 {len(payment_orders)} 条支付记录。")

    async def generate_search_data(self, history_count: int = 500, hot_count: int = 50):
        """生成搜索数据"""
        print("正在生成搜索数据...")
        
        # Hot Searches
        hot_keywords = [fake.word() for _ in range(hot_count)]
        hot_searches = [HotSearch(
            keyword=kw, 
            search_count=random.randint(100, 10000),
            trend_score=Decimal(random.uniform(0, 100)).quantize(Decimal("0.01"))
        ) for kw in hot_keywords]
        
        # Search History
        search_history = []
        if self.users:
            for _ in range(history_count):
                history = SearchHistory(
                    user_id=random.choice(self.users).id,
                    keyword=random.choice(hot_keywords),
                    search_type='content',
                    result_count=random.randint(0, 100)
                )
                search_history.append(history)

        async with self.AsyncSessionLocal() as session:
            if hot_searches:
                session.add_all(hot_searches)
            if search_history:
                session.add_all(search_history)
            await self._commit_with_retry(session)

        print(f"成功生成 {len(hot_searches)} 条热搜和 {len(search_history)} 条搜索历史。")

    async def generate_tasks(self, template_count: int = 20):
        """生成任务模板和奖励"""
        print(f"正在生成 {template_count} 个任务模板...")
        templates = []
        rewards = []
        task_actions = [
            (1, 1, '每日登录'), (2, 2, '发布内容'), (3, 3, '点赞'), 
            (3, 4, '评论'), (3, 5, '分享'), (4, 6, '消费'), (5, 7, '邀请用户')
        ]

        async with self.AsyncSessionLocal() as session:
            for i in range(min(template_count, len(task_actions))):
                category, action, name = task_actions[i]
                template = TaskTemplate(
                    task_name=name,
                    task_desc=f"完成{name}任务，获得奖励",
                    task_type=1, # Daily
                    task_category=category,
                    task_action=action,
                    target_count=random.randint(1, 5),
                    sort_order=i  # 添加缺失的sort_order字段
                )
                templates.append(template)
            
            session.add_all(templates)
            await session.flush()

            for template in templates:
                reward = TaskReward(
                    task_id=template.id,
                    reward_type=1, # Coin
                    reward_name='金币奖励',
                    reward_desc=f'完成任务获得{random.randint(10, 100)}金币',  # 添加缺失的reward_desc字段
                    reward_amount=random.randint(10, 100)
                )
                rewards.append(reward)
            
            session.add_all(rewards)
            await self._commit_with_retry(session)
        
        print(f"成功生成 {len(templates)} 个任务模板和 {len(rewards)} 个奖励。")
    
    async def generate_ads(self, count: int = 10):
        """生成广告数据"""
        print(f"正在生成 {count} 个广告...")
        ads = []
        ad_types = ['banner', 'popup', 'feed']

        for _ in range(count):
            ad = Ad(
                ad_name=fake.catch_phrase(),
                ad_title=fake.sentence(),
                ad_description=fake.text(max_nb_chars=100),
                ad_type=random.choice(ad_types),
                image_url=fake.image_url(),
                click_url=fake.url(),
                target_type='_blank',  # 添加缺失的target_type字段
                sort_order=random.randint(1, 100)
            )
            ads.append(ad)

        async with self.AsyncSessionLocal() as session:
            session.add_all(ads)
            await self._commit_with_retry(session)

        print(f"成功生成 {len(ads)} 个广告。")
    
    def _get_file_extension(self, content_type: str) -> str:
        """根据内容类型获取文件扩展名"""
        extensions = {
            "NOVEL": "txt",
            "COMIC": "jpg",
            "LONG_VIDEO": "mp4",
            "SHORT_VIDEO": "mp4",
            "ARTICLE": "html",
            "AUDIO": "mp3"
        }
        return extensions.get(content_type, "txt")
    
    async def generate_all_data(self, 
                               user_count: int = 100,
                               category_count: int = 20,
                               content_count: int = 200,
                               chapters_per_content: int = 5,
                               comment_count: int = 500,
                               like_count: int = 1000,
                               follow_count: int = 800,
                               favorite_count: int = 600,
                               tag_count: int = 50,
                               goods_count: int = 100,
                               social_dynamic_count: int = 150,
                               message_count: int = 1000,
                               order_count: int = 200,
                               search_history_count: int = 500,
                               task_template_count: int = 20,
                               ad_count: int = 10):
        """生成所有模块的假数据"""
        print("开始生成综合假数据...")
        
        # 按依赖关系顺序生成
        await self.generate_users(user_count)
        await self.generate_categories(category_count)
        await self.generate_tags(tag_count)
        await self.generate_contents(content_count)
        await self.generate_chapters(chapters_per_content)
        await self.generate_content_tags()
        await self.generate_user_interest_tags()
        await self.generate_goods(goods_count)
        await self.generate_social_dynamics(social_dynamic_count)
        await self.generate_comments(comment_count)
        await self.generate_likes(like_count)
        await self.generate_follows(follow_count)
        await self.generate_favorites(favorite_count)
        await self.generate_messages(message_count)
        await self.generate_orders_and_payments(order_count)
        await self.generate_search_data(search_history_count)
        await self.generate_tasks(task_template_count)
        await self.generate_ads(ad_count)
        
        print("所有假数据生成完成！")
        print(f"生成统计:")
        print(f"- 用户: {len(self.users)}")
        print(f"- 分类: {len(self.categories)}")
        print(f"- 内容: {len(self.contents)}")
        print(f"- 章节: {len(self.chapters)}")
        print(f"- 评论: {len(self.comments)}")
        print(f"- 点赞: {len(self.likes)}")
        print(f"- 关注: {len(self.follows)}")
        print(f"- 收藏: {len(self.favorites)}")
        print(f"- 标签: {len(self.tags)}")
        print(f"- 商品: {len(self.goods)}")
        print(f"- 社交动态: {len(self.social_dynamics)}")
        # 新增模块的统计待补充


async def main():
    """主函数"""
    generator = ComprehensiveDataGenerator()
    
    # 询问是否清空数据库
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await generator.clear_database()
    
    # 生成所有数据
    await generator.generate_all_data(
        user_count=100,
        category_count=20,
        content_count=200,
        chapters_per_content=5,
        comment_count=500,
        like_count=1000,
        follow_count=800,
        favorite_count=600,
        tag_count=50,
        goods_count=100,
        social_dynamic_count=150,
        message_count=1000,
        order_count=200,
        search_history_count=500,
        task_template_count=20,
        ad_count=10
    )


if __name__ == "__main__":
    asyncio.run(main()) 