-- ==========================================
-- 用户模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- V2: 拆分用户角色为独立表
-- ==========================================

USE collide;

-- 用户统一信息表（去连表设计）
DROP TABLE IF EXISTS `t_user`;
CREATE TABLE `t_user` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username`        VARCHAR(50)  NOT NULL                COMMENT '用户名',
    `nickname`        VARCHAR(100) NOT NULL                COMMENT '昵称',
    `avatar`          VARCHAR(500)                         COMMENT '头像URL',
    `email`           VARCHAR(100)                         COMMENT '邮箱',
    `phone`           VARCHAR(20)                          COMMENT '手机号',
    `password_hash`   VARCHAR(255) NOT NULL                COMMENT '密码哈希',
    `status`          VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '用户状态：active、inactive、suspended、banned',
    
    -- 扩展信息字段
    `bio`             TEXT                                 COMMENT '个人简介',
    `birthday`        DATE                                 COMMENT '生日',
    `gender`          VARCHAR(10)  DEFAULT 'unknown'       COMMENT '性别：male、female、unknown',
    `location`        VARCHAR(100)                         COMMENT '所在地',
    
    -- 统计字段（冗余设计，避免连表）
    `follower_count`  BIGINT       NOT NULL DEFAULT 0     COMMENT '粉丝数',
    `following_count` BIGINT       NOT NULL DEFAULT 0     COMMENT '关注数',
    `content_count`   BIGINT       NOT NULL DEFAULT 0     COMMENT '内容数',
    `like_count`      BIGINT       NOT NULL DEFAULT 0     COMMENT '获得点赞数',
    
    -- VIP相关字段
    `vip_expire_time` DATETIME                             COMMENT 'VIP过期时间',
    
    -- 登录相关
    `last_login_time` DATETIME                             COMMENT '最后登录时间',
    `login_count`     BIGINT       NOT NULL DEFAULT 0     COMMENT '登录次数',
    
    -- 邀请相关
    `invite_code`     VARCHAR(20)                          COMMENT '邀请码',
    `inviter_id`      BIGINT                               COMMENT '邀请人ID',
    `invited_count`   BIGINT       NOT NULL DEFAULT 0     COMMENT '邀请人数',
    
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    UNIQUE KEY `uk_phone` (`phone`),
    UNIQUE KEY `uk_invite_code` (`invite_code`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户统一信息表';


-- 用户钱包表（扩展版：支持任务金币系统）
DROP TABLE IF EXISTS `t_user_wallet`;
CREATE TABLE `t_user_wallet` (
    `id`               BIGINT        NOT NULL AUTO_INCREMENT COMMENT '钱包ID',
    `user_id`          BIGINT        NOT NULL                COMMENT '用户ID',
    
    -- 现金资产字段
    `balance`          DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '现金余额',
    `frozen_amount`    DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '冻结金额',
    
    -- 虚拟货币字段（任务系统）
    `coin_balance`     BIGINT        NOT NULL DEFAULT 0      COMMENT '金币余额（任务奖励虚拟货币）',
    `coin_total_earned` BIGINT       NOT NULL DEFAULT 0      COMMENT '累计获得金币',
    `coin_total_spent` BIGINT        NOT NULL DEFAULT 0      COMMENT '累计消费金币',
    
    -- 统计字段
    `total_income`     DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '总收入',
    `total_expense`    DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '总支出',
    
    `status`           VARCHAR(20)   NOT NULL DEFAULT 'active' COMMENT '状态：active、frozen',
    `create_time`      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_coin_balance` (`coin_balance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户钱包表（支持现金+金币）';

-- 用户拉黑表（无连表设计）
DROP TABLE IF EXISTS `t_user_block`;
CREATE TABLE `t_user_block` (
    `id`               BIGINT      NOT NULL AUTO_INCREMENT COMMENT '拉黑记录ID',
    `user_id`          BIGINT      NOT NULL                COMMENT '拉黑者用户ID',
    `blocked_user_id`  BIGINT      NOT NULL                COMMENT '被拉黑用户ID',
    
    -- 冗余用户信息，避免连表查询
    `user_username`    VARCHAR(50) NOT NULL                COMMENT '拉黑者用户名',
    `blocked_username` VARCHAR(50) NOT NULL                COMMENT '被拉黑用户名',
    
    `status`           VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '拉黑状态：active、cancelled',
    `reason`           VARCHAR(200)                        COMMENT '拉黑原因',
    
    `create_time`      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '拉黑时间',
    `update_time`      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_blocked` (`user_id`, `blocked_user_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_blocked_user_id` (`blocked_user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户拉黑关系表';