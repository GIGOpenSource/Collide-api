# Collide User Service - 用户微服务

基于 FastAPI 3.11 开发的用户微服务，采用领域驱动设计（DDD）和无连表设计原则。支持Spring Gateway + Sa-Token架构，集成Nacos服务注册与发现。

## 🏗️ 项目架构

```
Collide-api/
├── app/                          # 应用主目录
│   ├── common/                   # 公共模块
│   │   ├── config.py            # 配置管理
│   │   ├── response.py          # 统一响应模型
│   │   ├── exceptions.py        # 自定义异常
│   │   ├── security.py          # 安全相关（JWT、密码加密）
│   │   ├── pagination.py        # 分页工具
│   │   ├── dependencies.py      # FastAPI依赖项
│   │   └── exception_handlers.py # 全局异常处理器
│   ├── database/                 # 数据库模块
│   │   ├── connection.py        # 数据库连接配置
│   │   └── models.py            # SQLAlchemy模型
│   └── domains/                  # 业务域模块
│       └── users/               # 用户域
│           ├── schemas.py       # Pydantic模型
│           ├── service.py       # 业务服务层
│           └── router.py        # API路由
├── sql/                         # SQL数据库文件
├── main.py                      # 主应用文件
├── start.py                     # 启动脚本
├── requirements.txt             # 依赖包
└── .env.example                # 环境变量示例
```

## 🚀 快速开始

### 1. 环境准备

- Python 3.11+
- MySQL 8.0+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/collide

# JWT配置
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# 其他配置...
```

### 4. 配置Nacos（可选）

如果使用服务注册与发现：

```bash
# 启动Nacos服务器（单机模式）
# 下载并解压Nacos：https://nacos.io/zh-cn/docs/quick-start.html
cd nacos/bin
./startup.sh -m standalone

# 访问Nacos控制台：http://localhost:8848/nacos
# 默认用户名密码：nacos/nacos
```

### 5. 初始化数据库

执行 `sql/` 目录下的 SQL 文件来创建数据库表：

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE collide;"

# 执行用户模块SQL
mysql -u root -p collide < sql/users-simple.sql
```

### 6. 启动服务

```bash
# 方式1：使用启动脚本
python start.py

# 方式2：直接运行
python main.py

# 方式3：使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. 访问API文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health
- 服务信息: http://localhost:8000/

如果启用了Nacos，可以在Nacos控制台查看服务注册情况。

## 🏛️ 微服务架构

本服务设计为微服务架构中的用户服务组件：

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   客户端应用      │───▶│  Spring Gateway  │───▶│  Sa-Token认证   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────┐         ┌─────────────────┐
                       │    Nacos    │◀────────│ User Service    │
                       │ 服务注册中心  │         │  (本服务)       │
                       └─────────────┘         └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────┐         ┌─────────────────┐
                       │ 其他微服务   │         │    MySQL        │
                       │ Content等    │         │   用户数据库     │
                       └─────────────┘         └─────────────────┘
```

### 架构特点：

1. **服务注册** - 自动注册到Nacos，支持服务发现
2. **统一网关** - 通过Spring Gateway统一入口
3. **认证分离** - Sa-Token处理认证，服务专注业务逻辑
4. **头部传递** - 网关将用户信息通过HTTP头传递给服务
5. **健康检查** - 提供多个健康检查端点
6. **优雅关闭** - 支持信号处理和服务注销

### 请求流程：

1. 客户端请求到达Spring Gateway
2. Gateway进行路由和Sa-Token认证
3. 认证成功后，Gateway将用户信息添加到请求头
4. 请求转发到对应的微服务
5. 微服务从请求头获取用户信息，处理业务逻辑

## 📚 API 设计原则

### 1. 统一响应格式

#### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "success": true
}
```

#### 错误响应
```json
{
  "code": 400,
  "message": "error message",
  "data": null,
  "success": false
}
```

#### 分页响应
```json
{
  "success": true,
  "code": "200",
  "message": "操作成功",
  "data": {
    "datas": {...},
    "total": 100,
    "currentPage": 1,
    "pageSize": 20,
    "totalPage": 5
  }
}
```

### 2. 错误码规范

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 无权限
- `404`: 资源不存在
- `500`: 服务器内部错误

业务错误码：
- `1001`: 用户不存在
- `1002`: 用户已存在
- `1003`: 登录凭证无效
- `1004`: 余额不足
- `1005`: 操作失败

## 🔧 用户微服务API

### 内部服务接口（供认证服务调用）
- `POST /api/users/internal/create` - 创建用户
- `POST /api/users/internal/verify-password` - 验证用户密码
- `POST /api/users/internal/find-by-identifier` - 根据登录标识符查找用户
- `POST /api/users/internal/update-login-info/{user_id}` - 更新登录信息

### 用户信息
- `GET /api/users/me` - 获取当前用户信息
- `GET /api/users/{user_id}` - 获取指定用户信息
- `PUT /api/users/me` - 更新用户信息
- `PUT /api/users/password` - 修改密码

### 钱包管理
- `GET /api/users/me/wallet` - 获取钱包信息
- `POST /api/users/me/wallet/coin/grant` - 发放金币奖励
- `POST /api/users/me/wallet/coin/consume` - 消费金币

### 用户拉黑
- `POST /api/users/me/blocks` - 拉黑用户
- `DELETE /api/users/me/blocks/{user_id}` - 取消拉黑
- `GET /api/users/me/blocks` - 获取拉黑列表

### 用户列表
- `GET /api/users` - 获取用户列表（支持搜索筛选）

## 🛡️ 安全特性

1. **网关认证** - 通过Spring Gateway + Sa-Token进行统一认证
2. **密码加密** - 使用bcrypt进行密码哈希
3. **请求验证** - Pydantic模型验证所有输入
4. **SQL注入防护** - SQLAlchemy ORM防止SQL注入
5. **CORS配置** - 生产环境限制跨域访问
6. **头部传递** - 从网关获取用户身份信息

## 🔨 开发规范

### 1. 代码结构
- **领域驱动设计**: 按业务域组织代码
- **分层架构**: Router → Service → Database
- **依赖注入**: 使用FastAPI的依赖注入系统

### 2. 数据库设计
- **无连表原则**: 通过冗余字段避免复杂连表查询
- **字段冗余**: 适当冗余提高查询性能
- **索引优化**: 为高频查询字段建立索引

### 3. 错误处理
- **自定义异常**: 业务异常继承BusinessException
- **全局处理**: 统一的异常处理器
- **日志记录**: 完整的错误日志

## 📈 性能优化

1. **数据库连接池** - SQLAlchemy连接池管理
2. **查询优化** - 避免N+1查询问题
3. **响应缓存** - 可扩展Redis缓存
4. **分页查询** - 所有列表接口支持分页

## 🧪 测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
pytest
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请联系开发团队。