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
    
    # 日志配置
    log_level: str = "INFO"
    
    # 其他配置
    service_description: Optional[str] = None
    service_tags: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # 忽略.env中未定义的额外字段
    }


def load_settings() -> Settings:
    """加载配置，如果.env文件不存在则给出友好提示"""
    env_file_path = ".env"
    
    if not os.path.exists(env_file_path):
        print(f"⚠️  配置文件 {env_file_path} 不存在")
        print("请根据 config.example.env 创建配置文件：")
        print("   cp config.example.env .env")
        print("然后编辑 .env 文件配置相关参数")
        raise FileNotFoundError(f"配置文件 {env_file_path} 不存在")
    
    try:
        return Settings()
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        print("请检查 .env 文件格式是否正确")
        raise


# 全局配置实例
settings = load_settings()