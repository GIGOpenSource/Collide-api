"""
存储模块异步服务层
"""
import os
import uuid
import mimetypes
from typing import Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.storage.schemas import (
    FileUploadResponse, FileInfo, PresignedUrlRequest, 
    PresignedUrlResponse, StorageConfig
)
from app.common.exceptions import BusinessException
from app.common.config import settings


class StorageAsyncService:
    """存储异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = self._load_config()
        self.s3_client = self._init_s3_client()

    def _load_config(self) -> StorageConfig:
        """加载存储配置"""
        return StorageConfig(
            bucket_name=settings.AWS_S3_BUCKET_NAME,
            region=settings.AWS_REGION,
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            allowed_domains=settings.ALLOWED_DOMAINS.split(',') if settings.ALLOWED_DOMAINS else [],
            max_file_size=settings.MAX_FILE_SIZE,
            allowed_extensions=settings.ALLOWED_EXTENSIONS.split(',') if settings.ALLOWED_EXTENSIONS else [],
            cdn_domain=settings.CDN_DOMAIN
        )

    def _init_s3_client(self):
        """初始化S3客户端"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region
            )
        except Exception as e:
            raise BusinessException(f"S3客户端初始化失败: {str(e)}")

    def _validate_file_type(self, file_name: str) -> tuple[str, str]:
        """验证文件类型"""
        # 获取文件扩展名
        _, ext = os.path.splitext(file_name.lower())
        if not ext:
            raise BusinessException("文件必须包含扩展名")
        
        # 检查是否在允许的扩展名列表中
        if self.config.allowed_extensions and ext[1:] not in self.config.allowed_extensions:
            raise BusinessException(f"不支持的文件类型: {ext}")
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        return ext[1:], mime_type

    def _generate_object_key(self, file_name: str, folder: Optional[str] = None) -> str:
        """生成S3对象键"""
        # 生成唯一文件名
        unique_id = str(uuid.uuid4())
        name, ext = os.path.splitext(file_name)
        
        # 构建路径
        if folder:
            object_key = f"{folder}/{unique_id}{ext}"
        else:
            object_key = f"uploads/{unique_id}{ext}"
        
        return object_key

    def _check_referer(self, request: Request) -> bool:
        """检查防盗链"""
        referer = request.headers.get('referer')
        if not referer:
            return False
        
        try:
            parsed_url = urlparse(referer)
            domain = parsed_url.netloc.lower()
            
            # 检查是否在允许的域名列表中
            for allowed_domain in self.config.allowed_domains:
                if allowed_domain.strip().lower() in domain:
                    return True
            
            return False
        except Exception:
            return False

    async def upload_file(self, file_content: bytes, file_name: str, 
                         file_type: Optional[str] = None, folder: Optional[str] = None,
                         is_public: bool = True) -> FileUploadResponse:
        """上传文件到S3"""
        try:
            # 验证文件类型
            ext, mime_type = self._validate_file_type(file_name)
            
            # 检查文件大小
            if len(file_content) > self.config.max_file_size:
                raise BusinessException(f"文件大小超过限制: {self.config.max_file_size} 字节")
            
            # 生成对象键
            object_key = self._generate_object_key(file_name, folder)
            
            # 上传到S3
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=mime_type,
                ACL='public-read' if is_public else 'private'
            )
            
            # 生成访问URL
            if self.config.cdn_domain:
                file_url = f"https://{self.config.cdn_domain}/{object_key}"
            else:
                file_url = f"https://{self.config.bucket_name}.s3.{self.config.region}.amazonaws.com/{object_key}"
            
            return FileUploadResponse(
                file_url=file_url,
                file_name=file_name,
                file_size=len(file_content),
                file_type=ext,
                mime_type=mime_type,
                object_key=object_key,
                expires_in=3600
            )
            
        except ClientError as e:
            raise BusinessException(f"S3上传失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"文件上传失败: {str(e)}")

    async def get_presigned_url(self, request: PresignedUrlRequest) -> PresignedUrlResponse:
        """获取预签名URL"""
        try:
            # 验证文件类型
            ext, mime_type = self._validate_file_type(request.file_name)
            
            # 生成对象键
            object_key = self._generate_object_key(request.file_name, request.folder)
            
            # 生成上传URL
            upload_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.config.bucket_name,
                    'Key': object_key,
                    'ContentType': mime_type
                },
                ExpiresIn=request.expires_in
            )
            
            # 生成下载URL
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.config.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=request.expires_in
            )
            
            return PresignedUrlResponse(
                upload_url=upload_url,
                download_url=download_url,
                object_key=object_key,
                expires_in=request.expires_in
            )
            
        except ClientError as e:
            raise BusinessException(f"生成预签名URL失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"获取预签名URL失败: {str(e)}")

    async def get_file_info(self, object_key: str) -> FileInfo:
        """获取文件信息"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=object_key
            )
            
            # 生成访问URL
            if self.config.cdn_domain:
                file_url = f"https://{self.config.cdn_domain}/{object_key}"
            else:
                file_url = f"https://{self.config.bucket_name}.s3.{self.config.region}.amazonaws.com/{object_key}"
            
            return FileInfo(
                file_url=file_url,
                file_name=os.path.basename(object_key),
                file_size=response['ContentLength'],
                file_type=os.path.splitext(object_key)[1][1:],
                mime_type=response.get('ContentType', 'application/octet-stream'),
                object_key=object_key,
                expires_in=3600,
                created_at=response.get('LastModified', datetime.now())
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise BusinessException("文件不存在")
            raise BusinessException(f"获取文件信息失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"获取文件信息失败: {str(e)}")

    async def delete_file(self, object_key: str) -> bool:
        """删除文件"""
        try:
            self.s3_client.delete_object(
                Bucket=self.config.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError as e:
            raise BusinessException(f"删除文件失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"删除文件失败: {str(e)}")

    async def validate_access(self, request: Request, object_key: str) -> bool:
        """验证文件访问权限（防盗链）"""
        # 检查防盗链
        if not self._check_referer(request):
            return False
        
        # 检查文件是否存在
        try:
            self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=object_key
            )
            return True
        except ClientError:
            return False

    async def get_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        """获取文件下载URL"""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.config.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
        except ClientError as e:
            raise BusinessException(f"生成下载URL失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"获取下载URL失败: {str(e)}")

    async def refresh_file_url(self, object_key: str, expires_in: int = 3600) -> str:
        """刷新文件访问URL"""
        try:
            # 检查文件是否存在
            self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=object_key
            )
            
            # 生成新的访问URL
            if self.config.cdn_domain:
                file_url = f"https://{self.config.cdn_domain}/{object_key}"
            else:
                file_url = f"https://{self.config.bucket_name}.s3.{self.config.region}.amazonaws.com/{object_key}"
            
            return file_url
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise BusinessException("文件不存在")
            raise BusinessException(f"刷新文件URL失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"刷新文件URL失败: {str(e)}")

    async def batch_refresh_urls(self, object_keys: List[str], expires_in: int = 3600) -> dict:
        """批量刷新文件URL"""
        result = {}
        for object_key in object_keys:
            try:
                url = await self.refresh_file_url(object_key, expires_in)
                result[object_key] = {
                    "url": url,
                    "status": "success"
                }
            except Exception as e:
                result[object_key] = {
                    "url": None,
                    "status": "error",
                    "message": str(e)
                }
        return result

    async def get_file_url_with_expiry(self, object_key: str, expires_in: int = 3600) -> dict:
        """获取文件URL和过期时间信息"""
        try:
            # 检查文件是否存在
            response = self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=object_key
            )
            
            # 生成访问URL
            if self.config.cdn_domain:
                file_url = f"https://{self.config.cdn_domain}/{object_key}"
            else:
                file_url = f"https://{self.config.bucket_name}.s3.{self.config.region}.amazonaws.com/{object_key}"
            
            # 计算过期时间
            from datetime import datetime, timedelta
            expiry_time = datetime.now() + timedelta(seconds=expires_in)
            
            return {
                "url": file_url,
                "expires_at": expiry_time.isoformat(),
                "expires_in": expires_in,
                "file_size": response['ContentLength'],
                "last_modified": response.get('LastModified', datetime.now()).isoformat()
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise BusinessException("文件不存在")
            raise BusinessException(f"获取文件URL失败: {str(e)}")
        except Exception as e:
            raise BusinessException(f"获取文件URL失败: {str(e)}") 