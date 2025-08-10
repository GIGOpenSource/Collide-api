-- ==========================================
-- 社交动态模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 动态主表（去连表化设计）
DROP TABLE IF EXISTS `t_social_dynamic`;
CREATE TABLE `t_social_dynamic` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '动态ID',
  `content`      TEXT         NOT NULL                COMMENT '动态内容',
  `dynamic_type` VARCHAR(20)  NOT NULL DEFAULT 'text' COMMENT '动态类型：text、image、video、share',
  `images`       TEXT                                 COMMENT '图片列表，JSON格式',
  `video_url`    VARCHAR(500)                         COMMENT '视频URL',
  
  -- 用户信息（冗余字段，避免连表）
  `user_id`      BIGINT       NOT NULL                COMMENT '发布用户ID',
  `user_nickname` VARCHAR(100)                        COMMENT '用户昵称（冗余）',
  `user_avatar`  VARCHAR(500)                         COMMENT '用户头像（冗余）',
  
  -- 分享相关（如果是分享动态）
  `share_target_type` VARCHAR(20)                     COMMENT '分享目标类型：content、goods',
  `share_target_id`   BIGINT                          COMMENT '分享目标ID',
  `share_target_title` VARCHAR(200)                   COMMENT '分享目标标题（冗余）',
  
  -- 统计字段（冗余存储，避免聚合查询）
  `like_count`   BIGINT       NOT NULL DEFAULT 0     COMMENT '点赞数（冗余统计）',
  `comment_count` BIGINT      NOT NULL DEFAULT 0     COMMENT '评论数（冗余统计）',
  `share_count`  BIGINT       NOT NULL DEFAULT 0     COMMENT '分享数（冗余统计）',
  
  -- 状态相关字段
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'normal' COMMENT '状态：normal、hidden、deleted',
  `review_status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '审核状态：PENDING、APPROVED、REJECTED',
  `create_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_dynamic_type` (`dynamic_type`),
  KEY `idx_status` (`status`),
  KEY `idx_review_status` (`review_status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社交动态主表';

-- 付费动态表
DROP TABLE IF EXISTS `t_social_paid_dynamic`;
CREATE TABLE `t_social_paid_dynamic` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '付费动态ID',
  `dynamic_id`      BIGINT       NOT NULL                COMMENT '关联的动态ID',
  `price`           INT          NOT NULL DEFAULT 0      COMMENT '价格（金币）',
  `purchase_count`  BIGINT       NOT NULL DEFAULT 0      COMMENT '购买次数',
  `total_income`    BIGINT       NOT NULL DEFAULT 0      COMMENT '总收入（金币）',
  `is_active`       TINYINT(1)   NOT NULL DEFAULT 1      COMMENT '是否激活',
  `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dynamic_id` (`dynamic_id`),
  KEY `idx_price` (`price`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='付费动态表';

-- 动态购买记录表
DROP TABLE IF EXISTS `t_social_dynamic_purchase`;
CREATE TABLE `t_social_dynamic_purchase` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '购买记录ID',
  `dynamic_id`      BIGINT       NOT NULL                COMMENT '动态ID',
  `buyer_id`        BIGINT       NOT NULL                COMMENT '购买者用户ID',
  `price`           INT          NOT NULL                COMMENT '购买价格（金币）',
  `purchase_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '购买时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dynamic_buyer` (`dynamic_id`, `buyer_id`),
  KEY `idx_buyer_id` (`buyer_id`),
  KEY `idx_purchase_time` (`purchase_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='动态购买记录表'; 