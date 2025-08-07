package com.gig.collide.gateway.auth;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotPermissionException;
import cn.dev33.satoken.exception.NotRoleException;
import cn.dev33.satoken.reactor.filter.SaReactorFilter;
import cn.dev33.satoken.router.SaRouter;
import cn.dev33.satoken.stp.StpUtil;
import cn.dev33.satoken.util.SaResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Sa-Token 网关统一鉴权配置 - 用户服务版
 * 基于Collide用户微服务API设计的认证配置
 * 
 * @author GIG Team
 * @version 2.0.0
 */
@Configuration
@Slf4j
public class SaTokenConfigure {

    @Bean
    public SaReactorFilter getSaReactorFilter() {
        return new SaReactorFilter()
                // 拦截所有路径
                .addInclude("/**")
                
                // ========== 系统级放行路径 ==========
                .addExclude("/favicon.ico")
                .addExclude("/actuator/health")
                .addExclude("/health")  // 健康检查
                .addExclude("/")        // 根路径服务信息
                
                // ========== 认证服务公开接口 ==========
                .addExclude("/api/v1/auth/login")
                .addExclude("/api/v1/auth/register") 
                .addExclude("/api/v1/auth/login-or-register")
                .addExclude("/api/v1/auth/validate-invite-code")
                .addExclude("/api/v1/auth/test")
                
                // ========== 用户服务内部接口（服务间调用，网关不拦截） ==========
                .addExclude("/api/v1/users/internal/**")
                
                // 鉴权方法：每次访问进入
                .setAuth(obj -> {
                    // ========== 认证服务：部分需要登录 ==========
                    SaRouter.match("/api/v1/auth/logout").check(r -> StpUtil.checkLogin());
                    SaRouter.match("/api/v1/auth/me").check(r -> StpUtil.checkLogin());
                    SaRouter.match("/api/v1/auth/verify-token").check(r -> StpUtil.checkLogin());
                    SaRouter.match("/api/v1/auth/my-invite-info").check(r -> StpUtil.checkLogin());
                    
                    // ========== 用户服务：基础用户信息接口 ==========
                    // 获取当前用户信息 - 需要登录
                    SaRouter.match("/api/v1/users/me", "GET").check(r -> StpUtil.checkLogin());
                    // 更新当前用户信息 - 需要登录
                    SaRouter.match("/api/v1/users/me", "PUT").check(r -> StpUtil.checkLogin());
                    // 修改密码 - 需要登录
                    SaRouter.match("/api/v1/users/password", "PUT").check(r -> StpUtil.checkLogin());
                    
                    // ========== 用户钱包管理 ==========
                    // 获取当前用户钱包信息 - 需要登录
                    SaRouter.match("/api/v1/users/me/wallet", "GET").check(r -> StpUtil.checkLogin());
                    // 金币操作 - 需要登录
                    SaRouter.match("/api/v1/users/me/wallet/coin/**").check(r -> StpUtil.checkLogin());
                    
                    // ========== 用户拉黑管理 ==========
                    // 拉黑用户 - 需要登录
                    SaRouter.match("/api/v1/users/me/blocks", "POST").check(r -> StpUtil.checkLogin());
                    // 取消拉黑 - 需要登录
                    SaRouter.match("/api/v1/users/me/blocks/**", "DELETE").check(r -> StpUtil.checkLogin());
                    // 获取拉黑列表 - 需要登录
                    SaRouter.match("/api/v1/users/me/blocks", "GET").check(r -> StpUtil.checkLogin());
                    
                    // ========== 用户查看相关 ==========
                    // 获取指定用户信息 - 可选登录（用于区分是否显示敏感信息）
                    SaRouter.match("/api/v1/users/{userId}", "GET").stop();
                    // 获取指定用户钱包信息 - 需要登录且有权限
                    SaRouter.match("/api/v1/users/{userId}/wallet", "GET").check(r -> StpUtil.checkLogin());
                    
                    // ========== 用户列表管理 ==========
                    // 获取用户列表 - 需要登录（管理员或特定权限用户）
                    SaRouter.match("/api/v1/users", "GET").check(r -> {
                        StpUtil.checkLogin();
                        // 可以根据需要添加额外的权限检查
                        // StpUtil.checkRoleOr("admin", "blogger");
                    });
                    
                    // ========== 管理功能：需要管理员权限 ==========
                    SaRouter.match("/admin/**").check(r -> {
                        StpUtil.checkLogin();
                        StpUtil.checkRole("admin");
                    });
                })
                
                // 异常处理方法：每次setAuth函数出现异常时进入
                .setError(this::handleAuthException);
    }

    /**
     * 统一异常处理
     */
    private SaResult handleAuthException(Throwable e) {
        log.warn("Sa-Token 鉴权异常：{}", e.getMessage());
        
        return switch (e) {
            case NotLoginException ex -> {
                log.info("用户未登录，访问路径：{}", ex.getMessage());
                yield SaResult.error("请先登录").setCode(401);
            }
            case NotRoleException ex -> {
                log.warn("用户权限不足，缺少角色：{}", ex.getRole());
                String role = ex.getRole();
                if ("admin".equals(role)) {
                    yield SaResult.error("需要管理员权限").setCode(403);
                } else if ("blogger".equals(role)) {
                    yield SaResult.error("需要博主认证").setCode(403);
                } else if ("vip".equals(role)) {
                    yield SaResult.error("需要VIP权限").setCode(403);
                }
                yield SaResult.error("权限不足").setCode(403);
            }
            case NotPermissionException ex -> {
                log.warn("用户权限不足，缺少权限：{}", ex.getPermission());
                String permission = ex.getPermission();
                if ("vip".equals(permission)) {
                    yield SaResult.error("需要VIP权限").setCode(403);
                } else if ("blogger".equals(permission)) {
                    yield SaResult.error("需要博主认证").setCode(403);
                } else if ("admin".equals(permission)) {
                    yield SaResult.error("需要管理员权限").setCode(403);
                }
                yield SaResult.error("权限不足").setCode(403);
            }
            default -> {
                log.error("未知认证异常：", e);
                yield SaResult.error("认证失败").setCode(500);
            }
        };
    }
}