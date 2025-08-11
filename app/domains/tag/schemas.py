"""
标签模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer


class TagCreate(BaseModel):
    """创建标签请求"""
    name: str = Field(..., description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    tag_type: str = Field("content", description="标签类型：content、interest、system")
    category_id: Optional[int] = Field(None, description="所属分类ID")


class TagUpdate(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(None, description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    tag_type: Optional[str] = Field(None, description="标签类型")
    category_id: Optional[int] = Field(None, description="所属分类ID")
    status: Optional[str] = Field(None, description="状态：active、inactive")


class TagInfo(BaseModel):
    """标签信息"""
    id: int = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    tag_type: str = Field(..., description="标签类型")
    category_id: Optional[int] = Field(None, description="所属分类ID")
    usage_count: int = Field(..., description="使用次数")
    status: str = Field(..., description="状态")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}
    
    @field_serializer('create_time', 'update_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class UserInterestTagCreate(BaseModel):
    """创建用户兴趣标签请求"""
    tag_id: Optional[int] = Field(None, description="标签ID（与tag_name二选一）")
    tag_name: Optional[str] = Field(None, description="标签名称（与tag_id二选一，不存在则自动创建）")
    interest_score: Decimal = Field(..., ge=0, le=100, description="兴趣分数（0-100）")


class UserInterestTagInfo(BaseModel):
    """用户兴趣标签信息"""
    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    tag_id: int = Field(..., description="标签ID")
    interest_score: Decimal = Field(..., description="兴趣分数")
    status: str = Field(..., description="状态")
    create_time: datetime = Field(..., description="创建时间")
    tag_info: Optional[TagInfo] = Field(None, description="标签信息")

    model_config = {"from_attributes": True}
    
    @field_serializer('create_time')
    def serialize_datetime(self, dt: datetime) -> str:
        """序列化时间字段为指定格式"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class ContentTagCreate(BaseModel):
    """创建内容标签关联请求"""
    content_id: int = Field(..., description="内容ID")
    tag_ids: Optional[List[int]] = Field(None, description="标签ID列表（与tag_names二选一）")
    tag_names: Optional[List[str]] = Field(None, description="标签名称列表（与tag_ids二选一，不存在则自动创建）")


class TagQuery(BaseModel):
    """标签查询参数"""
    tag_type: Optional[str] = Field(None, description="标签类型")
    category_id: Optional[int] = Field(None, description="分类ID")
    status: Optional[str] = Field(None, description="状态")
    keyword: Optional[str] = Field(None, description="关键词搜索") 