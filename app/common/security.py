"""
安全相关工具类
微服务环境下只处理密码加密，认证由网关层Sa-Token处理
"""
from passlib.context import CryptContext
from app.common.config import settings


class SecurityManager:
    """安全管理器（微服务版本）"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """密码加密"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)


# 全局安全管理器实例
security_manager = SecurityManager()