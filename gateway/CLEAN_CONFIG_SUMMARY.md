# Sa-Token 配置清理总结

## 🧹 清理内容

已删除所有与当前项目无关的旧配置，只保留认证(auth)和用户(users)服务相关的配置。

### 已删除的服务配置
- ❌ 社交服务 (`/api/v1/social/**`)
- ❌ 内容服务 (`/api/v1/content/**`)
- ❌ 收藏服务 (`/api/v1/favorite/**`)
- ❌ 点赞服务 (`/api/v1/like/**`)
- ❌ 关注服务 (`/api/v1/follow/**`)
- ❌ 评论服务 (`/api/v1/comment/**`)
- ❌ 文件服务 (`/api/v1/files/**`)
- ❌ 订单服务 (`/api/v1/order/**`)
- ❌ 支付服务 (`/api/v1/payment/**`)
- ❌ 商品服务 (`/api/v1/goods/**`)
- ❌ 搜索服务 (`/api/v1/search/**`)
- ❌ 标签服务 (`/api/v1/tag/**`)
- ❌ 分类服务 (`/api/v1/category/**`)

### 已删除的权限码
- ❌ `content_read` - 读取内容
- ❌ `social_read` - 读取社交内容
- ❌ `content_create` - 内容创建
- ❌ `content_edit` - 内容编辑
- ❌ `content_delete` - 内容删除
- ❌ `content_manage` - 内容管理
- ❌ `content_vip_access` - VIP内容访问
- ❌ `social_interact` - 社交互动
- ❌ `comment_manage` - 评论管理
- ❌ `order_manage` - 订单管理
- ❌ `order_view` - 查看订单
- ❌ `goods_manage` - 商品管理
- ❌ `goods_create` - 商品创建
- ❌ `content_create_basic` - 基础内容创建
- ❌ `priority_support` - 优先支持

## ✅ 保留的配置

### API路径认证
#### 🔓 无需认证
- `/favicon.ico`, `/health`, `/` - 系统接口
- `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/login-or-register` - 认证公开接口
- `/api/v1/users/internal/**` - 用户服务内部接口
- `/api/v1/users/{userId}` (GET) - 获取指定用户信息（可选登录）

#### 🔒 需要登录
- `/api/v1/auth/logout`, `/api/v1/auth/me` - 认证服务
- `/api/v1/users/me` - 用户信息管理
- `/api/v1/users/me/wallet/**` - 钱包管理
- `/api/v1/users/me/blocks/**` - 拉黑管理
- `/api/v1/users/{userId}/wallet` - 查看指定用户钱包
- `/api/v1/users` (GET) - 获取用户列表

#### 🎖️ 需要特定角色
- `/admin/**` - 管理员权限

### 角色体系
```
admin → blogger, vip, user
blogger → user  
vip → user
user → 基础权限
```

### 保留的权限码
- ✅ `basic` - 基础权限
- ✅ `user_info_read` - 读取用户信息
- ✅ `user_info_edit` - 编辑用户信息
- ✅ `wallet_view` - 查看钱包
- ✅ `wallet_manage` - 钱包管理
- ✅ `user_manage` - 用户管理
- ✅ `system_manage` - 系统管理
- ✅ `blogger` - 博主权限
- ✅ `vip` - VIP权限
- ✅ `admin` - 管理员权限

### 各角色权限分配
| 角色 | 权限列表 |
|------|----------|
| **admin** | `admin`, `user_manage`, `system_manage`, `blogger`, `vip`, `user_info_edit`, `wallet_manage` |
| **blogger** | `blogger`, `user_info_edit`, `wallet_manage` |
| **vip** | `vip`, `user_info_edit`, `wallet_manage` |
| **user** | `user_info_edit`, `wallet_view` |

## 🎯 清理后的优势

1. **简洁明了**: 只包含当前实际使用的认证和用户服务配置
2. **易于维护**: 减少了不必要的复杂性，更容易理解和修改
3. **性能优化**: 减少了权限检查的开销
4. **扩展性**: 为未来新服务留下了清晰的扩展空间

## 🚀 下一步操作

当需要添加新服务时，可以参考以下模式：

```java
// 公开接口
SaRouter.match("/api/v1/新服务/public/**").stop();

// 需要登录
SaRouter.match("/api/v1/新服务/user/**").check(r -> StpUtil.checkLogin());

// 需要特定角色
SaRouter.match("/api/v1/新服务/admin/**").check(r -> {
    StpUtil.checkLogin();
    StpUtil.checkRole("admin");
});
```

并在 `StpInterfaceImpl.java` 中添加相应的权限码。
