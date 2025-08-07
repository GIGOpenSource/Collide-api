# 测试数据生成脚本说明

本目录包含了Collide User Service的测试数据生成脚本，可以快速创建各种测试场景的假数据。

## 📁 文件说明

- `fake_data_generator.py` - 基础假数据生成器
- `advanced_data_generator.py` - 高级假数据生成器（推荐）
- `test_data_config.py` - 测试数据配置文件
- `README.md` - 本说明文档

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install faker
# 或者安装完整依赖
pip install -r requirements.txt
```

### 2. 基础使用

```bash
# 在项目根目录执行
python create_test_data.py
```

### 3. 高级使用

```bash
# 创建小量测试数据（适合开发调试）
python create_test_data.py --scenario small

# 创建默认数量测试数据
python create_test_data.py --scenario default

# 创建大量测试数据（适合性能测试）
python create_test_data.py --scenario large

# 清空现有数据并重新生成
python create_test_data.py --clear

# 只创建预设用户（管理员、博主等）
python create_test_data.py --preset-only
```

## 📊 数据场景

### Small 场景
- 用户数量: 10个
- 拉黑关系: 5个
- 适用: 开发调试

### Default 场景
- 用户数量: 50个  
- 拉黑关系: 20个
- 适用: 功能测试

### Medium 场景
- 用户数量: 100个
- 拉黑关系: 30个
- 适用: 集成测试

### Large 场景
- 用户数量: 500个
- 拉黑关系: 100个
- 适用: 性能测试

### Demo 场景
- 用户数量: 20个
- 拉黑关系: 10个
- 适用: 演示展示

## 👥 预设用户

脚本会自动创建以下预设用户，密码统一为 `123456`:

| 用户名 | 角色 | 邮箱 | 说明 |
|--------|------|------|------|
| admin_user | admin | admin@collide.com | 系统管理员 |
| blogger_demo | blogger | blogger@collide.com | 知名博主 |
| vip_user | vip | vip@collide.com | VIP会员 |
| test_user_001 | user | test001@collide.com | 测试用户 |
| suspended_user | user | suspended@collide.com | 被封用户 |

## 🎯 生成的数据类型

### 用户数据
- ✅ 基本信息（用户名、昵称、邮箱、手机号）
- ✅ 角色和状态（用户、博主、管理员、VIP等）
- ✅ 个人资料（头像、简介、生日、性别、地址）
- ✅ 统计数据（粉丝数、关注数、内容数、点赞数）
- ✅ 登录信息（最后登录时间、登录次数）
- ✅ 邀请关系（邀请码、邀请人、被邀请人数）

### 钱包数据
- ✅ 现金余额（随机金额，按角色调整）
- ✅ 冻结金额（余额的一定比例）
- ✅ 金币系统（余额、累计获得、累计消费）
- ✅ 收支统计（总收入、总支出）
- ✅ 钱包状态（正常、冻结）

### 拉黑关系
- ✅ 用户之间的拉黑关系
- ✅ 拉黑原因（随机生成）
- ✅ 拉黑状态（活跃、已取消）
- ✅ 时间信息（拉黑时间）

## ⚙️ 配置说明

可以通过修改 `test_data_config.py` 来自定义数据生成规则：

### 用户角色分布
```python
USER_ROLE_WEIGHTS = {
    'user': 70,      # 普通用户 70%
    'blogger': 20,   # 博主 20%
    'admin': 5,      # 管理员 5%
    'vip': 5         # VIP用户 5%
}
```

### 数据范围配置
```python
GENERATION_CONFIG = {
    'follower_count_range': (0, 10000),    # 粉丝数范围
    'balance_range': (0, 10000),           # 余额范围
    'coin_balance_range': (0, 50000),      # 金币范围
    # 更多配置...
}
```

## 🔧 高级功能

### 1. 数据关联
- 自动建立用户邀请关系
- 钱包与用户一对一关联
- 拉黑关系避免重复创建

### 2. 数据真实性
- 使用中文姓名和地址
- 符合中国手机号格式
- 真实的邮箱格式
- 合理的数据分布

### 3. 性能优化
- 批量插入数据
- 避免重复查询
- 内存优化处理

### 4. 错误处理
- 数据库事务回滚
- 唯一性约束检查
- 详细错误信息

## 🧪 测试用途

### 功能测试
- 用户注册登录流程
- 用户信息CRUD操作
- 钱包系统功能
- 拉黑功能测试

### 性能测试
- 大量用户数据查询
- 分页性能测试
- 数据库连接池测试
- 并发操作测试

### 接口测试
- API响应时间测试
- 数据格式验证
- 边界条件测试
- 异常情况处理

## 📝 使用建议

1. **开发阶段**: 使用 `small` 场景，数据量小，创建快速
2. **测试阶段**: 使用 `default` 或 `medium` 场景
3. **性能测试**: 使用 `large` 场景
4. **演示环境**: 使用 `demo` 场景，数据精心设计

## ⚠️ 注意事项

1. **数据清理**: 使用 `--clear` 参数会删除所有现有数据
2. **密码安全**: 所有测试用户密码都是 `123456`，仅用于测试
3. **邮箱格式**: 生成的邮箱是虚假的，仅用于测试
4. **数据一致性**: 脚本会确保数据的完整性和一致性

## 🚨 故障排除

### 常见错误

1. **导入错误**: 确保已安装 `faker` 依赖
2. **数据库连接**: 检查数据库配置和连接
3. **重复数据**: 脚本会自动处理唯一性约束
4. **内存不足**: 大量数据生成时可能需要较多内存

### 解决方案

```bash
# 检查依赖
pip list | grep faker

# 测试数据库连接
python -c "from app.database.connection import engine; print('数据库连接正常')"

# 清理重新开始
python create_test_data.py --clear-only
python create_test_data.py --scenario small
```

---

如有问题，请参考项目文档或联系开发团队。