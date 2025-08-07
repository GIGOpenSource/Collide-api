"""
Collide User Service 假数据生成器
使用Faker库生成测试数据，支持用户、钱包、拉黑等数据
"""
import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal, engine
from app.database.models import User, UserWallet, UserBlock
from app.common.security import security_manager

# 初始化Faker，使用中文本地化
fake = Faker(['zh_CN', 'en_US'])
Faker.seed(42)  # 设置随机种子，确保可重现的数据


class FakeDataGenerator:
    """假数据生成器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.created_users: List[User] = []
        
    def generate_invite_code(self) -> str:
        """生成唯一邀请码"""
        import string
        import secrets
        
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            existing = self.db.query(User).filter(User.invite_code == code).first()
            if not existing:
                return code
    
    def generate_users(self, count: int = 50) -> List[User]:
        """生成假用户数据"""
        print(f"正在生成 {count} 个用户...")
        
        users = []
        roles = ['user', 'blogger', 'admin', 'vip']
        statuses = ['active', 'inactive', 'suspended']
        genders = ['male', 'female', 'unknown']
        
        for i in range(count):
            # 生成用户名，确保唯一性
            username = fake.user_name()
            while self.db.query(User).filter(User.username == username).first():
                username = f"{fake.user_name()}_{random.randint(1000, 9999)}"
            
            # 生成邮箱，确保唯一性
            email = fake.email()
            while self.db.query(User).filter(User.email == email).first():
                email = fake.email()
            
            # 生成手机号，确保唯一性
            phone = fake.phone_number().replace('-', '').replace(' ', '')[:11]
            if not phone.startswith('1'):
                phone = f"1{random.randint(3, 9)}{random.randint(10000000, 99999999)}"
            while self.db.query(User).filter(User.phone == phone).first():
                phone = f"1{random.randint(3, 9)}{random.randint(10000000, 99999999)}"
            
            # 先确定用户角色和状态
            user_role = random.choices(roles, weights=[70, 20, 5, 5])[0]  # 权重分配
            user_status = random.choices(statuses, weights=[85, 10, 5])[0]  # 大部分用户为活跃状态
            
            # 创建用户
            user = User(
                username=username,
                nickname=fake.name(),
                avatar=fake.image_url(width=200, height=200) if random.choice([True, False]) else None,
                email=email,
                phone=phone,
                password_hash=security_manager.hash_password("123456"),  # 默认密码
                role=user_role,
                status=user_status,
                
                # 扩展信息
                bio=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                birthday=fake.date_of_birth(minimum_age=16, maximum_age=80) if random.choice([True, False]) else None,
                gender=random.choice(genders),
                location=fake.city() if random.choice([True, False]) else None,
                
                # 统计字段（随机生成一些数据）
                follower_count=random.randint(0, 10000),
                following_count=random.randint(0, 1000),
                content_count=random.randint(0, 500),
                like_count=random.randint(0, 5000),
                
                # VIP相关
                vip_expire_time=(
                    fake.future_datetime(end_date='+1y') 
                    if user_role == 'vip' and random.choice([True, False]) 
                    else None
                ),
                
                # 登录相关
                last_login_time=fake.date_time_between(start_date='-30d', end_date='now'),
                login_count=random.randint(1, 1000),
                
                # 邀请相关
                invite_code=self.generate_invite_code(),
                invited_count=random.randint(0, 20),
                
                # 时间
                create_time=fake.date_time_between(start_date='-1y', end_date='now'),
            )
            
            # 设置邀请人（随机选择之前创建的用户）
            if users and random.choice([True, False]):
                user.inviter_id = random.choice(users).id
            
            users.append(user)
            self.db.add(user)
            
            if (i + 1) % 10 == 0:
                print(f"已生成 {i + 1} 个用户...")
        
        # 批量提交
        self.db.commit()
        
        # 刷新对象以获取ID
        for user in users:
            self.db.refresh(user)
        
        self.created_users = users
        print(f"✅ 成功生成 {len(users)} 个用户")
        return users
    
    def generate_wallets(self, users: List[User]) -> List[UserWallet]:
        """为用户生成钱包数据"""
        print(f"正在为 {len(users)} 个用户生成钱包...")
        
        wallets = []
        
        for i, user in enumerate(users):
            # 生成随机的钱包数据
            balance = Decimal(str(random.uniform(0, 10000))).quantize(Decimal('0.01'))
            frozen_amount = Decimal(str(random.uniform(0, balance * 0.1))).quantize(Decimal('0.01'))
            
            coin_balance = random.randint(0, 50000)
            coin_total_earned = random.randint(coin_balance, coin_balance + 100000)
            coin_total_spent = coin_total_earned - coin_balance
            
            total_income = Decimal(str(random.uniform(balance, balance * 2))).quantize(Decimal('0.01'))
            total_expense = total_income - balance
            
            wallet = UserWallet(
                user_id=user.id,
                balance=balance,
                frozen_amount=frozen_amount,
                coin_balance=coin_balance,
                coin_total_earned=coin_total_earned,
                coin_total_spent=coin_total_spent,
                total_income=total_income,
                total_expense=total_expense,
                status=random.choices(['active', 'frozen'], weights=[95, 5])[0],
                create_time=user.create_time + timedelta(minutes=random.randint(1, 60)),
            )
            
            wallets.append(wallet)
            self.db.add(wallet)
            
            if (i + 1) % 10 == 0:
                print(f"已生成 {i + 1} 个钱包...")
        
        self.db.commit()
        print(f"✅ 成功生成 {len(wallets)} 个钱包")
        return wallets
    
    def generate_user_blocks(self, users: List[User], count: int = 20) -> List[UserBlock]:
        """生成用户拉黑关系数据"""
        print(f"正在生成 {count} 个拉黑关系...")
        
        blocks = []
        active_users = [u for u in users if u.status == 'active']
        
        if len(active_users) < 2:
            print("⚠️ 活跃用户数量不足，跳过拉黑关系生成")
            return blocks
        
        for i in range(count):
            # 随机选择拉黑者和被拉黑者
            user = random.choice(active_users)
            blocked_user = random.choice(active_users)
            
            # 确保不是同一个用户
            while blocked_user.id == user.id:
                blocked_user = random.choice(active_users)
            
            # 检查是否已存在拉黑关系
            existing = self.db.query(UserBlock).filter(
                UserBlock.user_id == user.id,
                UserBlock.blocked_user_id == blocked_user.id
            ).first()
            
            if existing:
                continue
            
            block = UserBlock(
                user_id=user.id,
                blocked_user_id=blocked_user.id,
                user_username=user.username,
                blocked_username=blocked_user.username,
                status=random.choices(['active', 'cancelled'], weights=[80, 20])[0],
                reason=fake.sentence() if random.choice([True, False]) else None,
                create_time=fake.date_time_between(
                    start_date=max(user.create_time, blocked_user.create_time),
                    end_date='now'
                ),
            )
            
            blocks.append(block)
            self.db.add(block)
        
        self.db.commit()
        print(f"✅ 成功生成 {len(blocks)} 个拉黑关系")
        return blocks
    
    def clear_all_data(self):
        """清空所有测试数据"""
        print("正在清空所有测试数据...")
        
        # 按依赖关系顺序删除
        self.db.query(UserBlock).delete()
        self.db.query(UserWallet).delete()
        self.db.query(User).delete()
        
        self.db.commit()
        print("✅ 所有测试数据已清空")
    
    def generate_all_data(self, user_count: int = 50, block_count: int = 20):
        """生成所有假数据"""
        print("🚀 开始生成所有假数据...")
        print("=" * 50)
        
        # 生成用户
        users = self.generate_users(user_count)
        
        # 生成钱包
        wallets = self.generate_wallets(users)
        
        # 生成拉黑关系
        blocks = self.generate_user_blocks(users, block_count)
        
        print("=" * 50)
        print("📊 数据生成完成统计:")
        print(f"👥 用户数量: {len(users)}")
        print(f"💰 钱包数量: {len(wallets)}")
        print(f"🚫 拉黑关系: {len(blocks)}")
        
        # 显示一些统计信息
        total_balance = sum(w.balance for w in wallets)
        total_coins = sum(w.coin_balance for w in wallets)
        
        print(f"\n💹 财务统计:")
        print(f"总现金余额: ¥{total_balance:,.2f}")
        print(f"总金币数量: {total_coins:,}")
        
        # 用户角色分布
        role_stats = {}
        for user in users:
            role_stats[user.role] = role_stats.get(user.role, 0) + 1
        
        print(f"\n👤 用户角色分布:")
        for role, count in role_stats.items():
            print(f"{role}: {count} 人")
        
        print("\n✅ 所有假数据生成完成！")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collide User Service 假数据生成器')
    parser.add_argument('--users', type=int, default=50, help='生成用户数量 (默认: 50)')
    parser.add_argument('--blocks', type=int, default=20, help='生成拉黑关系数量 (默认: 20)')
    parser.add_argument('--clear', action='store_true', help='清空所有数据')
    parser.add_argument('--clear-only', action='store_true', help='只清空数据，不生成新数据')
    
    args = parser.parse_args()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        generator = FakeDataGenerator(db)
        
        if args.clear or args.clear_only:
            generator.clear_all_data()
        
        if not args.clear_only:
            generator.generate_all_data(args.users, args.blocks)
        
    except Exception as e:
        print(f"❌ 生成数据时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()