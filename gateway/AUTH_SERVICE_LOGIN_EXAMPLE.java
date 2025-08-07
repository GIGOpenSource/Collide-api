package com.gig.collide.auth.controller;

import cn.dev33.satoken.stp.StpUtil;
import cn.dev33.satoken.util.SaResult;
import com.gig.collide.auth.dto.LoginRequest;
import com.gig.collide.auth.dto.LoginResponse;
import com.gig.collide.auth.service.AuthService;
import com.gig.collide.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 认证服务登录控制器 - 示例
 * 展示如何在登录成功后设置Sa-Token Session信息
 * 
 * @author GIG Team
 * @version 2.0.0
 */
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "认证服务", description = "用户认证相关接口")
public class AuthController {

    private final AuthService authService;

    /**
     * 用户登录接口
     * 登录成功后设置Sa-Token Session信息
     */
    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "用户名/邮箱/手机号登录")
    public ApiResponse<LoginResponse> login(@RequestBody LoginRequest request) {
        try {
            // 1. 调用用户服务验证用户身份
            UserInfo userInfo = authService.authenticateUser(request);
            
            if (userInfo == null) {
                return ApiResponse.error("用户名或密码错误");
            }
            
            // 2. 执行Sa-Token登录，传入用户ID
            StpUtil.login(userInfo.getId());
            
            // 3. 设置用户信息到Session中（重要！这里是设置Session的地方）
            setUserSession(userInfo);
            
            // 4. 调用用户服务更新登录信息
            authService.updateUserLoginInfo(userInfo.getId());
            
            // 5. 生成响应
            LoginResponse response = LoginResponse.builder()
                    .token(StpUtil.getTokenValue())
                    .userInfo(userInfo)
                    .expiresIn(StpUtil.getTokenTimeout())
                    .build();
            
            log.info("用户 {} 登录成功", userInfo.getUsername());
            return ApiResponse.success(response, "登录成功");
            
        } catch (Exception e) {
            log.error("登录失败：", e);
            return ApiResponse.error("登录失败，请稍后重试");
        }
    }

    /**
     * 设置用户Session信息
     * 这是关键方法：将用户信息存储到Sa-Token Session中
     * 供StpInterfaceImpl获取权限时使用
     */
    private void setUserSession(UserInfo userInfo) {
        // 构建用户信息Map
        Map<String, Object> userInfoMap = new HashMap<>();
        userInfoMap.put("user_id", userInfo.getId());
        userInfoMap.put("username", userInfo.getUsername());
        userInfoMap.put("nickname", userInfo.getNickname());
        userInfoMap.put("role", userInfo.getRole());
        userInfoMap.put("status", userInfo.getStatus());
        userInfoMap.put("email", userInfo.getEmail());
        userInfoMap.put("phone", userInfo.getPhone());
        userInfoMap.put("vip_expire_time", userInfo.getVipExpireTime());
        
        // 设置到Sa-Token Session中
        // 这个userInfo对象会被StpInterfaceImpl.java中的getPermissionList和getRoleList方法使用
        StpUtil.getSession().set("userInfo", userInfoMap);
        
        log.debug("用户 {} Session信息设置完成：{}", userInfo.getUsername(), userInfoMap);
    }

    /**
     * 第三方登录或注册接口
     * 支持登录或注册逻辑
     */
    @PostMapping("/login-or-register")
    @Operation(summary = "登录或注册", description = "如果用户不存在则自动注册")
    public ApiResponse<LoginResponse> loginOrRegister(@RequestBody LoginOrRegisterRequest request) {
        try {
            // 1. 尝试查找用户
            UserInfo userInfo = authService.findUserByIdentifier(request.getIdentifier());
            
            if (userInfo == null) {
                // 2. 用户不存在，创建新用户
                userInfo = authService.registerUser(request);
                log.info("新用户注册成功：{}", userInfo.getUsername());
            } else {
                // 3. 用户存在，验证密码（如果有密码）
                if (request.getPassword() != null && !authService.verifyPassword(userInfo.getId(), request.getPassword())) {
                    return ApiResponse.error("密码错误");
                }
            }
            
            // 4. 执行登录流程
            StpUtil.login(userInfo.getId());
            setUserSession(userInfo);
            authService.updateUserLoginInfo(userInfo.getId());
            
            // 5. 生成响应
            LoginResponse response = LoginResponse.builder()
                    .token(StpUtil.getTokenValue())
                    .userInfo(userInfo)
                    .expiresIn(StpUtil.getTokenTimeout())
                    .isNewUser(userInfo.getLoginCount() == 1)
                    .build();
            
            return ApiResponse.success(response, "登录成功");
            
        } catch (Exception e) {
            log.error("登录或注册失败：", e);
            return ApiResponse.error("操作失败，请稍后重试");
        }
    }

    /**
     * 获取当前用户信息
     */
    @GetMapping("/me")
    @Operation(summary = "获取当前用户信息")
    public ApiResponse<UserInfo> getCurrentUser() {
        try {
            // 从Session中获取用户信息
            Map<String, Object> userInfoMap = (Map<String, Object>) StpUtil.getSession().get("userInfo");
            
            if (userInfoMap == null) {
                return ApiResponse.error("用户信息不存在，请重新登录");
            }
            
            // 也可以重新从用户服务获取最新信息
            Integer userId = (Integer) userInfoMap.get("user_id");
            UserInfo userInfo = authService.getUserInfo(userId);
            
            return ApiResponse.success(userInfo);
            
        } catch (Exception e) {
            log.error("获取用户信息失败：", e);
            return ApiResponse.error("获取用户信息失败");
        }
    }

    /**
     * 用户登出
     */
    @PostMapping("/logout")
    @Operation(summary = "用户登出")
    public ApiResponse<String> logout() {
        try {
            StpUtil.logout();
            return ApiResponse.success("登出成功");
        } catch (Exception e) {
            log.error("登出失败：", e);
            return ApiResponse.error("登出失败");
        }
    }

    /**
     * 验证Token
     */
    @PostMapping("/verify-token")
    @Operation(summary = "验证Token")
    public ApiResponse<Map<String, Object>> verifyToken() {
        try {
            Map<String, Object> result = new HashMap<>();
            result.put("isLogin", StpUtil.isLogin());
            result.put("userId", StpUtil.getLoginIdAsInt());
            result.put("tokenValue", StpUtil.getTokenValue());
            result.put("tokenTimeout", StpUtil.getTokenTimeout());
            
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("验证Token失败：", e);
            return ApiResponse.error("Token验证失败");
        }
    }
}
