"""
全局异常处理器
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.common.exceptions import BusinessException
from app.common.response import ErrorResponse

logger = logging.getLogger(__name__)


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """业务异常处理器"""
    logger.warning(f"业务异常: {exc.message} - {request.url}")
    
    error_response = ErrorResponse.create(code=exc.code, message=exc.message)
    return JSONResponse(
        status_code=400,
        content=error_response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.detail} - {request.url}")
    
    error_response = ErrorResponse.create(code=exc.status_code, message=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """数据库异常处理器"""
    logger.error(f"数据库异常: {str(exc)} - {request.url}")
    
    error_response = ErrorResponse.create(code=500, message="数据库操作失败")
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"系统异常: {str(exc)} - {request.url}", exc_info=True)
    
    error_response = ErrorResponse.create(code=500, message="系统内部错误")
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )