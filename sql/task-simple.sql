-- ==========================================
-- Collide 每日任务系统 - 优化版
-- 用户每日任务功能，支持金币和商品奖励
-- 设计原则：简洁、高效、易扩展
-- 基于用户系统优化经验进行重构
-- ==========================================

USE collide;

-- ==========================================
-- 任务类型和状态常量说明
-- ==========================================

-- 任务类型常量：1-daily, 2-weekly, 3-monthly, 4-achievement
-- 任务分类常量：1-login, 2-content, 3-social, 4-consume, 5-invite
-- 任务动作常量：1-login, 2-publish_content, 3-like, 4-comment, 5-share, 6-purchase, 7-invite_user
-- 奖励类型常量：1-coin, 2-item, 3-vip, 4-experience, 5-badge
-- 奖励来源常量：1-task, 2-event, 3-system, 4-admin
-- 奖励状态常量：1-pending, 2-success, 3-failed, 4-expired

-- ==========================================
-- 任务定义表
-- ==========================================

-- 任务模板表（系统预定义的任务类型）
DROP TABLE IF EXISTS `t_task_template`;
CREATE TABLE `t_task_template` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '任务模板ID',
    `task_name`       VARCHAR(60)  NOT NULL                COMMENT '任务名称',
    `task_desc`       VARCHAR(200) NOT NULL                COMMENT '任务描述',
    `task_type`       TINYINT      NOT NULL                COMMENT '任务类型：1-daily, 2-weekly, 3-monthly, 4-achievement',
    `task_category`   TINYINT      NOT NULL                COMMENT '任务分类：1-login, 2-content, 3-social, 4-consume, 5-invite',
    `task_action`     TINYINT      NOT NULL                COMMENT '任务动作：1-login, 2-publish_content, 3-like, 4-comment, 5-share, 6-purchase, 7-invite_user',
    `target_count`    INT          NOT NULL DEFAULT 1      COMMENT '目标完成次数',
    `sort_order`      SMALLINT     NOT NULL DEFAULT 0      COMMENT '排序值',
    `is_active`       TINYINT(1)   NOT NULL DEFAULT 1      COMMENT '是否启用',
    `start_date`      DATE         NULL                    COMMENT '任务开始日期',
    `end_date`        DATE         NULL                    COMMENT '任务结束日期',
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_task_type` (`task_type`),
    KEY `idx_task_category` (`task_category`),
    KEY `idx_task_action` (`task_action`) USING HASH,
    KEY `idx_active_sort` (`is_active`, `sort_order`),
    KEY `idx_date_range` (`start_date`, `end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务模板表';

-- ==========================================
-- 任务奖励配置表
-- ==========================================

-- 任务奖励表
DROP TABLE IF EXISTS `t_task_reward`;
CREATE TABLE `t_task_reward` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '奖励ID',
    `task_id`       BIGINT       NOT NULL                COMMENT '任务模板ID',
    `reward_type`   TINYINT      NOT NULL                COMMENT '奖励类型：1-coin, 2-item, 3-vip, 4-experience, 5-badge',
    `reward_name`   VARCHAR(60)  NOT NULL                COMMENT '奖励名称',
    `reward_desc`   VARCHAR(200)                         COMMENT '奖励描述',
    `reward_amount` INT          NOT NULL DEFAULT 1      COMMENT '奖励数量',
    `reward_data`   JSON                                 COMMENT '奖励扩展数据（商品信息等）',
    `is_main_reward` TINYINT(1)  NOT NULL DEFAULT 1      COMMENT '是否主要奖励',
    `create_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_task_id` (`task_id`),
    KEY `idx_reward_type` (`reward_type`) USING HASH,
    KEY `idx_main_reward` (`is_main_reward`, `reward_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务奖励配置表';

-- ==========================================
-- 用户任务记录表
-- ==========================================

-- 用户任务记录表
DROP TABLE IF EXISTS `t_user_task_record`;
CREATE TABLE `t_user_task_record` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `user_id`         BIGINT       NOT NULL                COMMENT '用户ID',
    `task_id`         BIGINT       NOT NULL                COMMENT '任务模板ID',
    `task_date`       DATE         NOT NULL                COMMENT '任务日期（用于每日任务）',
    
    -- 任务信息冗余（避免连表查询，数据类型与模板表一致）
    `task_name`       VARCHAR(60)  NOT NULL                COMMENT '任务名称（冗余）',
    `task_type`       TINYINT      NOT NULL                COMMENT '任务类型（冗余）',
    `task_category`   TINYINT      NOT NULL                COMMENT '任务分类（冗余）',
    `target_count`    INT          NOT NULL                COMMENT '目标完成次数（冗余）',
    
    -- 完成情况
    `current_count`   INT          NOT NULL DEFAULT 0      COMMENT '当前完成次数',
    `is_completed`    TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '是否已完成',
    `is_rewarded`     TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '是否已领取奖励',
    `complete_time`   TIMESTAMP    NULL                    COMMENT '完成时间',
    `reward_time`     TIMESTAMP    NULL                    COMMENT '奖励领取时间',
    
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_task_date` (`user_id`, `task_id`, `task_date`),
    KEY `idx_user_date` (`user_id`, `task_date`),
    KEY `idx_task_id` (`task_id`) USING HASH,
    KEY `idx_task_type` (`task_type`, `task_date`),
    KEY `idx_completed_rewarded` (`is_completed`, `is_rewarded`),
    KEY `idx_complete_time` (`complete_time` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户任务记录表';

-- ==========================================
-- 用户奖励记录表
-- ==========================================

-- 用户奖励记录表
DROP TABLE IF EXISTS `t_user_reward_record`;
CREATE TABLE `t_user_reward_record` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '奖励记录ID',
    `user_id`       BIGINT       NOT NULL                COMMENT '用户ID',
    `task_record_id` BIGINT      NOT NULL                COMMENT '任务记录ID',
    `reward_source` TINYINT      NOT NULL DEFAULT 1      COMMENT '奖励来源：1-task, 2-event, 3-system, 4-admin',
    
    -- 奖励信息
    `reward_type`   TINYINT      NOT NULL                COMMENT '奖励类型：1-coin, 2-item, 3-vip, 4-experience, 5-badge',
    `reward_name`   VARCHAR(60)  NOT NULL                COMMENT '奖励名称',
    `reward_amount` INT          NOT NULL                COMMENT '奖励数量',
    `reward_data`   JSON                                 COMMENT '奖励扩展数据',
    
    -- 发放状态
    `status`        TINYINT      NOT NULL DEFAULT 1      COMMENT '状态：1-pending, 2-success, 3-failed, 4-expired',
    `grant_time`    TIMESTAMP    NULL                    COMMENT '发放时间',
    `expire_time`   TIMESTAMP    NULL                    COMMENT '过期时间',
    
    `create_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_task_record` (`task_record_id`) USING HASH,
    KEY `idx_reward_type` (`reward_type`) USING HASH,
    KEY `idx_status` (`status`) USING HASH,
    KEY `idx_reward_source` (`reward_source`, `reward_type`),
    KEY `idx_grant_time` (`grant_time` DESC),
    KEY `idx_create_time` (`create_time` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户奖励记录表';