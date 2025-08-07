# Sa-Token 网关认证配置文档

## 概述

本文档说明了为Collide用户微服务项目配置的Sa-Token网关认证规则。配置包含两个主要文件：

- `SaTokenConfigure.java` - 定义API路径的认证规则
- `StpInterfaceImpl.java` - 定义用户角色和权限体系

## 角色体系

### 角色层级
```
admin (管理员)
├── blogger (博主)
├── vip (VIP用户)
└── user (普通用户)
```

### 角色权限
| 角色 | 权限说明 |
|------|----------|
| **admin** | 拥有所有权限，包括系统管理、用户管理等 |
| **blogger** | 拥有博主权限和钱包管理权限 |
| **vip** | 拥有VIP权限和钱包管理权限 |
| **user** | 基础用户权限，包括编辑个人信息、查看钱包 |

### 特殊权限检查
- **VIP权限**: 除了role字段外，还会检查`vip_expire_time`字段来动态判断VIP权限
- **状态检查**: 只有状态为`active`的用户才能获得权限

## API路径认证规则

### 🔓 无需认证的接口

#### 系统接口
- `/favicon.ico` - 网站图标
- `/actuator/health` - 健康检查
- `/health` - 健康检查
- `/` - 根路径服务信息

#### 认证服务公开接口
- `/api/v1/auth/login` - 用户登录
- `/api/v1/auth/register` - 用户注册
- `/api/v1/auth/login-or-register` - 登录或注册
- `/api/v1/auth/validate-invite-code` - 验证邀请码
- `/api/v1/auth/test` - 测试接口

#### 用户服务内部接口（服务间调用）
- `/api/v1/users/internal/**` - 所有内部接口

#### 其他公开接口
- `/api/v1/users/{userId}` (GET) - 获取指定用户信息（可选登录）

### 🔒 需要登录的接口

#### 认证服务
- `/api/v1/auth/logout` - 用户登出
- `/api/v1/auth/me` - 获取当前用户信息
- `/api/v1/auth/verify-token` - 验证Token
- `/api/v1/auth/my-invite-info` - 获取邀请信息

#### 用户服务 - 基础功能
- `/api/v1/users/me` (GET/PUT) - 获取/更新当前用户信息
- `/api/v1/users/password` (PUT) - 修改密码
- `/api/v1/users/me/wallet` (GET) - 获取当前用户钱包信息
- `/api/v1/users/me/wallet/coin/**` - 金币操作
- `/api/v1/users/me/blocks` - 拉黑管理
- `/api/v1/users/{userId}/wallet` (GET) - 获取指定用户钱包（需权限）
- `/api/v1/users` (GET) - 获取用户列表

### 🎖️ 需要特定角色的接口

#### Admin角色需求
- `/admin/**` - 所有管理功能

## 权限验证流程

### 1. 用户信息获取
从Sa-Token Session中获取`userInfo`对象，包含：
```json
{
  "role": "user|blogger|vip|admin",
  "status": "active|inactive|blocked",
  "vip_expire_time": "2024-12-31T23:59:59",
  "user_id": 123,
  "username": "example"
}
```

### 2. 状态检查
- 只有`status = "active"`的用户才能通过认证
- 非活跃用户返回空权限/角色列表

### 3. 角色继承
- `admin` → 包含 `blogger`, `vip`, `user`
- `blogger` → 包含 `user`
- `vip` → 包含 `user`

### 4. 动态VIP检查
除了角色字段外，还会检查`vip_expire_time`：
- 如果当前时间 < VIP过期时间，自动添加VIP角色和权限
- 支持字符串（ISO格式）和时间戳格式

## 错误处理

### 认证异常处理
- `401` - 未登录：`请先登录`
- `403` - 权限不足：
  - 管理员权限：`需要管理员权限`
  - 博主权限：`需要博主认证`
  - VIP权限：`需要VIP权限`
  - 通用权限：`权限不足`
- `500` - 系统错误：`认证失败`

## 配置注意事项

### 1. 内部接口放行
用户服务的内部接口（`/api/v1/users/internal/**`）完全放行，因为这些是微服务之间的内部调用。

### 2. 可选登录接口
某些接口如获取指定用户信息支持可选登录，未登录时返回公开信息，登录时返回更详细信息。

### 3. 权限粒度
配置支持细粒度的权限控制，可以根据具体业务需求调整权限分配。

### 4. VIP权限的特殊处理
VIP权限支持基于时间的动态检查，这样可以准确控制VIP权限的有效期。

## 使用示例

### 在业务代码中检查权限
```java
// 检查是否登录
StpUtil.checkLogin();

// 检查角色
StpUtil.checkRole("admin");
StpUtil.checkRoleOr("blogger", "admin");

// 检查权限
StpUtil.checkPermission("user_manage");
StpUtil.checkPermissionOr("vip", "admin");
```

### 在Gateway中的应用
```java
// 需要登录
SaRouter.match("/api/v1/users/me").check(r -> StpUtil.checkLogin());

// 需要特定角色
SaRouter.match("/admin/**").check(r -> {
    StpUtil.checkLogin();
    StpUtil.checkRole("admin");
});

// 需要特定权限
SaRouter.match("/api/v1/users").check(r -> {
    StpUtil.checkLogin();
    StpUtil.checkPermissionOr("user_manage", "admin");
});
```

## 部署建议

1. **网关配置**: 确保Gateway正确传递用户信息到后端微服务
2. **Session存储**: 建议使用Redis等外部存储来保存用户Session信息
3. **权限缓存**: 考虑缓存用户权限信息以提高性能
4. **监控日志**: 关注认证异常日志，及时发现权限配置问题
