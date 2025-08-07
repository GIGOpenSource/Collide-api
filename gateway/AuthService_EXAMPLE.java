package com.gig.collide.auth.service;

import com.gig.collide.auth.dto.LoginRequest;
import com.gig.collide.auth.dto.LoginOrRegisterRequest;
import com.gig.collide.auth.dto.UserInfo;
import com.gig.collide.auth.feign.UserServiceClient;
import com.gig.collide.common.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * 认证服务 - 示例
 * 展示如何调用用户服务的内部接口进行用户认证
 * 
 * @author GIG Team
 * @version 2.0.0
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UserServiceClient userServiceClient;

    /**
     * 用户认证
     * 验证用户身份并返回用户信息
     */
    public UserInfo authenticateUser(LoginRequest request) {
        try {
            // 1. 根据登录标识查找用户
            UserByIdentifierRequest findRequest = new UserByIdentifierRequest();
            findRequest.setIdentifier(request.getIdentifier());
            
            ApiResponse<UserByIdentifierResponse> findResult = userServiceClient.findUserByIdentifier(findRequest);
            if (findResult == null || !findResult.isSuccess() || findResult.getData() == null) {
                log.warn("查找用户失败：{}", request.getIdentifier());
                return null;
            }
            
            UserByIdentifierResponse userResponse = findResult.getData();
            if (!userResponse.isExists() || userResponse.getUserInfo() == null) {
                log.warn("用户不存在：{}", request.getIdentifier());
                return null;
            }
            
            UserInfo userInfo = userResponse.getUserInfo();
            
            // 2. 验证密码
            UserPasswordVerifyRequest verifyRequest = new UserPasswordVerifyRequest();
            verifyRequest.setUserId(userInfo.getId());
            verifyRequest.setPassword(request.getPassword());
            
            ApiResponse<Boolean> verifyResult = userServiceClient.verifyPassword(verifyRequest);
            if (verifyResult == null || !verifyResult.isSuccess() || !Boolean.TRUE.equals(verifyResult.getData())) {
                log.warn("密码验证失败：用户ID {}", userInfo.getId());
                return null;
            }
            
            log.info("用户认证成功：{}", userInfo.getUsername());
            return userInfo;
            
        } catch (Exception e) {
            log.error("用户认证异常：", e);
            return null;
        }
    }

    /**
     * 根据标识符查找用户
     */
    public UserInfo findUserByIdentifier(String identifier) {
        try {
            UserByIdentifierRequest request = new UserByIdentifierRequest();
            request.setIdentifier(identifier);
            
            ApiResponse<UserByIdentifierResponse> result = userServiceClient.findUserByIdentifier(request);
            if (result != null && result.isSuccess() && result.getData() != null) {
                UserByIdentifierResponse response = result.getData();
                if (response.isExists()) {
                    return response.getUserInfo();
                }
            }
            
            return null;
        } catch (Exception e) {
            log.error("查找用户异常：", e);
            return null;
        }
    }

    /**
     * 验证用户密码
     */
    public boolean verifyPassword(Integer userId, String password) {
        try {
            UserPasswordVerifyRequest request = new UserPasswordVerifyRequest();
            request.setUserId(userId);
            request.setPassword(password);
            
            ApiResponse<Boolean> result = userServiceClient.verifyPassword(request);
            return result != null && result.isSuccess() && Boolean.TRUE.equals(result.getData());
        } catch (Exception e) {
            log.error("验证密码异常：", e);
            return false;
        }
    }

    /**
     * 注册新用户
     */
    public UserInfo registerUser(LoginOrRegisterRequest request) {
        try {
            UserCreateRequest createRequest = new UserCreateRequest();
            createRequest.setUsername(generateUsername(request.getIdentifier()));
            createRequest.setNickname(request.getNickname() != null ? request.getNickname() : "新用户");
            createRequest.setPassword(request.getPassword());
            createRequest.setEmail(isEmail(request.getIdentifier()) ? request.getIdentifier() : null);
            createRequest.setPhone(isPhone(request.getIdentifier()) ? request.getIdentifier() : null);
            createRequest.setRole("user");
            createRequest.setInviteCode(request.getInviteCode());
            
            ApiResponse<UserInfo> result = userServiceClient.createUser(createRequest);
            if (result != null && result.isSuccess() && result.getData() != null) {
                log.info("用户注册成功：{}", createRequest.getUsername());
                return result.getData();
            }
            
            log.error("用户注册失败：{}", result != null ? result.getMessage() : "未知错误");
            return null;
        } catch (Exception e) {
            log.error("注册用户异常：", e);
            return null;
        }
    }

    /**
     * 更新用户登录信息
     */
    public void updateUserLoginInfo(Integer userId) {
        try {
            ApiResponse<Boolean> result = userServiceClient.updateLoginInfo(userId);
            if (result == null || !result.isSuccess()) {
                log.warn("更新用户登录信息失败：用户ID {}", userId);
            }
        } catch (Exception e) {
            log.error("更新登录信息异常：", e);
        }
    }

    /**
     * 获取用户信息
     */
    public UserInfo getUserInfo(Integer userId) {
        try {
            // 这里可以调用用户服务的获取用户信息接口
            // 或者从缓存中获取
            return null; // 根据实际情况实现
        } catch (Exception e) {
            log.error("获取用户信息异常：", e);
            return null;
        }
    }

    // ==================== 工具方法 ====================

    /**
     * 生成用户名
     */
    private String generateUsername(String identifier) {
        if (isEmail(identifier)) {
            return identifier.split("@")[0];
        } else if (isPhone(identifier)) {
            return "user_" + identifier.substring(identifier.length() - 4);
        } else {
            return identifier;
        }
    }

    /**
     * 判断是否为邮箱
     */
    private boolean isEmail(String identifier) {
        return identifier != null && identifier.contains("@");
    }

    /**
     * 判断是否为手机号
     */
    private boolean isPhone(String identifier) {
        return identifier != null && identifier.matches("^1[3-9]\\d{9}$");
    }
}
