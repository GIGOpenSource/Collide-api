"""
存储模块API路由
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.domains.storage.async_service import StorageAsyncService
from app.domains.storage.schemas import (
    FileUploadResponse, FileInfo, PresignedUrlRequest, 
    PresignedUrlResponse, FileDeleteRequest, UrlRefreshRequest,
    BatchUrlRefreshRequest, FileUrlInfo
)
from app.common.response import SuccessResponse
from app.common.exceptions import BusinessException
from app.common.dependencies import get_current_user, UserContext

router = APIRouter(prefix="/api/v1/storage", tags=["存储管理"])


@router.post("/upload", response_model=SuccessResponse[FileUploadResponse], summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    file_type: Optional[str] = Form(None, description="文件类型分类"),
    folder: Optional[str] = Form(None, description="存储文件夹"),
    is_public: bool = Form(True, description="是否公开访问"),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    上传文件到S3存储
    
    支持的文件类型：jpg, jpeg, png, gif, webp, pdf, doc, docx, xls, xlsx, ppt, pptx, txt, zip, rar, mp4, mp3, wav
    
    - **file**: 要上传的文件（必填）
    - **file_type**: 文件类型分类，如 "image", "document", "video"（可选）
    - **folder**: 存储文件夹，如 "avatars", "documents", "videos"（可选）
    - **is_public**: 是否公开访问，默认true
    
    返回文件访问URL和元数据信息
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        service = StorageAsyncService(db)
        result = await service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            file_type=file_type,
            folder=folder,
            is_public=is_public
        )
        
        return SuccessResponse.create(data=result, message="文件上传成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件上传失败")


@router.post("/presigned-url", response_model=SuccessResponse[PresignedUrlResponse], summary="获取预签名URL")
async def get_presigned_url(
    request: PresignedUrlRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    获取预签名URL用于客户端直接上传到S3
    
    适用于大文件上传，避免通过服务器中转，提高上传效率
    
    - **file_name**: 文件名（必填）
    - **file_type**: 文件类型，如 "image", "document", "video"（必填）
    - **mime_type**: MIME类型，如 "image/jpeg", "application/pdf"（必填）
    - **folder**: 存储文件夹，如 "avatars", "documents"（可选）
    - **expires_in**: URL过期时间（秒），默认3600，范围300-86400
    
    返回上传URL和下载URL，客户端可直接使用上传URL上传文件
    """
    try:
        service = StorageAsyncService(db)
        result = await service.get_presigned_url(request)
        return SuccessResponse.create(data=result, message="获取预签名URL成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取预签名URL失败")


@router.get("/file/{object_key:path}", response_model=SuccessResponse[FileInfo], summary="获取文件信息")
async def get_file_info(
    object_key: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    获取文件信息
    
    - **object_key**: S3对象键
    """
    try:
        service = StorageAsyncService(db)
        result = await service.get_file_info(object_key)
        return SuccessResponse.create(data=result, message="获取文件信息成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取文件信息失败")


@router.get("/download/{object_key:path}", summary="下载文件（带防盗链验证）")
async def download_file(
    object_key: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    下载文件（带防盗链验证）
    
    需要包含有效的 Referer 头部，验证通过后重定向到S3预签名下载URL
    
    - **object_key**: S3对象键（路径参数）
    
    防盗链验证规则：
    - 检查请求头中的 Referer 字段
    - 验证 Referer 域名是否在允许列表中
    - 验证失败返回403错误
    
    成功时重定向到S3下载URL，失败时返回错误信息
    """
    try:
        service = StorageAsyncService(db)
        
        # 验证访问权限
        if not await service.validate_access(request, object_key):
            raise HTTPException(status_code=403, detail="访问被拒绝：防盗链验证失败")
        
        # 获取下载URL
        download_url = await service.get_download_url(object_key)
        
        # 重定向到下载URL
        return RedirectResponse(url=download_url)
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件下载失败")


@router.delete("/file", response_model=SuccessResponse[bool], summary="删除文件")
async def delete_file(
    request: FileDeleteRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    删除文件
    
    - **object_key**: S3对象键
    """
    try:
        service = StorageAsyncService(db)
        result = await service.delete_file(request.object_key)
        return SuccessResponse.create(data=result, message="文件删除成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件删除失败")


@router.get("/validate/{object_key:path}", response_model=SuccessResponse[bool], summary="验证文件访问权限")
async def validate_file_access(
    object_key: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    验证文件访问权限（防盗链检查）
    
    检查文件是否存在以及访问权限是否有效，用于客户端预检查
    
    - **object_key**: S3对象键（路径参数）
    
    验证内容：
    - 文件是否存在于S3中
    - Referer 域名是否在允许列表中
    - 返回验证结果（true/false）
    
    注意：此接口不下载文件，仅验证访问权限
    """
    try:
        service = StorageAsyncService(db)
        result = await service.validate_access(request, object_key)
        return SuccessResponse.create(data=result, message="权限验证完成")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="权限验证失败")


@router.post("/refresh-url", response_model=SuccessResponse[str], summary="刷新文件访问URL")
async def refresh_file_url(
    request: UrlRefreshRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    刷新文件访问URL
    
    用于处理URL过期问题，重新生成文件访问链接
    
    - **object_key**: S3对象键
    - **expires_in**: URL过期时间（秒），默认3600
    
    返回新的文件访问URL
    """
    try:
        service = StorageAsyncService(db)
        url = await service.refresh_file_url(request.object_key, request.expires_in)
        return SuccessResponse.create(data=url, message="URL刷新成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="URL刷新失败")


@router.post("/batch-refresh-urls", response_model=SuccessResponse[dict], summary="批量刷新文件URL")
async def batch_refresh_urls(
    request: BatchUrlRefreshRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    批量刷新文件URL
    
    一次性刷新多个文件的访问URL，提高效率
    
    - **object_keys**: S3对象键列表
    - **expires_in**: URL过期时间（秒），默认3600
    
    返回每个文件的刷新结果
    """
    try:
        service = StorageAsyncService(db)
        result = await service.batch_refresh_urls(request.object_keys, request.expires_in)
        return SuccessResponse.create(data=result, message="批量URL刷新完成")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="批量URL刷新失败")


@router.get("/url-info/{object_key:path}", response_model=SuccessResponse[FileUrlInfo], summary="获取文件URL详细信息")
async def get_file_url_info(
    object_key: str,
    expires_in: int = 3600,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    获取文件URL详细信息
    
    包含URL、过期时间、文件大小等完整信息
    
    - **object_key**: S3对象键（路径参数）
    - **expires_in**: URL过期时间（秒），默认3600
    
    返回文件的完整URL信息
    """
    try:
        service = StorageAsyncService(db)
        result = await service.get_file_url_with_expiry(object_key, expires_in)
        return SuccessResponse.create(data=result, message="获取文件URL信息成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取文件URL信息失败") 