"""
搜索模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """搜索请求"""
    keyword: str = Field(..., description="搜索关键词")
    search_type: str = Field("content", description="搜索类型：content、goods、user")


class SearchHistoryInfo(BaseModel):
    """搜索历史信息"""
    id: int = Field(..., description="搜索历史ID")
    user_id: int = Field(..., description="用户ID")
    keyword: str = Field(..., description="搜索关键词")
    search_type: str = Field(..., description="搜索类型")
    result_count: int = Field(..., description="搜索结果数量")
    create_time: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


class HotSearchInfo(BaseModel):
    """热门搜索信息"""
    id: int = Field(..., description="热搜ID")
    keyword: str = Field(..., description="搜索关键词")
    search_count: int = Field(..., description="搜索次数")
    trend_score: float = Field(..., description="趋势分数")
    status: str = Field(..., description="状态：active、inactive")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    """搜索结果"""
    keyword: str = Field(..., description="搜索关键词")
    search_type: str = Field(..., description="搜索类型")
    result_count: int = Field(..., description="结果数量")
    results: List[dict] = Field(..., description="搜索结果列表") 