-- ==========================================
-- 分类模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 分类主表
DROP TABLE IF EXISTS `t_category`;
CREATE TABLE `t_category` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name`         VARCHAR(100) NOT NULL                COMMENT '分类名称',
  `description`  TEXT                                 COMMENT '分类描述',
  `parent_id`    BIGINT       NOT NULL DEFAULT 0     COMMENT '父分类ID，0表示顶级分类',
  `icon_url`     VARCHAR(500)                         COMMENT '分类图标URL',
  `sort`         INT          NOT NULL DEFAULT 0     COMMENT '排序值',
  `content_count` BIGINT      NOT NULL DEFAULT 0     COMMENT '内容数量（冗余统计）',
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、inactive',
  `create_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_parent` (`name`, `parent_id`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_status` (`status`),
  KEY `idx_sort` (`sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类主表';