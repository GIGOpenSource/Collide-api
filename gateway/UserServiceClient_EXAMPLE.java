package com.gig.collide.auth.feign;

import com.gig.collide.auth.dto.*;
import com.gig.collide.common.response.ApiResponse;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;

/**
 * 用户服务Feign客户端 - 示例
 * 调用用户服务的内部接口
 * 
 * @author GIG Team
 * @version 2.0.0
 */
@FeignClient(
    name = "user-service",                    // 用户服务名称
    path = "/api/v1/users/internal",          // 内部接口路径
    fallback = UserServiceClientFallback.class // 降级处理
)
public interface UserServiceClient {

    /**
     * 创建用户
     * 对应：POST /api/v1/users/internal/create
     */
    @PostMapping("/create")
    ApiResponse<UserInfo> createUser(@RequestBody UserCreateRequest request);

    /**
     * 验证用户密码
     * 对应：POST /api/v1/users/internal/verify-password
     */
    @PostMapping("/verify-password")
    ApiResponse<Boolean> verifyPassword(@RequestBody UserPasswordVerifyRequest request);

    /**
     * 根据登录标识符查找用户
     * 对应：POST /api/v1/users/internal/find-by-identifier
     */
    @PostMapping("/find-by-identifier")
    ApiResponse<UserByIdentifierResponse> findUserByIdentifier(@RequestBody UserByIdentifierRequest request);

    /**
     * 更新用户登录信息
     * 对应：POST /api/v1/users/internal/update-login-info/{user_id}
     */
    @PostMapping("/update-login-info/{userId}")
    ApiResponse<Boolean> updateLoginInfo(@PathVariable("userId") Integer userId);
}

/**
 * 用户服务降级处理
 */
@Component
@Slf4j
class UserServiceClientFallback implements UserServiceClient {

    @Override
    public ApiResponse<UserInfo> createUser(UserCreateRequest request) {
        log.error("调用用户服务创建用户失败，触发降级处理");
        return ApiResponse.error("用户服务暂不可用，请稍后重试");
    }

    @Override
    public ApiResponse<Boolean> verifyPassword(UserPasswordVerifyRequest request) {
        log.error("调用用户服务验证密码失败，触发降级处理");
        return ApiResponse.error("认证服务暂不可用，请稍后重试");
    }

    @Override
    public ApiResponse<UserByIdentifierResponse> findUserByIdentifier(UserByIdentifierRequest request) {
        log.error("调用用户服务查找用户失败，触发降级处理");
        return ApiResponse.error("用户服务暂不可用，请稍后重试");
    }

    @Override
    public ApiResponse<Boolean> updateLoginInfo(Integer userId) {
        log.error("调用用户服务更新登录信息失败，触发降级处理");
        return ApiResponse.error("用户服务暂不可用");
    }
}
