"""
高级假数据生成器
支持预设场景、批量生成、数据关联等功能
"""
import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import User, UserWallet, UserBlock
from app.common.security import security_manager
from scripts.test_data_config import *

# 初始化Faker
fake = Faker(['zh_CN', 'en_US'])
Faker.seed(42)


class AdvancedDataGenerator:
    """高级数据生成器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.created_users: List[User] = []
        self.existing_usernames = set()
        self.existing_emails = set()
        self.existing_phones = set()
        
    def load_existing_data(self):
        """加载现有数据，避免重复"""
        existing_users = self.db.query(User).all()
        self.existing_usernames = {u.username for u in existing_users}
        self.existing_emails = {u.email for u in existing_users if u.email}
        self.existing_phones = {u.phone for u in existing_users if u.phone}
        
    def generate_unique_username(self, base_username: str = None) -> str:
        """生成唯一用户名"""
        if base_username:
            username = base_username
        else:
            username = fake.user_name()
            
        original_username = username
        counter = 1
        
        while username in self.existing_usernames:
            username = f"{original_username}_{counter}"
            counter += 1
        
        self.existing_usernames.add(username)
        return username
    
    def generate_unique_email(self, base_email: str = None) -> str:
        """生成唯一邮箱"""
        if base_email:
            email = base_email
        else:
            email = fake.email()
            
        while email in self.existing_emails:
            email = fake.email()
        
        self.existing_emails.add(email)
        return email
    
    def generate_unique_phone(self) -> str:
        """生成唯一手机号"""
        while True:
            phone = f"1{random.randint(3, 9)}{random.randint(10000000, 99999999)}"
            if phone not in self.existing_phones:
                self.existing_phones.add(phone)
                return phone
    
    def generate_invite_code(self) -> str:
        """生成唯一邀请码"""
        import string
        import secrets
        
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            existing = self.db.query(User).filter(User.invite_code == code).first()
            if not existing:
                return code
    
    def generate_rich_bio(self, user_data: Dict[str, Any]) -> str:
        """生成丰富的个人简介"""
        role_names = {
            'user': '用户',
            'blogger': '博主',
            'admin': '管理员',
            'vip': 'VIP会员'
        }
        
        template = random.choice(BIO_TEMPLATES)
        
        replacements = {
            'role_name': role_names.get(user_data.get('role', 'user'), '用户'),
            'interest': random.choice(INTERESTS),
            'hobby': random.choice(INTERESTS),
            'personality': random.choice(PERSONALITIES),
            'age': f"{random.randint(20, 40)}",
            'occupation': random.choice(OCCUPATIONS),
            'field': random.choice(INTERESTS),
            'city': random.choice(CHINESE_CITIES),
            'goal': random.choice(GOALS)
        }
        
        bio = template
        for key, value in replacements.items():
            bio = bio.replace(f'{{{key}}}', value)
        
        return bio
    
    def create_preset_users(self) -> List[User]:
        """创建预设用户"""
        print("正在创建预设用户...")
        
        users = []
        
        for preset in PRESET_USERS:
            # 检查用户是否已存在
            existing = self.db.query(User).filter(User.username == preset['username']).first()
            if existing:
                print(f"⚠️ 用户 {preset['username']} 已存在，跳过创建")
                continue
            
            user = User(
                username=preset['username'],
                nickname=preset['nickname'],
                email=self.generate_unique_email(preset['email']),
                phone=self.generate_unique_phone(),
                password_hash=security_manager.hash_password(GENERATION_CONFIG['default_password']),
                role=preset['role'],
                status=preset['status'],
                bio=preset['bio'],
                gender=random.choice(GENDER_OPTIONS),
                location=random.choice(CHINESE_CITIES),
                follower_count=preset.get('follower_count', random.randint(0, 1000)),
                following_count=random.randint(0, 500),
                content_count=preset.get('content_count', random.randint(0, 100)),
                like_count=random.randint(0, 2000),
                last_login_time=fake.date_time_between(start_date='-7d', end_date='now'),
                login_count=random.randint(10, 500),
                invite_code=self.generate_invite_code(),
                invited_count=random.randint(0, 10),
                create_time=fake.date_time_between(start_date='-6m', end_date='-1m'),
            )
            
            # VIP用户设置过期时间
            if user.role == 'vip':
                user.vip_expire_time = fake.future_datetime(end_date='+1y')
            
            users.append(user)
            self.db.add(user)
            print(f"✅ 创建预设用户: {user.username} ({user.role})")
        
        self.db.commit()
        
        # 创建对应的钱包
        for i, user in enumerate(users):
            self.db.refresh(user)
            preset = PRESET_USERS[i]
            
            wallet = UserWallet(
                user_id=user.id,
                balance=Decimal(str(preset.get('balance', 0))),
                frozen_amount=Decimal('0.00'),
                coin_balance=preset.get('coin_balance', 0),
                coin_total_earned=preset.get('coin_balance', 0),
                coin_total_spent=0,
                total_income=Decimal(str(preset.get('balance', 0))),
                total_expense=Decimal('0.00'),
                status='active',
                create_time=user.create_time + timedelta(minutes=5),
            )
            
            self.db.add(wallet)
            print(f"✅ 创建钱包: {user.username} - ¥{wallet.balance} / {wallet.coin_balance}金币")
        
        self.db.commit()
        print(f"✅ 预设用户创建完成，共 {len(users)} 个")
        return users
    
    def generate_random_users(self, count: int, with_relationships: bool = True) -> List[User]:
        """生成随机用户"""
        print(f"正在生成 {count} 个随机用户...")
        
        users = []
        
        for i in range(count):
            # 选择角色和状态
            role = random.choices(
                list(USER_ROLE_WEIGHTS.keys()), 
                weights=list(USER_ROLE_WEIGHTS.values())
            )[0]
            
            status = random.choices(
                list(USER_STATUS_WEIGHTS.keys()), 
                weights=list(USER_STATUS_WEIGHTS.values())
            )[0]
            
            user = User(
                username=self.generate_unique_username(),
                nickname=fake.name(),
                avatar=fake.image_url(width=200, height=200) if random.random() < GENERATION_CONFIG['avatar_probability'] else None,
                email=self.generate_unique_email(),
                phone=self.generate_unique_phone(),
                password_hash=security_manager.hash_password(GENERATION_CONFIG['default_password']),
                role=role,
                status=status,
                
                # 扩展信息
                bio=self.generate_rich_bio({'role': role}) if random.random() < GENERATION_CONFIG['bio_probability'] else None,
                birthday=fake.date_of_birth(
                    minimum_age=GENERATION_CONFIG['min_age'], 
                    maximum_age=GENERATION_CONFIG['max_age']
                ) if random.random() < GENERATION_CONFIG['birthday_probability'] else None,
                gender=random.choice(GENDER_OPTIONS),
                location=random.choice(CHINESE_CITIES) if random.random() < GENERATION_CONFIG['location_probability'] else None,
                
                # 统计字段
                follower_count=random.randint(*GENERATION_CONFIG['follower_count_range']),
                following_count=random.randint(*GENERATION_CONFIG['following_count_range']),
                content_count=random.randint(*GENERATION_CONFIG['content_count_range']),
                like_count=random.randint(*GENERATION_CONFIG['like_count_range']),
                
                # 登录相关
                last_login_time=fake.date_time_between(start_date='-30d', end_date='now'),
                login_count=random.randint(*GENERATION_CONFIG['login_count_range']),
                
                # 邀请相关
                invite_code=self.generate_invite_code(),
                invited_count=random.randint(*GENERATION_CONFIG['invited_count_range']),
                
                # 时间
                create_time=fake.date_time_between(start_date='-1y', end_date='now'),
            )
            
            # VIP用户设置过期时间
            if user.role == 'vip' and random.random() < GENERATION_CONFIG['vip_expire_probability']:
                user.vip_expire_time = fake.future_datetime(end_date='+1y')
            
            # 设置邀请关系
            if with_relationships and users and random.random() < GENERATION_CONFIG['inviter_probability']:
                user.inviter_id = random.choice(users).id
            
            users.append(user)
            self.db.add(user)
            
            if (i + 1) % 10 == 0:
                print(f"已生成 {i + 1} 个用户...")
        
        self.db.commit()
        
        # 刷新对象以获取ID
        for user in users:
            self.db.refresh(user)
        
        print(f"✅ 随机用户生成完成，共 {len(users)} 个")
        return users
    
    def generate_advanced_wallets(self, users: List[User]) -> List[UserWallet]:
        """生成高级钱包数据"""
        print(f"正在为 {len(users)} 个用户生成高级钱包...")
        
        wallets = []
        
        for i, user in enumerate(users):
            # 根据用户角色调整财富水平
            role_multipliers = {
                'admin': 5.0,
                'blogger': 3.0,
                'vip': 2.0,
                'user': 1.0
            }
            
            multiplier = role_multipliers.get(user.role, 1.0)
            
            # 生成基础余额
            base_balance = random.uniform(*GENERATION_CONFIG['balance_range'])
            balance = Decimal(str(base_balance * multiplier)).quantize(Decimal('0.01'))
            
            # 冻结金额
            frozen_amount = Decimal(str(random.uniform(0, float(balance) * GENERATION_CONFIG['frozen_ratio_max']))).quantize(Decimal('0.01'))
            
            # 金币数据
            base_coins = random.randint(*GENERATION_CONFIG['coin_balance_range'])
            coin_balance = int(base_coins * multiplier)
            
            coin_bonus = random.randint(*GENERATION_CONFIG['coin_earned_bonus_range'])
            coin_total_earned = coin_balance + coin_bonus
            coin_total_spent = coin_bonus
            
            # 收入支出数据
            total_income = balance + Decimal(str(random.uniform(0, float(balance) * 2))).quantize(Decimal('0.01'))
            total_expense = total_income - balance
            
            # 钱包状态
            wallet_status = random.choices(
                list(WALLET_STATUS_WEIGHTS.keys()),
                weights=list(WALLET_STATUS_WEIGHTS.values())
            )[0]
            
            wallet = UserWallet(
                user_id=user.id,
                balance=balance,
                frozen_amount=frozen_amount,
                coin_balance=coin_balance,
                coin_total_earned=coin_total_earned,
                coin_total_spent=coin_total_spent,
                total_income=total_income,
                total_expense=total_expense,
                status=wallet_status,
                create_time=user.create_time + timedelta(minutes=random.randint(1, 60)),
            )
            
            wallets.append(wallet)
            self.db.add(wallet)
            
            if (i + 1) % 10 == 0:
                print(f"已生成 {i + 1} 个钱包...")
        
        self.db.commit()
        print(f"✅ 高级钱包生成完成，共 {len(wallets)} 个")
        return wallets
    
    def generate_scenario_data(self, scenario: str = "default") -> Dict[str, List]:
        """生成特定场景的测试数据"""
        scenarios = {
            "default": {"users": 50, "blocks": 20},
            "small": {"users": 10, "blocks": 5},
            "medium": {"users": 100, "blocks": 30},
            "large": {"users": 500, "blocks": 100},
            "demo": {"users": 20, "blocks": 10}
        }
        
        config = scenarios.get(scenario, scenarios["default"])
        
        print(f"🎬 生成 '{scenario}' 场景数据...")
        print("=" * 50)
        
        # 加载现有数据
        self.load_existing_data()
        
        # 创建预设用户
        preset_users = self.create_preset_users()
        
        # 生成随机用户
        random_users = self.generate_random_users(config["users"])
        
        # 合并用户列表
        all_users = preset_users + random_users
        self.created_users = all_users
        
        # 生成钱包（只为新用户生成）
        new_users = [u for u in all_users if not self.db.query(UserWallet).filter(UserWallet.user_id == u.id).first()]
        wallets = self.generate_advanced_wallets(new_users)
        
        # 生成拉黑关系
        blocks = self.generate_user_blocks(all_users, config["blocks"])
        
        return {
            "users": all_users,
            "wallets": wallets,
            "blocks": blocks
        }
    
    def generate_user_blocks(self, users: List[User], count: int) -> List[UserBlock]:
        """生成用户拉黑关系"""
        print(f"正在生成 {count} 个拉黑关系...")
        
        blocks = []
        active_users = [u for u in users if u.status == 'active']
        
        if len(active_users) < 2:
            print("⚠️ 活跃用户数量不足，跳过拉黑关系生成")
            return blocks
        
        for i in range(count):
            # 随机选择用户
            user = random.choice(active_users)
            blocked_user = random.choice(active_users)
            
            # 确保不是同一个用户
            while blocked_user.id == user.id:
                blocked_user = random.choice(active_users)
            
            # 检查是否已存在
            existing = self.db.query(UserBlock).filter(
                UserBlock.user_id == user.id,
                UserBlock.blocked_user_id == blocked_user.id
            ).first()
            
            if existing:
                continue
            
            status = random.choices(
                list(BLOCK_STATUS_WEIGHTS.keys()),
                weights=list(BLOCK_STATUS_WEIGHTS.values())
            )[0]
            
            # 生成拉黑原因
            reasons = [
                "发布不当内容", "恶意骚扰", "垃圾信息", "虚假信息", 
                "侵犯版权", "人身攻击", "违反社区规则", "其他原因"
            ]
            
            block = UserBlock(
                user_id=user.id,
                blocked_user_id=blocked_user.id,
                user_username=user.username,
                blocked_username=blocked_user.username,
                status=status,
                reason=random.choice(reasons) if random.choice([True, False]) else None,
                create_time=fake.date_time_between(
                    start_date=max(user.create_time, blocked_user.create_time),
                    end_date='now'
                ),
            )
            
            blocks.append(block)
            self.db.add(block)
        
        self.db.commit()
        print(f"✅ 拉黑关系生成完成，共 {len(blocks)} 个")
        return blocks
    
    def clear_all_data(self):
        """清空所有测试数据"""
        print("🗑️ 正在清空所有测试数据...")
        
        # 按依赖关系顺序删除
        deleted_blocks = self.db.query(UserBlock).count()
        self.db.query(UserBlock).delete()
        
        deleted_wallets = self.db.query(UserWallet).count()
        self.db.query(UserWallet).delete()
        
        deleted_users = self.db.query(User).count()
        self.db.query(User).delete()
        
        self.db.commit()
        
        print(f"✅ 数据清空完成:")
        print(f"   删除用户: {deleted_users} 个")
        print(f"   删除钱包: {deleted_wallets} 个")
        print(f"   删除拉黑关系: {deleted_blocks} 个")
    
    def print_statistics(self, data: Dict[str, List]):
        """打印数据统计信息"""
        users = data["users"]
        wallets = data["wallets"]
        blocks = data["blocks"]
        
        print("=" * 50)
        print("📊 数据生成统计:")
        print(f"👥 用户总数: {len(users)}")
        print(f"💰 钱包总数: {len(wallets)}")
        print(f"🚫 拉黑关系: {len(blocks)}")
        
        # 用户角色分布
        role_stats = {}
        status_stats = {}
        for user in users:
            role_stats[user.role] = role_stats.get(user.role, 0) + 1
            status_stats[user.status] = status_stats.get(user.status, 0) + 1
        
        print(f"\n👤 用户角色分布:")
        for role, count in role_stats.items():
            print(f"   {role}: {count} 人")
        
        print(f"\n📈 用户状态分布:")
        for status, count in status_stats.items():
            print(f"   {status}: {count} 人")
        
        # 财务统计
        if wallets:
            total_balance = sum(w.balance for w in wallets)
            total_coins = sum(w.coin_balance for w in wallets)
            
            print(f"\n💹 财务统计:")
            print(f"   总现金余额: ¥{total_balance:,.2f}")
            print(f"   总金币数量: {total_coins:,}")
            print(f"   平均余额: ¥{total_balance/len(wallets):,.2f}")
            print(f"   平均金币: {total_coins//len(wallets):,}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collide User Service 高级假数据生成器')
    parser.add_argument('--scenario', choices=['small', 'default', 'medium', 'large', 'demo'], 
                       default='default', help='数据生成场景')
    parser.add_argument('--clear', action='store_true', help='清空所有数据后重新生成')
    parser.add_argument('--clear-only', action='store_true', help='只清空数据，不生成新数据')
    parser.add_argument('--preset-only', action='store_true', help='只创建预设用户')
    
    args = parser.parse_args()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        generator = AdvancedDataGenerator(db)
        
        if args.clear or args.clear_only:
            generator.clear_all_data()
        
        if not args.clear_only:
            if args.preset_only:
                generator.load_existing_data()
                preset_users = generator.create_preset_users()
                wallets = generator.generate_advanced_wallets(preset_users)
                data = {"users": preset_users, "wallets": wallets, "blocks": []}
            else:
                data = generator.generate_scenario_data(args.scenario)
            
            generator.print_statistics(data)
        
        print("\n✅ 所有操作完成！")
        
    except Exception as e:
        print(f"❌ 生成数据时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()