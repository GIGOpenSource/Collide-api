# Spring Gateway 头部传递配置

## 🎯 重要说明

基于您的配置，用户信息是通过 **HTTP Headers** 从Gateway传递到用户服务的：

- `X-User-Id` - 用户ID
- `X-Username` - 用户名
- `X-User-Role` - 用户角色

## 📋 Gateway配置

### 1. Gateway过滤器配置

需要在Spring Gateway中配置全局过滤器，将Sa-Token Session信息转换为HTTP Headers传递给下游服务。

```java
package com.gig.collide.gateway.filter;

import cn.dev33.satoken.stp.StpUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * 用户信息头部传递过滤器
 * 将Sa-Token Session信息转换为HTTP Headers传递给下游微服务
 */
@Component
@Slf4j
public class UserInfoHeaderFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        try {
            // 检查用户是否登录
            if (StpUtil.isLogin()) {
                // 获取用户ID
                Object loginId = StpUtil.getLoginId();
                
                // 从Session获取用户信息
                Map<String, Object> userInfo = (Map<String, Object>) StpUtil.getSession().get("userInfo");
                
                if (userInfo != null) {
                    // 构建新的请求头
                    ServerHttpRequest.Builder requestBuilder = exchange.getRequest().mutate();
                    
                    // 添加用户信息头部
                    requestBuilder.header("X-User-Id", String.valueOf(userInfo.get("user_id")));
                    requestBuilder.header("X-Username", (String) userInfo.get("username"));
                    requestBuilder.header("X-User-Role", (String) userInfo.get("role"));
                    
                    // 可选：添加更多用户信息
                    if (userInfo.get("nickname") != null) {
                        requestBuilder.header("X-User-Nickname", (String) userInfo.get("nickname"));
                    }
                    if (userInfo.get("email") != null) {
                        requestBuilder.header("X-User-Email", (String) userInfo.get("email"));
                    }
                    
                    // 创建新的ServerWebExchange
                    ServerWebExchange newExchange = exchange.mutate()
                            .request(requestBuilder.build())
                            .build();
                    
                    log.debug("已添加用户信息头部：user_id={}, username={}, role={}", 
                            userInfo.get("user_id"), userInfo.get("username"), userInfo.get("role"));
                    
                    return chain.filter(newExchange);
                }
            }
        } catch (Exception e) {
            log.error("处理用户信息头部时发生异常：", e);
        }
        
        // 未登录或异常情况，直接传递原始请求
        return chain.filter(exchange);
    }

    @Override
    public int getOrder() {
        // 确保在认证过滤器之后执行
        return Ordered.LOWEST_PRECEDENCE - 100;
    }
}
```

### 2. 路由配置示例

```yaml
# application.yml
spring:
  cloud:
    gateway:
      routes:
        # 用户服务路由
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/v1/users/**
          filters:
            - name: UserInfoHeader  # 自定义过滤器名称
            
        # 认证服务路由  
        - id: auth-service
          uri: lb://auth-service
          predicates:
            - Path=/api/v1/auth/**
```

### 3. 认证服务Session设置更新

基于您的头部配置，更新之前的认证服务示例：

```java
/**
 * 设置用户Session信息
 * 确保字段名与Gateway过滤器和用户服务期望的一致
 */
private void setUserSession(UserInfo userInfo) {
    Map<String, Object> userInfoMap = new HashMap<>();
    
    // 核心字段 - 必须与HTTP Headers对应
    userInfoMap.put("user_id", userInfo.getId());           // 对应 X-User-Id
    userInfoMap.put("username", userInfo.getUsername());     // 对应 X-Username
    userInfoMap.put("role", userInfo.getRole());            // 对应 X-User-Role
    userInfoMap.put("status", userInfo.getStatus());        // 状态检查用
    
    // 可选字段
    userInfoMap.put("nickname", userInfo.getNickname());
    userInfoMap.put("email", userInfo.getEmail());
    userInfoMap.put("phone", userInfo.getPhone());
    userInfoMap.put("vip_expire_time", userInfo.getVipExpireTime());
    
    // 设置到Sa-Token Session中
    StpUtil.getSession().set("userInfo", userInfoMap);
    
    log.debug("用户 {} Session信息设置完成", userInfo.getUsername());
}
```

## 🔧 验证配置

### 1. 测试Gateway头部传递

创建测试接口验证头部传递：

```python
# 在用户服务中添加测试接口
@router.get("/debug/headers", summary="调试：查看请求头部")
async def debug_headers(
    request: Request,
    user_context: Optional[UserContext] = Depends(get_optional_user_context)
):
    """调试接口：查看Gateway传递的头部信息"""
    headers = dict(request.headers)
    
    return {
        "headers": headers,
        "user_context": user_context.dict() if user_context else None,
        "parsed_user_info": {
            "user_id": headers.get("x-user-id"),
            "username": headers.get("x-username"), 
            "role": headers.get("x-user-role")
        }
    }
```

### 2. 测试流程

1. **登录认证服务**：
   ```bash
   POST /api/v1/auth/login
   {
     "identifier": "test@example.com",
     "password": "password123"
   }
   ```

2. **携带Token访问用户服务**：
   ```bash
   GET /api/v1/users/debug/headers
   Authorization: Bearer {token}
   ```

3. **验证响应**：
   ```json
   {
     "headers": {
       "x-user-id": "123",
       "x-username": "testuser",
       "x-user-role": "user"
     },
     "user_context": {
       "user_id": 123,
       "username": "testuser", 
       "role": "user"
     }
   }
   ```

## 🚨 注意事项

### 1. 安全考虑
- 确保这些头部只能由Gateway设置，下游服务不应信任外部请求中的这些头部
- 在Gateway中清理可能存在的用户头部，防止伪造

### 2. 字段映射
确保三个地方的字段名保持一致：
- **认证服务Session**: `user_id`, `username`, `role`
- **Gateway Headers**: `X-User-Id`, `X-Username`, `X-User-Role`  
- **用户服务配置**: `USER_ID_HEADER=X-User-Id`

### 3. 错误处理
- Gateway过滤器要处理Session不存在的情况
- 用户服务要处理头部缺失的情况
- 记录详细日志便于排查问题

## 📖 总结

您的架构使用 **`user_id_header`** 方式，即：

1. **认证服务**设置Sa-Token Session信息
2. **Gateway过滤器**从Session提取信息转换为HTTP Headers
3. **用户服务**从HTTP Headers获取用户信息

这种方式的优势是微服务间解耦，用户服务不需要直接访问Session存储。
