-- ==========================================
-- 收藏模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 收藏主表（去连表化设计）
DROP TABLE IF EXISTS `t_favorite`;
CREATE TABLE `t_favorite` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
  `favorite_type` VARCHAR(20) NOT NULL                COMMENT '收藏类型：CONTENT、GOODS',
  `target_id`   BIGINT       NOT NULL                COMMENT '收藏目标ID',
  `user_id`     BIGINT       NOT NULL                COMMENT '收藏用户ID',
  
  -- 收藏对象信息（冗余字段，避免连表）
  `target_title`    VARCHAR(200)                     COMMENT '收藏对象标题（冗余）',
  `target_cover`    VARCHAR(500)                     COMMENT '收藏对象封面（冗余）',
  `target_author_id` BIGINT                          COMMENT '收藏对象作者ID（冗余）',
  
  -- 用户信息（冗余字段，避免连表）
  `user_nickname`   VARCHAR(100)                     COMMENT '用户昵称（冗余）',
  
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、cancelled',
  `create_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_target` (`user_id`, `favorite_type`, `target_id`),
  KEY `idx_target_id` (`target_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_favorite_type` (`favorite_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏主表'; 