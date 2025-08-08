"""
广告模块 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AdCreate(BaseModel):
    """创建广告请求"""
    ad_name: str = Field(..., description="广告名称")
    ad_title: str = Field(..., description="广告标题")
    ad_description: Optional[str] = Field(None, description="广告描述")
    ad_type: str = Field(..., description="广告类型：banner、sidebar、popup、feed")
    image_url: str = Field(..., description="广告图片URL")
    click_url: str = Field(..., description="点击跳转链接")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    target_type: str = Field("_blank", description="链接打开方式：_blank、_self")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序权重")


class AdUpdate(BaseModel):
    """更新广告请求"""
    ad_name: Optional[str] = Field(None, description="广告名称")
    ad_title: Optional[str] = Field(None, description="广告标题")
    ad_description: Optional[str] = Field(None, description="广告描述")
    ad_type: Optional[str] = Field(None, description="广告类型")
    image_url: Optional[str] = Field(None, description="广告图片URL")
    click_url: Optional[str] = Field(None, description="点击跳转链接")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    target_type: Optional[str] = Field(None, description="链接打开方式")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序权重")


class AdInfo(BaseModel):
    """广告信息"""
    id: int = Field(..., description="广告ID")
    ad_name: str = Field(..., description="广告名称")
    ad_title: str = Field(..., description="广告标题")
    ad_description: Optional[str] = Field(None, description="广告描述")
    ad_type: str = Field(..., description="广告类型")
    image_url: str = Field(..., description="广告图片URL")
    click_url: str = Field(..., description="点击跳转链接")
    alt_text: Optional[str] = Field(None, description="图片替代文本")
    target_type: str = Field(..., description="链接打开方式")
    is_active: bool = Field(..., description="是否启用")
    sort_order: int = Field(..., description="排序权重")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class AdQuery(BaseModel):
    """广告查询参数"""
    ad_type: Optional[str] = Field(None, description="广告类型")
    is_active: Optional[bool] = Field(None, description="是否启用")
    keyword: Optional[str] = Field(None, description="关键词搜索") 