"""
任务模块 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class TaskTemplateCreate(BaseModel):
    """创建任务模板请求"""
    task_name: str = Field(..., description="任务名称")
    task_desc: str = Field(..., description="任务描述")
    task_type: int = Field(..., description="任务类型：1-daily, 2-weekly, 3-monthly, 4-achievement")
    task_category: int = Field(..., description="任务分类：1-login, 2-content, 3-social, 4-consume, 5-invite")
    task_action: int = Field(..., description="任务动作：1-login, 2-publish_content, 3-like, 4-comment, 5-share, 6-purchase, 7-invite_user")
    target_count: int = Field(1, description="目标完成次数")
    sort_order: int = Field(0, description="排序值")
    is_active: bool = Field(True, description="是否启用")
    start_date: Optional[date] = Field(None, description="任务开始日期")
    end_date: Optional[date] = Field(None, description="任务结束日期")


class TaskTemplateUpdate(BaseModel):
    """更新任务模板请求"""
    task_name: Optional[str] = Field(None, description="任务名称")
    task_desc: Optional[str] = Field(None, description="任务描述")
    task_type: Optional[int] = Field(None, description="任务类型")
    task_category: Optional[int] = Field(None, description="任务分类")
    task_action: Optional[int] = Field(None, description="任务动作")
    target_count: Optional[int] = Field(None, description="目标完成次数")
    sort_order: Optional[int] = Field(None, description="排序值")
    is_active: Optional[bool] = Field(None, description="是否启用")
    start_date: Optional[date] = Field(None, description="任务开始日期")
    end_date: Optional[date] = Field(None, description="任务结束日期")


class TaskTemplateInfo(BaseModel):
    """任务模板信息"""
    id: int = Field(..., description="任务模板ID")
    task_name: str = Field(..., description="任务名称")
    task_desc: str = Field(..., description="任务描述")
    task_type: int = Field(..., description="任务类型")
    task_category: int = Field(..., description="任务分类")
    task_action: int = Field(..., description="任务动作")
    target_count: int = Field(..., description="目标完成次数")
    sort_order: int = Field(..., description="排序值")
    is_active: bool = Field(..., description="是否启用")
    start_date: Optional[date] = Field(None, description="任务开始日期")
    end_date: Optional[date] = Field(None, description="任务结束日期")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class TaskRewardCreate(BaseModel):
    """创建任务奖励请求"""
    task_id: int = Field(..., description="任务模板ID")
    reward_type: int = Field(..., description="奖励类型：1-coin, 2-item, 3-vip, 4-experience, 5-badge")
    reward_name: str = Field(..., description="奖励名称")
    reward_desc: Optional[str] = Field(None, description="奖励描述")
    reward_amount: int = Field(1, description="奖励数量")
    reward_data: Optional[Dict[str, Any]] = Field(None, description="奖励扩展数据")
    is_main_reward: bool = Field(True, description="是否主要奖励")


class TaskRewardInfo(BaseModel):
    """任务奖励信息"""
    id: int = Field(..., description="奖励ID")
    task_id: int = Field(..., description="任务模板ID")
    reward_type: int = Field(..., description="奖励类型")
    reward_name: str = Field(..., description="奖励名称")
    reward_desc: Optional[str] = Field(None, description="奖励描述")
    reward_amount: int = Field(..., description="奖励数量")
    reward_data: Optional[Dict[str, Any]] = Field(None, description="奖励扩展数据")
    is_main_reward: bool = Field(..., description="是否主要奖励")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class UserTaskRecordInfo(BaseModel):
    """用户任务记录信息"""
    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    task_id: int = Field(..., description="任务模板ID")
    task_date: date = Field(..., description="任务日期")
    task_name: str = Field(..., description="任务名称")
    task_type: int = Field(..., description="任务类型")
    task_category: int = Field(..., description="任务分类")
    target_count: int = Field(..., description="目标完成次数")
    current_count: int = Field(..., description="当前完成次数")
    is_completed: bool = Field(..., description="是否已完成")
    is_rewarded: bool = Field(..., description="是否已领取奖励")
    complete_time: Optional[datetime] = Field(None, description="完成时间")
    reward_time: Optional[datetime] = Field(None, description="奖励领取时间")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class UserRewardRecordInfo(BaseModel):
    """用户奖励记录信息"""
    id: int = Field(..., description="奖励记录ID")
    user_id: int = Field(..., description="用户ID")
    task_record_id: int = Field(..., description="任务记录ID")
    reward_source: int = Field(..., description="奖励来源")
    reward_type: int = Field(..., description="奖励类型")
    reward_name: str = Field(..., description="奖励名称")
    reward_amount: int = Field(..., description="奖励数量")
    reward_data: Optional[Dict[str, Any]] = Field(None, description="奖励扩展数据")
    status: int = Field(..., description="状态")
    grant_time: Optional[datetime] = Field(None, description="发放时间")
    expire_time: Optional[datetime] = Field(None, description="过期时间")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class TaskProgressUpdate(BaseModel):
    """任务进度更新请求"""
    task_action: int = Field(..., description="任务动作")
    count: int = Field(1, description="完成次数")


class TaskQuery(BaseModel):
    """任务查询参数"""
    task_type: Optional[int] = Field(None, description="任务类型")
    task_category: Optional[int] = Field(None, description="任务分类")
    is_active: Optional[bool] = Field(None, description="是否启用")
    task_date: Optional[date] = Field(None, description="任务日期")
    is_completed: Optional[bool] = Field(None, description="是否已完成")
    is_rewarded: Optional[bool] = Field(None, description="是否已领取奖励") 