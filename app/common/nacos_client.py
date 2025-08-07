"""
Nacos服务注册与发现客户端
"""
import nacos
import socket
import logging
from typing import Optional
from app.common.config import settings

logger = logging.getLogger(__name__)


class NacosClient:
    """Nacos客户端管理类"""
    
    def __init__(self):
        self.client: Optional[nacos.NacosClient] = None
        self.service_ip = settings.service_ip or self._get_local_ip()
        self.service_port = settings.port
        self.service_name = settings.service_name
        
    def _get_local_ip(self) -> str:
        """获取本机IP地址"""
        try:
            # 创建一个UDP socket连接，获取本机IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def init_client(self) -> bool:
        """初始化Nacos客户端"""
        try:
            # Nacos客户端配置
            client_config = {
                "server_addresses": settings.nacos_server,
                "namespace": settings.nacos_namespace,
            }
            
            # 如果配置了用户名密码，添加认证信息
            if settings.nacos_username and settings.nacos_password:
                client_config.update({
                    "username": settings.nacos_username,
                    "password": settings.nacos_password,
                })
            
            self.client = nacos.NacosClient(**client_config)
            logger.info(f"Nacos客户端初始化成功，服务器地址: {settings.nacos_server}")
            return True
            
        except Exception as e:
            logger.error(f"Nacos客户端初始化失败: {e}")
            return False
    
    def register_service(self) -> bool:
        """注册服务到Nacos"""
        if not self.client:
            logger.error("Nacos客户端未初始化")
            return False
        
        try:
            # 注册服务
            self.client.add_naming_instance(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name="DEFAULT",
                weight=settings.service_weight,
                metadata={
                    "version": settings.app_version,
                    "service_name": settings.app_name,
                    "environment": "dev" if settings.debug else "prod"
                },
                enable=settings.service_enabled,
                healthy=settings.service_healthy,
                ephemeral=settings.service_ephemeral,
                group_name=settings.nacos_group
            )
            
            logger.info(f"服务注册成功: {self.service_name} ({self.service_ip}:{self.service_port})")
            return True
            
        except Exception as e:
            logger.error(f"服务注册失败: {e}")
            return False
    
    def deregister_service(self) -> bool:
        """从Nacos注销服务"""
        if not self.client:
            return True
        
        try:
            self.client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name="DEFAULT",
                group_name=settings.nacos_group
            )
            
            logger.info(f"服务注销成功: {self.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"服务注销失败: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
        """发送心跳（Nacos SDK会自动处理心跳，这里作为手动触发接口）"""
        if not self.client:
            return False
        
        try:
            # 获取服务实例信息来验证服务是否正常
            instances = self.client.list_naming_instance(
                service_name=self.service_name,
                group_name=settings.nacos_group
            )
            
            # 检查当前实例是否在服务列表中
            current_instance = None
            for instance in instances.get("hosts", []):
                if (instance.get("ip") == self.service_ip and 
                    instance.get("port") == self.service_port):
                    current_instance = instance
                    break
            
            if current_instance and current_instance.get("healthy"):
                logger.debug(f"服务健康检查通过: {self.service_name}")
                return True
            else:
                logger.warning(f"服务健康检查失败: {self.service_name}")
                return False
                
        except Exception as e:
            logger.error(f"心跳检查失败: {e}")
            return False
    
    def get_service_instances(self, service_name: str) -> list:
        """获取指定服务的实例列表"""
        if not self.client:
            return []
        
        try:
            instances = self.client.list_naming_instance(
                service_name=service_name,
                group_name=settings.nacos_group,
                healthy_only=True
            )
            return instances.get("hosts", [])
            
        except Exception as e:
            logger.error(f"获取服务实例失败: {e}")
            return []


# 全局Nacos客户端实例
nacos_client = NacosClient()