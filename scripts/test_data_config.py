"""
测试数据配置文件
定义测试数据的生成规则和预设场景
"""
from typing import Dict, List, Any

# 用户角色分布权重
USER_ROLE_WEIGHTS = {
    'user': 70,      # 普通用户 70%
    'blogger': 20,   # 博主 20%
    'admin': 5,      # 管理员 5%
    'vip': 5         # VIP用户 5%
}

# 用户状态分布权重
USER_STATUS_WEIGHTS = {
    'active': 85,    # 活跃用户 85%
    'inactive': 10,  # 不活跃用户 10%
    'suspended': 5   # 被封禁用户 5%
}

# 性别分布
GENDER_OPTIONS = ['male', 'female', 'unknown']

# 钱包状态分布权重
WALLET_STATUS_WEIGHTS = {
    'active': 95,    # 正常钱包 95%
    'frozen': 5      # 冻结钱包 5%
}

# 拉黑关系状态分布权重
BLOCK_STATUS_WEIGHTS = {
    'active': 80,     # 活跃拉黑 80%
    'cancelled': 20   # 已取消拉黑 20%
}

# 预设用户场景
PRESET_USERS = [
    {
        'username': 'admin_user',
        'nickname': '系统管理员',
        'email': 'admin@collide.com',
        'role': 'admin',
        'status': 'active',
        'bio': '我是系统管理员，负责平台的日常管理工作。',
        'balance': 10000.00,
        'coin_balance': 100000
    },
    {
        'username': 'blogger_demo',
        'nickname': '知名博主',
        'email': 'blogger@collide.com',
        'role': 'blogger',
        'status': 'active',
        'bio': '专业内容创作者，分享有趣的科技和生活内容。',
        'follower_count': 50000,
        'content_count': 500,
        'balance': 5000.00,
        'coin_balance': 50000
    },
    {
        'username': 'vip_user',
        'nickname': 'VIP会员',
        'email': 'vip@collide.com',
        'role': 'vip',
        'status': 'active',
        'bio': 'VIP会员用户，享受平台特权服务。',
        'balance': 2000.00,
        'coin_balance': 20000
    },
    {
        'username': 'test_user_001',
        'nickname': '测试用户001',
        'email': 'test001@collide.com',
        'role': 'user',
        'status': 'active',
        'bio': '这是一个用于测试的普通用户账号。',
        'balance': 100.00,
        'coin_balance': 1000
    },
    {
        'username': 'suspended_user',
        'nickname': '被封用户',
        'email': 'suspended@collide.com',
        'role': 'user',
        'status': 'suspended',
        'bio': '这个用户因为违规行为被暂时封禁。',
        'balance': 50.00,
        'coin_balance': 500
    }
]

# 数据生成配置
GENERATION_CONFIG = {
    'default_password': '123456',  # 所有测试用户的默认密码
    'min_age': 16,                 # 最小年龄
    'max_age': 80,                 # 最大年龄
    'avatar_probability': 0.7,     # 设置头像的概率
    'bio_probability': 0.6,        # 设置个人简介的概率
    'birthday_probability': 0.8,   # 设置生日的概率
    'location_probability': 0.5,   # 设置地址的概率
    'vip_expire_probability': 0.6, # VIP用户设置过期时间的概率
    'inviter_probability': 0.3,    # 设置邀请人的概率
    
    # 统计数据范围
    'follower_count_range': (0, 10000),
    'following_count_range': (0, 1000),
    'content_count_range': (0, 500),
    'like_count_range': (0, 5000),
    'login_count_range': (1, 1000),
    'invited_count_range': (0, 20),
    
    # 钱包数据范围
    'balance_range': (0, 10000),
    'frozen_ratio_max': 0.1,  # 冻结金额最大不超过余额的10%
    'coin_balance_range': (0, 50000),
    'coin_earned_bonus_range': (0, 100000),  # 累计获得金币的额外范围
}

# 常用的中文城市列表（用于location字段）
CHINESE_CITIES = [
    '北京市', '上海市', '广州市', '深圳市', '杭州市', '南京市', '武汉市', '成都市',
    '重庆市', '天津市', '苏州市', '西安市', '长沙市', '沈阳市', '青岛市', '郑州市',
    '大连市', '东莞市', '宁波市', '厦门市', '福州市', '无锡市', '合肥市', '昆明市',
    '哈尔滨市', '济南市', '佛山市', '长春市', '温州市', '石家庄市', '南宁市', '常州市',
    '泉州市', '南昌市', '贵阳市', '太原市', '烟台市', '嘉兴市', '南通市', '金华市'
]

# 常用的个人简介模板
BIO_TEMPLATES = [
    "热爱生活，热爱分享的{role_name}。",
    "专注于{interest}领域的内容创作者。",
    "喜欢{hobby}，在这里分享我的日常生活。",
    "{personality}的{age}后，欢迎大家关注我的动态。",
    "一个普通的{occupation}，希望在这里认识更多朋友。",
    "专业的{field}从业者，分享行业见解和经验。",
    "生活在{city}的{role_name}，记录美好的每一天。",
    "追求{goal}的路上，用文字记录成长的足迹。"
]

# 兴趣爱好列表
INTERESTS = [
    '科技', '摄影', '旅行', '美食', '音乐', '电影', '读书', '运动',
    '绘画', '编程', '设计', '写作', '游戏', '动漫', '时尚', '健身'
]

# 职业列表
OCCUPATIONS = [
    '程序员', '设计师', '教师', '医生', '律师', '记者', '销售',
    '学生', '自由职业者', '创业者', '艺术家', '工程师', '研究员'
]

# 个性特点
PERSONALITIES = [
    '开朗', '内向', '幽默', '认真', '随和', '严谨', '创新', '踏实',
    '乐观', '理性', '感性', '独立', '团队合作', '有责任心'
]

# 目标追求
GOALS = [
    '技术excellence', '创意表达', '知识分享', '个人成长', '事业发展',
    '生活品质', '健康生活', '财务自由', '社会贡献', '家庭幸福'
]