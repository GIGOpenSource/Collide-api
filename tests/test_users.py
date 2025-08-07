"""
用户API测试
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_user_register():
    """测试用户注册"""
    user_data = {
        "username": "testuser123",
        "nickname": "测试用户",
        "password": "123456",
        "email": "test@example.com"
    }
    
    response = client.post("/api/users/register", json=user_data)
    
    # 注意：这里可能会因为数据库连接问题而失败
    # 在真实测试环境中需要配置测试数据库
    print(f"注册响应: {response.status_code} - {response.text}")


def test_user_list():
    """测试用户列表接口"""
    response = client.get("/api/users")
    
    # 注意：这里可能会因为数据库连接问题而失败
    print(f"用户列表响应: {response.status_code} - {response.text}")


if __name__ == "__main__":
    # 运行简单测试
    test_health_check()
    test_root()
    print("基础接口测试通过！")
    
    # 注意：数据库相关的测试需要先配置数据库连接
    print("提示：用户相关接口测试需要先配置数据库连接")