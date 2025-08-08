"""
分类模块 Pydantic 数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., max_length=100, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: int = Field(default=0, ge=0, description="父分类ID，0表示顶级分类")
    icon_url: Optional[str] = Field(None, max_length=500, description="分类图标URL")
    sort: int = Field(default=0, ge=0, description="排序值（越大越靠前）")
    status: str = Field(default="active", description="状态：active、inactive")


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    pass


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, ge=0, description="父分类ID")
    icon_url: Optional[str] = Field(None, max_length=500, description="分类图标URL")
    sort: Optional[int] = Field(None, ge=0, description="排序值")
    status: Optional[str] = Field(None, description="状态")


class CategoryInfo(CategoryBase):
    """分类信息响应"""
    id: int = Field(..., description="分类ID")
    content_count: int = Field(default=0, description="内容数量")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class CategoryQuery(BaseModel):
    """分类列表查询参数"""
    keyword: Optional[str] = Field(None, description="关键词（按名称模糊搜索）")
    parent_id: Optional[int] = Field(None, ge=0, description="父分类ID过滤")
    status: Optional[str] = Field(None, description="状态过滤")

