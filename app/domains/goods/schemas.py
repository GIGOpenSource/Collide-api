"""
商品模块 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class GoodsCreate(BaseModel):
    """创建商品请求"""
    name: str = Field(..., description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    category_id: int = Field(..., description="分类ID")
    goods_type: str = Field(..., description="商品类型：coin-金币、goods-商品、subscription-订阅、content-内容")
    price: Decimal = Field(0.00, description="现金价格")
    original_price: Optional[Decimal] = Field(None, description="原价")
    coin_price: int = Field(0, description="金币价格")
    coin_amount: Optional[int] = Field(None, description="金币数量")
    
    content_id: Optional[int] = Field(None, description="关联内容ID")
    subscription_duration: Optional[int] = Field(None, description="订阅时长（天数）")
    subscription_type: Optional[str] = Field(None, description="订阅类型")
    
    stock: int = Field(-1, description="库存数量（-1表示无限库存）")
    cover_url: Optional[str] = Field(None, description="商品封面图")
    images: Optional[str] = Field(None, description="商品图片，JSON数组格式")
    
    seller_id: int = Field(..., description="商家ID")
    seller_name: str = Field(..., description="商家名称")


class GoodsUpdate(BaseModel):
    """更新商品请求"""
    name: Optional[str] = Field(None, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    goods_type: Optional[str] = Field(None, description="商品类型")
    price: Optional[Decimal] = Field(None, description="现金价格")
    original_price: Optional[Decimal] = Field(None, description="原价")
    coin_price: Optional[int] = Field(None, description="金币价格")
    coin_amount: Optional[int] = Field(None, description="金币数量")
    
    content_id: Optional[int] = Field(None, description="关联内容ID")
    subscription_duration: Optional[int] = Field(None, description="订阅时长（天数）")
    subscription_type: Optional[str] = Field(None, description="订阅类型")
    
    stock: Optional[int] = Field(None, description="库存数量")
    cover_url: Optional[str] = Field(None, description="商品封面图")
    images: Optional[str] = Field(None, description="商品图片")
    
    seller_name: Optional[str] = Field(None, description="商家名称")
    status: Optional[str] = Field(None, description="状态")


class GoodsInfo(BaseModel):
    """商品信息"""
    id: int = Field(..., description="商品ID")
    name: str = Field(..., description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    category_id: int = Field(..., description="分类ID")
    category_name: Optional[str] = Field(None, description="分类名称")
    goods_type: str = Field(..., description="商品类型")
    price: Decimal = Field(..., description="现金价格")
    original_price: Optional[Decimal] = Field(None, description="原价")
    coin_price: int = Field(..., description="金币价格")
    coin_amount: Optional[int] = Field(None, description="金币数量")
    
    content_id: Optional[int] = Field(None, description="关联内容ID")
    content_title: Optional[str] = Field(None, description="内容标题")
    subscription_duration: Optional[int] = Field(None, description="订阅时长")
    subscription_type: Optional[str] = Field(None, description="订阅类型")
    
    stock: int = Field(..., description="库存数量")
    cover_url: Optional[str] = Field(None, description="商品封面图")
    images: Optional[str] = Field(None, description="商品图片")
    
    seller_id: int = Field(..., description="商家ID")
    seller_name: str = Field(..., description="商家名称")
    status: str = Field(..., description="状态")
    sales_count: int = Field(..., description="销量")
    view_count: int = Field(..., description="查看数")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class GoodsQuery(BaseModel):
    """商品查询参数"""
    category_id: Optional[int] = Field(None, description="分类ID")
    goods_type: Optional[str] = Field(None, description="商品类型")
    seller_id: Optional[int] = Field(None, description="商家ID")
    status: Optional[str] = Field(None, description="状态")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    min_price: Optional[Decimal] = Field(None, description="最低价格")
    max_price: Optional[Decimal] = Field(None, description="最高价格")
    min_coin_price: Optional[int] = Field(None, description="最低金币价格")
    max_coin_price: Optional[int] = Field(None, description="最高金币价格") 