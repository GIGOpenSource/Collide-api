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
from app.domains.users.models import User
from app.domains.content.models import Content, ContentChapter, ContentPayment, UserContentPurchase
from app.domains.category.models import Category
from app.domains.comment.models import Comment
from app.domains.like.models import Like
from app.domains.follow.models import Follow
from app.domains.favorite.models import Favorite
from app.domains.tag.models import Tag
from app.domains.goods.models import Goods

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
                't_content', 't_category',
                't_user_block', 't_user_wallet', 't_user'
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
    
    async def generate_users(self, count: int = 100) -> List[User]:
        """生成用户数据"""
        print(f"正在生成 {count} 个用户...")
        
        users = []
        roles = ['user', 'blogger', 'admin', 'vip']
        statuses = ['active', 'inactive', 'suspended']
        genders = ['male', 'female', 'unknown']
        
        batch_size = 25
        batch = []
        for i in range(count):
            # 生成用户名，确保唯一性
            username = f"user_{fake.user_name()}_{random.randint(1000, 9999)}_{i}"
            email = f"{fake.user_name()}_{random.randint(1000, 9999)}_{i}@example.com"
            phone = f"1{random.randint(3, 9)}{random.randint(10000000, 99999999)}"
            
            # 确定用户角色和状态
            user_role = random.choices(roles, weights=[70, 20, 5, 5])[0]
            user_status = random.choices(statuses, weights=[85, 10, 5])[0]
            
            # 创建用户
            user = User(
                username=username,
                nickname=fake.name(),
                avatar=fake.image_url(width=200, height=200) if random.choice([True, False]) else None,
                email=email,
                phone=phone,
                password_hash=self._hash_password("123456"),
                role=user_role,
                status=user_status,
                
                # 扩展信息
                bio=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                birthday=fake.date_of_birth(minimum_age=16, maximum_age=80) if random.choice([True, False]) else None,
                gender=random.choice(genders),
                location=fake.city() if random.choice([True, False]) else None,
                
                # 统计字段
                follower_count=random.randint(0, 10000),
                following_count=random.randint(0, 1000),
                content_count=random.randint(0, 500),
                like_count=random.randint(0, 5000),
                
                # VIP相关
                vip_expire_time=(
                    datetime.now() + timedelta(days=random.randint(30, 365))
                    if user_role == 'vip' and random.choice([True, False])
                    else None
                ),
                
                # 登录相关
                last_login_time=fake.date_time_between(start_date='-30d', end_date='now'),
                login_count=random.randint(1, 1000),
                
                # 邀请相关
                invite_code=self._generate_invite_code(),
                invited_count=random.randint(0, 50),
                
                create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                update_time=datetime.now()
            )
            
            users.append(user)
            batch.append(user)
            if len(batch) >= batch_size:
                async with self.AsyncSessionLocal() as session:
                    session.add_all(batch)
                    await self._commit_with_retry(session)
                batch = []

        if batch:
            async with self.AsyncSessionLocal() as session:
                session.add_all(batch)
                await self._commit_with_retry(session)
            
        self.users = users
        print(f"成功生成 {len(users)} 个用户")
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
                    icon_url=fake.image_url(width=100, height=100),
                    sort=random.randint(1, 100),
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
        """生成内容数据"""
        print(f"正在生成 {count} 个内容...")
        
        if not self.users:
            raise ValueError("请先生成用户数据")
        if not self.categories:
            raise ValueError("请先生成分类数据")
        
        contents = []
        content_types = ["NOVEL", "COMIC", "LONG_VIDEO", "SHORT_VIDEO", "ARTICLE", "AUDIO"]
        content_statuses = ["DRAFT", "PUBLISHED", "OFFLINE"]
        review_statuses = ["PENDING", "APPROVED", "REJECTED"]
        
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
                    cover_url=fake.image_url(width=400, height=600),
                    tags=",".join(fake.words(nb=random.randint(3, 8))),
                    author_id=user.id,
                    author_nickname=user.nickname or user.username,
                    author_avatar=user.avatar,
                    category_id=category.id,
                    category_name=category.name,
                    status=random.choices(content_statuses, weights=[20, 70, 10])[0],
                    review_status=random.choices(review_statuses, weights=[10, 80, 10])[0],
                    
                    # 随机统计数据
                    view_count=random.randint(0, 50000),
                    like_count=random.randint(0, 5000),
                    comment_count=random.randint(0, 1000),
                    share_count=random.randint(0, 500),
                    favorite_count=random.randint(0, 2000),
                    score_count=random.randint(0, 1000),
                    score_total=random.randint(0, 5000),
                    
                    publish_time=fake.date_time_between(start_date='-180d', end_date='now') if random.choice([True, False]) else None,
                    create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                    update_time=datetime.now()
                )
                
                contents.append(content)
            
            session.add_all(contents)
            await self._commit_with_retry(session)
            
            
            self.contents = contents
            print(f"成功生成 {len(contents)} 个内容")
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
                if content.content_type in ["NOVEL", "COMIC"]:  # 只有小说和漫画有章节
                    for i in range(chapters_per_content):
                        chapter = ContentChapter(
                            content_id=content.id,
                            chapter_num=i + 1,
                            title=f"第{i + 1}章 {fake.sentence(nb_words=4)}",
                            content=fake.text(max_nb_chars=random.randint(1000, 5000)),
                            word_count=random.randint(1000, 5000),
                            status=random.choices(chapter_statuses, weights=[20, 80])[0],
                            create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                            update_time=datetime.now()
                        )
                        chapters.append(chapter)
            
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
        comment_types = ["content", "comment"]
        
        async with self.AsyncSessionLocal() as session:
            for i in range(count):
                user = random.choice(self.users)
                comment_type = random.choice(comment_types)
                
                if comment_type == "content":
                    target = random.choice(self.contents)
                    target_id = target.id
                    parent_id = None
                else:
                    # 回复其他评论
                    if comments:
                        parent_comment = random.choice(comments)
                        target_id = parent_comment.target_id
                        parent_id = parent_comment.id
                    else:
                        target = random.choice(self.contents)
                        target_id = target.id
                        parent_id = None
                
                comment = Comment(
                    user_id=user.id,
                    user_nickname=user.nickname or user.username,
                    user_avatar=user.avatar,
                    comment_type=comment_type,
                    target_id=target_id,
                    parent_comment_id=parent_id or 0,
                    content=fake.text(max_nb_chars=200),
                    like_count=random.randint(0, 100),
                    reply_count=random.randint(0, 20),
                    status=random.choices(['NORMAL', 'HIDDEN', 'DELETED'], weights=[95, 3, 2])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                comments.append(comment)
            
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
        like_types = ["content", "comment"]
        
        async with self.AsyncSessionLocal() as session:
            # 创建所有可能的点赞组合
            all_like_combinations = []
            
            # 内容点赞组合
            for user in self.users:
                for content in self.contents:
                    all_like_combinations.append((user.id, "content", content.id))
            
            # 评论点赞组合
            if self.comments:
                for user in self.users:
                    for comment in self.comments:
                        all_like_combinations.append((user.id, "comment", comment.id))
            
            # 随机选择指定数量的点赞
            if len(all_like_combinations) > count:
                selected_combinations = random.sample(all_like_combinations, count)
            else:
                selected_combinations = all_like_combinations
            
            for user_id, like_type, target_id in selected_combinations:
                user = next(u for u in self.users if u.id == user_id)
                
                like = Like(
                    user_id=user_id,
                    user_nickname=user.nickname or user.username,
                    user_avatar=user.avatar,
                    like_type=like_type,
                    target_id=target_id,
                    status=random.choices(['active', 'cancelled'], weights=[90, 10])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                likes.append(like)
            
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
                    follower_nickname=follower.nickname or follower.username,
                    follower_avatar=follower.avatar,
                    followee_id=followee_id,
                    followee_nickname=followee.nickname or followee.username,
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
        favorite_types = ["content", "comment"]
        
        async with self.AsyncSessionLocal() as session:
            # 创建所有可能的收藏组合
            all_favorite_combinations = []
            
            # 内容收藏组合
            for user in self.users:
                for content in self.contents:
                    all_favorite_combinations.append((user.id, "content", content.id))
            
            # 评论收藏组合
            if self.comments:
                for user in self.users:
                    for comment in self.comments:
                        all_favorite_combinations.append((user.id, "comment", comment.id))
            
            # 随机选择指定数量的收藏
            if len(all_favorite_combinations) > count:
                selected_combinations = random.sample(all_favorite_combinations, count)
            else:
                selected_combinations = all_favorite_combinations
            
            for user_id, favorite_type, target_id in selected_combinations:
                user = next(u for u in self.users if u.id == user_id)
                
                favorite = Favorite(
                    user_id=user_id,
                    user_nickname=user.nickname or user.username,
                    favorite_type=favorite_type,
                    target_id=target_id,
                    status=random.choices(['active', 'cancelled'], weights=[90, 10])[0],
                    create_time=fake.date_time_between(start_date='-180d', end_date='now'),
                    update_time=datetime.now()
                )
                
                favorites.append(favorite)
            
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
                
                tag = Tag(
                    name=name,
                    description=fake.text(max_nb_chars=100),
                    tag_type=tag_type,
                    usage_count=random.randint(0, 1000),
                    status=random.choices(['active', 'inactive'], weights=[80, 20])[0],
                    create_time=fake.date_time_between(start_date='-365d', end_date='now'),
                    update_time=datetime.now()
                )
                tags.append(tag)
            
            session.add_all(tags)
            await self._commit_with_retry(session)
            
            
            self.tags = tags
            print(f"成功生成 {len(tags)} 个标签")
            return tags
    
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
                
                if goods_type == "coin":
                    price = random.randint(1, 1000)
                    original_price = price + random.randint(0, 200)
                elif goods_type == "subscription":
                    price = random.randint(10, 100)
                    original_price = price + random.randint(0, 50)
                else:
                    price = random.randint(1, 500)
                    original_price = price + random.randint(0, 100)
                
                # 关联一个卖家（随机选择一个用户作为商家）
                seller = random.choice(self.users) if self.users else None

                # 不同类型的字段填充
                coin_price = 0
                coin_amount = None
                content_id = None
                content_title = None
                subscription_duration = None
                subscription_type = None
                
                if goods_type == "coin":
                    coin_amount = random.randint(10, 10000)
                elif goods_type == "content" and self.contents:
                    linked = random.choice(self.contents)
                    content_id = linked.id
                    content_title = linked.title
                elif goods_type == "subscription":
                    subscription_duration = random.choice([7, 30, 90, 180, 365])
                    subscription_type = random.choice(["VIP", "PREMIUM"]) 

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
                    stock=random.randint(0, 1000),
                    cover_url=fake.image_url(width=300, height=300),
                    images=None,
                    seller_id=seller.id if seller else 1,
                    seller_name=seller.nickname or seller.username if seller else "官方",
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
                               comment_count: int = 500,
                               like_count: int = 1000,
                               follow_count: int = 800,
                               favorite_count: int = 600,
                               tag_count: int = 50,
                               goods_count: int = 100):
        """生成所有模块的假数据"""
        print("开始生成综合假数据...")
        
        # 按依赖关系顺序生成
        await self.generate_users(user_count)
        await self.generate_categories(category_count)
        await self.generate_contents(content_count)
        await self.generate_comments(comment_count)
        await self.generate_likes(like_count)
        await self.generate_follows(follow_count)
        await self.generate_favorites(favorite_count)
        await self.generate_tags(tag_count)
        await self.generate_goods(goods_count)
        
        print("所有假数据生成完成！")
        print(f"生成统计:")
        print(f"- 用户: {len(self.users)}")
        print(f"- 分类: {len(self.categories)}")
        print(f"- 内容: {len(self.contents)}")
        print(f"- 评论: {len(self.comments)}")
        print(f"- 点赞: {len(self.likes)}")
        print(f"- 关注: {len(self.follows)}")
        print(f"- 收藏: {len(self.favorites)}")
        print(f"- 标签: {len(self.tags)}")
        print(f"- 商品: {len(self.goods)}")


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
        comment_count=500,
        like_count=1000,
        follow_count=800,
        favorite_count=600,
        tag_count=50,
        goods_count=100
    )


if __name__ == "__main__":
    asyncio.run(main()) 