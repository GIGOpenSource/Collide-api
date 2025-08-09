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
from fastapi.openapi.utils import get_openapi
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
from app.domains.category.async_router import router as category_router
from app.domains.social.async_router import router as social_router
from app.domains.comment.async_router import router as comment_router
from app.domains.like.async_router import router as like_router
from app.domains.follow.async_router import router as follow_router
from app.domains.favorite.async_router import router as favorite_router
from app.domains.search.async_router import router as search_router
from app.domains.tag.async_router import router as tag_router
from app.domains.ads.async_router import router as ads_router
from app.domains.message.async_router import router as message_router
from app.domains.task.async_router import router as task_router
from app.domains.goods.async_router import router as goods_router
from app.domains.order.async_router import router as order_router
from app.domains.payment.async_router import router as payment_router
from app.domains.category.async_router import router as category_router

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

# OpenAPI Tags 元数据（中文说明）
tags_metadata = [
    {"name": "系统", "description": "系统级接口：健康检查、服务信息等"},
    {"name": "用户管理", "description": "用户信息、认证辅助、钱包与黑名单等用户相关接口"},
    {"name": "内容管理", "description": "内容的创建、更新、发布、查询与统计"},
    {"name": "分类管理", "description": "分类的增删改查与筛选"},
    {"name": "社交动态", "description": "动态流、互动相关接口"},
    {"name": "评论管理", "description": "评论的增删改查、树状结构与回复"},
    {"name": "点赞/关注/收藏", "description": "常见互动行为"},
    {"name": "搜索", "description": "关键词搜索与热搜/历史"},
    {"name": "广告管理", "description": "广告的管理与投放"},
    {"name": "消息中心", "description": "消息与通知相关"},
    {"name": "任务系统", "description": "任务与调度相关"},
    {"name": "商品管理", "description": "商品、价格、热销等"},
]

# 创建FastAPI应用实例（中文文档说明包含分页规范）
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Collide 业务服务 - 用户与内容管理微服务架构\n\n"
        "文档与字段说明：\n"
        "- 所有接口均返回统一响应结构，错误时包含明确的 code 与 message。\n"
        "- 分页参数（推荐）：curretPage 与 pageSize。\n"
        "  - 示例：?curretPage=2&pageSize=20\n"
        "  - 默认：curretPage=1，pageSize=20；pageSize 最大为 100。\n"
        "- 兼容参数（不推荐，仅为兼容旧前端）：currentPage/page/pageNum/current 或 offset + limit。\n"
        "- 分页响应字段：datas、total、currentPage、pageSize、totalPage。\n"
    ),
    terms_of_service="https://example.com/terms",
    contact={
        "name": "Collide 团队",
        "url": "https://example.com",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    servers=[
        {"url": "/", "description": "默认环境"},
    ],
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


def custom_openapi():
    """自定义 OpenAPI，增强中文文档信息与展示细节"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # 附加中文友好的元信息
    info = openapi_schema.get("info", {})
    info.setdefault("x-logo", {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"})
    info.setdefault("x-summary", "本服务提供用户、内容、标签、消息、任务、商品等领域接口，支持统一响应与分页规范。")
    openapi_schema["info"] = info

    # 为常见响应模型补充示例（如果存在）
    components = openapi_schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    # 可能的模型名称（根据 Pydantic 泛型展开的可能性，尽力匹配基础模型名）
    if "BaseResponse" in schemas and "properties" in schemas["BaseResponse"]:
        schemas["BaseResponse"].setdefault("example", {
            "code": 200,
            "message": "操作成功",
            "success": True,
            "data": None
        })

    if "ErrorResponse" in schemas and "properties" in schemas["ErrorResponse"]:
        schemas["ErrorResponse"].setdefault("example", {
            "code": 400,
            "message": "参数错误",
            "success": False,
            "data": None
        })

    if "PaginationData" in schemas and "properties" in schemas["PaginationData"]:
        schemas["PaginationData"].setdefault("example", {
            "datas": [
                {"id": 1, "name": "示例"}
            ],
            "total": 100,
            "currentPage": 1,
            "pageSize": 20,
            "totalPage": 5
        })

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# 挂载自定义 OpenAPI 生成函数
app.openapi = custom_openapi  # type: ignore

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
app.include_router(category_router)
app.include_router(social_router)
app.include_router(comment_router)
app.include_router(like_router)
app.include_router(follow_router)
app.include_router(favorite_router)
app.include_router(search_router)
app.include_router(tag_router)
app.include_router(ads_router)
app.include_router(message_router)
app.include_router(task_router)
app.include_router(goods_router)
app.include_router(order_router)
app.include_router(payment_router)

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