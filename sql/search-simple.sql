-- ==========================================
-- 搜索模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 搜索历史表
DROP TABLE IF EXISTS `t_search_history`;
CREATE TABLE `t_search_history` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '搜索历史ID',
  `user_id`     BIGINT       NOT NULL                COMMENT '用户ID',
  `keyword`     VARCHAR(200) NOT NULL                COMMENT '搜索关键词',
  `search_type` VARCHAR(20)  NOT NULL DEFAULT 'content' COMMENT '搜索类型：content、goods、user',
  `result_count` INT         NOT NULL DEFAULT 0     COMMENT '搜索结果数量',
  `create_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_search_type` (`search_type`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='搜索历史表';

-- 热门搜索表
DROP TABLE IF EXISTS `t_hot_search`;
CREATE TABLE `t_hot_search` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '热搜ID',
  `keyword`     VARCHAR(200) NOT NULL                COMMENT '搜索关键词',
  `search_count` BIGINT      NOT NULL DEFAULT 0     COMMENT '搜索次数',
  `trend_score` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '趋势分数',
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、inactive',
  `create_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_keyword` (`keyword`),
  KEY `idx_search_count` (`search_count`),
  KEY `idx_trend_score` (`trend_score`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='热门搜索表'; 