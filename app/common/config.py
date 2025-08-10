"""
应用配置模块
仅使用 .env 文件动态加载配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类 - 所有配置都从 .env 文件获取"""
    
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
    # 对外回调地址根域名（可选），例如：https://api.example.com
    payment_public_base_url: Optional[str] = None
    # 上游支付网关默认基础地址（可选），例如：https://pay.example.com
    default_payment_api_base_url: Optional[str] = None
    
    # AWS S3 存储配置
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_s3_bucket_name: str
    
    # 存储安全配置
    allowed_domains: Optional[str] = None  # 允许的域名列表，逗号分隔
    max_file_size: int = 10485760  # 最大文件大小，默认10MB
    allowed_extensions: Optional[str] = None  # 允许的文件扩展名，逗号分隔
    
    # CDN配置（可选）
    cdn_domain: Optional[str] = None  # CDN域名
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # 忽略.env中未定义的额外字段
    }


def load_settings() -> Settings:
    """仅从 .env 加载配置"""
    env_file_path = ".env"
    
    if not os.path.exists(env_file_path):
        print("⚠️  .env 配置文件不存在")
        print("请在项目根目录创建 .env 文件，可以参考 config.docker.env")
        raise FileNotFoundError(".env 配置文件不存在")
    
    print(f"✅ 使用配置文件: {env_file_path}")
    
    try:
        return Settings()
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        print("请检查 .env 文件格式是否正确")
        raise


# 全局配置实例
settings = load_settings()