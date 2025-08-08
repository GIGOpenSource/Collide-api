"""
应用配置模块
从.env文件动态加载配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类 - 所有配置都从.env文件获取"""
    
    # 应用基础配置
    app_name: str
    app_version: str
    debug: bool
    service_name: str
    
    # 服务器配置
    host: str
    port: int
    
    # 数据库配置
    database_url: str
    
    # Nacos配置
    nacos_server: str
    nacos_namespace: str
    nacos_group: str
    nacos_username: Optional[str] = None
    nacos_password: Optional[str] = None
    
    # 服务注册配置
    service_ip: Optional[str] = None  # 如果不设置，会自动获取本机IP
    service_weight: float
    service_healthy: bool
    service_enabled: bool
    service_ephemeral: bool
    
    # 密码加密配置
    password_bcrypt_rounds: int
    
    # 网关传递的用户信息头部
    user_id_header: str
    username_header: str
    user_role_header: str
    
    # Redis配置
    redis_host: str
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_max_connections: int = 20
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # 日志配置
    log_level: str = "INFO"
    
    # 其他配置
    service_description: Optional[str] = None
    service_tags: Optional[str] = None
    
    model_config = {
        "env_file": [".env", "config.docker.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # 忽略.env中未定义的额外字段
    }


def load_settings() -> Settings:
    """加载配置，支持多个配置文件"""
    env_files = [".env", "config.docker.env"]
    found_files = []
    
    for env_file in env_files:
        if os.path.exists(env_file):
            found_files.append(env_file)
    
    if not found_files:
        print("⚠️  配置文件不存在")
        print("请创建以下配置文件之一：")
        for env_file in env_files:
            print(f"   - {env_file}")
        print("或者根据 config.docker.env 创建 .env 文件")
        raise FileNotFoundError("配置文件不存在")
    
    print(f"✅ 找到配置文件: {', '.join(found_files)}")
    
    try:
        return Settings()
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        print("请检查配置文件格式是否正确")
        raise


# 全局配置实例
settings = load_settings()