"""
存储模块数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import os


class FileUploadRequest(BaseModel):
    """文件上传请求"""
    file_type: str = Field(..., description="文件类型：image、video、audio、document、other")
    is_public: bool = Field(True, description="是否公开访问")
    folder_path: Optional[str] = Field(None, description="文件夹路径")

    @validator('file_type')
    def validate_file_type(cls, v):
        allowed_types = ['image', 'video', 'audio', 'document', 'other']
        if v not in allowed_types:
            raise ValueError(f'文件类型必须是以下之一: {", ".join(allowed_types)}')
        return v


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    object_key: str = Field(description="S3对象键")
    file_url: str = Field(description="文件访问URL")
    file_name: str = Field(description="文件名")
    file_size: int = Field(description="文件大小(字节)")
    mime_type: str = Field(description="MIME类型")
    expires_in: int = Field(description="URL过期时间(秒)")


class PresignedUrlRequest(BaseModel):
    """预签名URL请求"""
    file_name: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    mime_type: str = Field(..., description="MIME类型")
    folder: Optional[str] = Field(None, description="存储文件夹")
    expires_in: int = Field(3600, ge=300, le=86400, description="URL过期时间（秒）")


class PresignedUrlResponse(BaseModel):
    """预签名URL响应"""
    upload_url: str = Field(description="上传URL")
    download_url: str = Field(description="下载URL")
    object_key: str = Field(description="S3对象键")
    expires_in: int = Field(description="URL过期时间(秒)")


class FileInfo(BaseModel):
    """文件信息"""
    id: int = Field(description="文件ID")
    file_name: str = Field(description="文件名")
    original_name: str = Field(description="原始文件名")
    file_url: str = Field(description="文件访问URL")
    file_size: int = Field(description="文件大小(字节)")
    file_type: str = Field(description="文件类型")
    mime_type: str = Field(description="MIME类型")
    is_public: bool = Field(description="是否公开访问")
    access_count: int = Field(description="访问次数")
    status: str = Field(description="状态")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class FileAccessLogInfo(BaseModel):
    """文件访问日志信息"""
    id: int = Field(description="日志ID")
    file_id: int = Field(description="文件ID")
    access_user_id: Optional[int] = Field(description="访问用户ID")
    access_ip: str = Field(description="访问IP")
    user_agent: Optional[str] = Field(description="用户代理")
    referer: Optional[str] = Field(description="来源页面")
    access_time: datetime = Field(description="访问时间")
    access_result: str = Field(description="访问结果")
    block_reason: Optional[str] = Field(description="拦截原因")

    class Config:
        from_attributes = True


class FileQuery(BaseModel):
    """文件查询参数"""
    file_type: Optional[str] = Field(None, description="文件类型")
    upload_user_id: Optional[int] = Field(None, description="上传用户ID")
    is_public: Optional[bool] = Field(None, description="是否公开")
    status: Optional[str] = Field(None, description="状态")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class UploadUrlResponse(BaseModel):
    """上传URL响应"""
    upload_url: str = Field(description="预签名上传URL")
    file_key: str = Field(description="文件在S3中的键")
    expires_in: int = Field(description="URL过期时间(秒)")


class FileDeleteRequest(BaseModel):
    """文件删除请求"""
    object_key: str = Field(..., description="S3对象键")


class StorageStats(BaseModel):
    """存储统计信息"""
    total_files: int = Field(description="总文件数")
    total_size: int = Field(description="总大小(字节)")
    file_type_stats: dict = Field(description="各类型文件统计")
    recent_uploads: int = Field(description="最近24小时上传数")
    recent_access: int = Field(description="最近24小时访问数")


class StorageConfig(BaseModel):
    """存储配置"""
    bucket_name: str = Field(description="S3存储桶名称")
    region: str = Field(description="AWS区域")
    access_key_id: str = Field(description="AWS访问密钥ID")
    secret_access_key: str = Field(description="AWS秘密访问密钥")
    allowed_domains: List[str] = Field(description="允许的域名列表")
    max_file_size: int = Field(description="最大文件大小(字节)")
    allowed_extensions: List[str] = Field(description="允许的文件扩展名")
    cdn_domain: Optional[str] = Field(None, description="CDN域名")


class UrlRefreshRequest(BaseModel):
    """URL刷新请求"""
    object_key: str = Field(description="S3对象键")
    expires_in: int = Field(3600, ge=300, le=86400, description="URL过期时间（秒）")


class BatchUrlRefreshRequest(BaseModel):
    """批量URL刷新请求"""
    object_keys: List[str] = Field(description="S3对象键列表")
    expires_in: int = Field(3600, ge=300, le=86400, description="URL过期时间（秒）")


class FileUrlInfo(BaseModel):
    """文件URL信息"""
    url: str = Field(description="文件访问URL")
    expires_at: str = Field(description="过期时间")
    expires_in: int = Field(description="过期时间（秒）")
    file_size: int = Field(description="文件大小")
    last_modified: str = Field(description="最后修改时间")


class BatchUrlResult(BaseModel):
    """批量URL结果"""
    url: Optional[str] = Field(None, description="文件访问URL")
    status: str = Field(description="状态：success/error")
    message: Optional[str] = Field(None, description="错误信息") 