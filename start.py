"""
Collide API 启动脚本
简化启动过程
"""
import uvicorn
from app.common.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=8080,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
        access_log=settings.debug
    )