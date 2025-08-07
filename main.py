"""
Collide User Service 主应用入口
微服务架构，支持Nacos服务注册与发现
"""
import logging
import signal
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.common.config import settings
from app.common.exceptions import BusinessException
from app.common.exception_handlers import (
    business_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from app.common.nacos_client import nacos_client
from app.common.redis_client import init_redis, close_redis
from app.database.connection import engine, Base
from app.domains.users.async_router import router as users_router
from app.domains.content.async_router import router as content_router

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"正在启动 {settings.app_name}...")
    
    # 创建数据库表（如果不存在）
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表检查完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    # 初始化Redis连接
    try:
        await init_redis()
        logger.info("Redis连接初始化成功")
    except Exception as e:
        logger.warning(f"Redis初始化失败: {e}，缓存功能将不可用")
    
    # 初始化并注册到Nacos
    try:
        if nacos_client.init_client():
            if nacos_client.register_service():
                logger.info("Nacos服务注册成功")
            else:
                logger.warning("Nacos服务注册失败，但服务仍将继续运行")
        else:
            logger.warning("Nacos客户端初始化失败，服务将在无服务发现模式下运行")
    except Exception as e:
        logger.warning(f"Nacos配置失败: {e}，服务将在无服务发现模式下运行")
    
    yield
    
    # 关闭时执行
    logger.info(f"正在关闭 {settings.app_name}...")
    
    # 关闭Redis连接
    try:
        await close_redis()
        logger.info("Redis连接已关闭")
    except Exception as e:
        logger.error(f"关闭Redis连接失败: {e}")
    
    # 从Nacos注销服务
    try:
        nacos_client.deregister_service()
        logger.info("Nacos服务注销完成")
    except Exception as e:
        logger.warning(f"Nacos服务注销失败: {e}")
    
    # 关闭数据库连接
    engine.dispose()


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在优雅关闭服务...")
    try:
        nacos_client.deregister_service()
    except:
        pass
    sys.exit(0)


# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Collide 业务服务 - 用户与内容管理微服务架构",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(users_router)
app.include_router(content_router)

# 健康检查接口
@app.get("/health", tags=["系统"], summary="健康检查")
async def health_check():
    """
    系统健康检查接口
    用于Nacos健康检查和负载均衡器检查
    """
    # 检查数据库连接
    try:
        from app.database.connection import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # 检查Nacos连接
    nacos_status = "healthy" if nacos_client.send_heartbeat() else "unhealthy"
    
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.app_version,
        "checks": {
            "database": db_status,
            "nacos": nacos_status
        },
        "timestamp": datetime.now().isoformat()
    }


# 根路径
@app.get("/", tags=["系统"], summary="服务信息")
async def root():
    """服务根路径信息"""
    return {
        "service": settings.app_name,
        "service_name": settings.service_name,
        "version": settings.app_version,
        "description": "Collide 业务微服务 - 用户与内容管理",
        "docs": "/docs" if settings.debug else "文档已关闭",
        "health": "/health"
    }


# Nacos心跳检查接口
@app.get("/actuator/health", tags=["系统"], summary="Spring Boot风格健康检查")
async def actuator_health():
    """
    Spring Boot风格的健康检查接口
    与Spring Cloud生态兼容
    """
    return await health_check()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )