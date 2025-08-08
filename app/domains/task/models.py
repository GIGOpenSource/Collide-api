"""
任务模块数据库模型
与 sql/task-simple.sql 保持一致
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, Boolean, SmallInteger, Date, JSON
from sqlalchemy.sql import func

from app.database.connection import Base


class TaskTemplate(Base):
    """任务模板表"""
    __tablename__ = "t_task_template"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务模板ID")
    task_name = Column(String(60), nullable=False, comment="任务名称")
    task_desc = Column(String(200), nullable=False, comment="任务描述")
    task_type = Column(SmallInteger, nullable=False, comment="任务类型：1-daily, 2-weekly, 3-monthly, 4-achievement")
    task_category = Column(SmallInteger, nullable=False, comment="任务分类：1-login, 2-content, 3-social, 4-consume, 5-invite")
    task_action = Column(SmallInteger, nullable=False, comment="任务动作：1-login, 2-publish_content, 3-like, 4-comment, 5-share, 6-purchase, 7-invite_user")
    target_count = Column(Integer, nullable=False, default=1, comment="目标完成次数")
    sort_order = Column(SmallInteger, nullable=False, default=0, comment="排序值")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    start_date = Column(Date, comment="任务开始日期")
    end_date = Column(Date, comment="任务结束日期")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class TaskReward(Base):
    """任务奖励表"""
    __tablename__ = "t_task_reward"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="奖励ID")
    task_id = Column(BigInteger, nullable=False, comment="任务模板ID")
    reward_type = Column(SmallInteger, nullable=False, comment="奖励类型：1-coin, 2-item, 3-vip, 4-experience, 5-badge")
    reward_name = Column(String(60), nullable=False, comment="奖励名称")
    reward_desc = Column(String(200), comment="奖励描述")
    reward_amount = Column(Integer, nullable=False, default=1, comment="奖励数量")
    reward_data = Column(JSON, comment="奖励扩展数据（商品信息等）")
    is_main_reward = Column(Boolean, nullable=False, default=True, comment="是否主要奖励")
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class UserTaskRecord(Base):
    """用户任务记录表"""
    __tablename__ = "t_user_task_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    task_id = Column(BigInteger, nullable=False, comment="任务模板ID")
    task_date = Column(Date, nullable=False, comment="任务日期（用于每日任务）")
    
    task_name = Column(String(60), nullable=False, comment="任务名称（冗余）")
    task_type = Column(SmallInteger, nullable=False, comment="任务类型（冗余）")
    task_category = Column(SmallInteger, nullable=False, comment="任务分类（冗余）")
    target_count = Column(Integer, nullable=False, comment="目标完成次数（冗余）")
    
    current_count = Column(Integer, nullable=False, default=0, comment="当前完成次数")
    is_completed = Column(Boolean, nullable=False, default=False, comment="是否已完成")
    is_rewarded = Column(Boolean, nullable=False, default=False, comment="是否已领取奖励")
    complete_time = Column(DateTime, comment="完成时间")
    reward_time = Column(DateTime, comment="奖励领取时间")
    
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")


class UserRewardRecord(Base):
    """用户奖励记录表"""
    __tablename__ = "t_user_reward_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="奖励记录ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    task_record_id = Column(BigInteger, nullable=False, comment="任务记录ID")
    reward_source = Column(SmallInteger, nullable=False, default=1, comment="奖励来源：1-task, 2-event, 3-system, 4-admin")
    
    reward_type = Column(SmallInteger, nullable=False, comment="奖励类型：1-coin, 2-item, 3-vip, 4-experience, 5-badge")
    reward_name = Column(String(60), nullable=False, comment="奖励名称")
    reward_amount = Column(Integer, nullable=False, comment="奖励数量")
    reward_data = Column(JSON, comment="奖励扩展数据")
    
    status = Column(SmallInteger, nullable=False, default=1, comment="状态：1-pending, 2-success, 3-failed, 4-expired")
    grant_time = Column(DateTime, comment="发放时间")
    expire_time = Column(DateTime, comment="过期时间")
    
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间") 