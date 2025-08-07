"""
Collide User Service 微服务API使用示例
演示如何调用各个API接口（模拟网关传递用户信息）
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"

class CollideUserServiceClient:
    """Collide User Service 客户端"""
    
    def __init__(self, base_url: str = BASE_URL, user_id: int = None):
        self.base_url = base_url
        self.user_id = user_id
        self.headers = {"Content-Type": "application/json"}
        
        # 模拟网关传递的用户信息
        if user_id:
            self.headers.update({
                "X-User-Id": str(user_id),
                "X-Username": f"user_{user_id}",
                "X-User-Role": "user"
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs):
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 添加请求头
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        response = requests.request(method, url, **kwargs)
        
        try:
            return response.json()
        except:
            return {"error": "无法解析响应", "text": response.text}
    
    def set_user_context(self, user_id: int, username: str = None, role: str = "user"):
        """设置用户上下文（模拟网关传递）"""
        self.user_id = user_id
        self.headers.update({
            "X-User-Id": str(user_id),
            "X-Username": username or f"user_{user_id}",
            "X-User-Role": role
        })
    
    def health_check(self):
        """健康检查"""
        return self._make_request("GET", "/health")
    
    def create_user_internal(self, username: str, nickname: str, password: str = None, email: str = None, role: str = "user"):
        """创建用户（内部接口）"""
        data = {
            "username": username,
            "nickname": nickname,
            "role": role
        }
        if password:
            data["password"] = password
        if email:
            data["email"] = email
        
        return self._make_request("POST", "/api/users/internal/create", json=data)
    
    def verify_password_internal(self, user_id: int, password: str):
        """验证用户密码（内部接口）"""
        data = {
            "user_id": user_id,
            "password": password
        }
        
        return self._make_request("POST", "/api/users/internal/verify-password", json=data)
    
    def find_user_by_identifier_internal(self, identifier: str):
        """根据登录标识符查找用户（内部接口）"""
        data = {
            "identifier": identifier
        }
        
        return self._make_request("POST", "/api/users/internal/find-by-identifier", json=data)
    
    def get_current_user(self):
        """获取当前用户信息"""
        return self._make_request("GET", "/api/users/me")
    
    def get_user_wallet(self):
        """获取用户钱包信息"""
        return self._make_request("GET", "/api/users/me/wallet")
    
    def update_user_info(self, **kwargs):
        """更新用户信息"""
        return self._make_request("PUT", "/api/users/me", json=kwargs)
    
    def get_user_list(self, page: int = 1, page_size: int = 20, keyword: str = None):
        """获取用户列表"""
        params = {"page": page, "page_size": page_size}
        if keyword:
            params["keyword"] = keyword
        
        return self._make_request("GET", "/api/users", params=params)


def main():
    """微服务API测试演示"""
    client = CollideUserServiceClient()
    
    print("🚀 Collide User Service 微服务API 测试演示")
    print("=" * 60)
    
    # 1. 健康检查
    print("\n1. 健康检查")
    health = client.health_check()
    print(f"响应: {json.dumps(health, indent=2, ensure_ascii=False)}")
    
    # 2. 创建用户（内部接口）
    print("\n2. 创建用户（内部接口）")
    create_result = client.create_user_internal(
        username="demo_user_001",
        nickname="演示用户",
        password="123456",
        email="demo@example.com"
    )
    print(f"创建结果: {json.dumps(create_result, indent=2, ensure_ascii=False)}")
    
    # 从创建结果中获取用户ID
    user_id = None
    if create_result.get("success") and create_result.get("data"):
        user_id = create_result["data"]["id"]
        print(f"获取到用户ID: {user_id}")
    
    # 3. 根据标识符查找用户（内部接口）
    print("\n3. 根据登录标识符查找用户（内部接口）")
    find_result = client.find_user_by_identifier_internal("demo_user_001")
    print(f"查找结果: {json.dumps(find_result, indent=2, ensure_ascii=False)}")
    
    # 4. 验证用户密码（内部接口）
    if user_id:
        print("\n4. 验证用户密码（内部接口）")
        verify_result = client.verify_password_internal(user_id, "123456")
        print(f"验证结果: {json.dumps(verify_result, indent=2, ensure_ascii=False)}")
        
        # 设置用户上下文，模拟网关传递
        client.set_user_context(user_id, "demo_user_001", "user")
        print(f"设置用户上下文: user_id={user_id}")
    
    # 5. 获取当前用户信息（需要用户上下文）
    print("\n5. 获取当前用户信息")
    user_info = client.get_current_user()
    print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
    
    # 6. 获取钱包信息
    print("\n6. 获取钱包信息")
    wallet_info = client.get_user_wallet()
    print(f"钱包信息: {json.dumps(wallet_info, indent=2, ensure_ascii=False)}")
    
    # 7. 更新用户信息
    print("\n7. 更新用户信息")
    update_result = client.update_user_info(
        bio="这是一个演示用户的个人简介",
        location="北京市"
    )
    print(f"更新结果: {json.dumps(update_result, indent=2, ensure_ascii=False)}")
    
    # 8. 获取用户列表（无需用户上下文）
    print("\n8. 获取用户列表")
    client_no_user = CollideUserServiceClient()  # 无用户上下文的客户端
    user_list = client_no_user.get_user_list(page=1, page_size=5)
    print(f"用户列表: {json.dumps(user_list, indent=2, ensure_ascii=False)}")
    
    print("\n✅ 微服务API测试演示完成！")
    print("\n📝 微服务特点:")
    print("1. 无需JWT认证，通过网关传递用户信息")
    print("2. 内部接口供其他服务（如认证服务）调用")
    print("3. 支持Nacos服务注册与发现")
    print("4. 专注用户业务逻辑，认证由网关层处理")
    print("\n🔧 使用说明:")
    print("1. 确保服务器已启动 (python start.py)")
    print("2. 确保数据库已配置并运行")
    print("3. 可选：启动Nacos服务器")
    print("4. 运行此脚本: python api_test_example.py")


if __name__ == "__main__":
    main()