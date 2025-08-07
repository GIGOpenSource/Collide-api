-- ==========================================
-- 标签模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 标签主表
DROP TABLE IF EXISTS `t_tag`;
CREATE TABLE `t_tag` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name`         VARCHAR(100) NOT NULL                 COMMENT '标签名称',
  `description`  TEXT                                  COMMENT '标签描述',
  `tag_type`     VARCHAR(20)  NOT NULL DEFAULT 'content' COMMENT '标签类型：content、interest、system',
  `category_id`  BIGINT                                COMMENT '所属分类ID',
  `usage_count`  BIGINT       NOT NULL DEFAULT 0      COMMENT '使用次数',
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、inactive',
  `create_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_type` (`name`, `tag_type`),
  KEY `idx_tag_type` (`tag_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签主表';

-- 用户兴趣标签关联表
DROP TABLE IF EXISTS `t_user_interest_tag`;
CREATE TABLE `t_user_interest_tag` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id`        BIGINT       NOT NULL                 COMMENT '用户ID',
  `tag_id`         BIGINT       NOT NULL                 COMMENT '标签ID',
  `interest_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00   COMMENT '兴趣分数（0-100）',
  `status`         VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、inactive',
  `create_time`    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_tag` (`user_id`, `tag_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户兴趣标签关联表';

-- 内容标签关联表
DROP TABLE IF EXISTS `t_content_tag`;
CREATE TABLE `t_content_tag` (
  `id`          BIGINT    NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `content_id`  BIGINT    NOT NULL                 COMMENT '内容ID',
  `tag_id`      BIGINT    NOT NULL                 COMMENT '标签ID',
  `create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_content_tag` (`content_id`, `tag_id`),
  KEY `idx_content_id` (`content_id`),
  KEY `idx_tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内容标签关联表';