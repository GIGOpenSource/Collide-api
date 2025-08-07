-- ==========================================
-- 关注模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 关注关系表（去连表化设计）
DROP TABLE IF EXISTS `t_follow`;
CREATE TABLE `t_follow` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '关注ID',
  `follower_id` BIGINT       NOT NULL                COMMENT '关注者用户ID',
  `followee_id` BIGINT       NOT NULL                COMMENT '被关注者用户ID',
  
  -- 关注者信息（冗余字段，避免连表）
  `follower_nickname` VARCHAR(100)                   COMMENT '关注者昵称（冗余）',
  `follower_avatar`   VARCHAR(500)                   COMMENT '关注者头像（冗余）',
  
  -- 被关注者信息（冗余字段，避免连表）
  `followee_nickname` VARCHAR(100)                   COMMENT '被关注者昵称（冗余）',
  `followee_avatar`   VARCHAR(500)                   COMMENT '被关注者头像（冗余）',
  
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、cancelled',
  `create_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_follower_followee` (`follower_id`, `followee_id`),
  KEY `idx_follower_id` (`follower_id`),
  KEY `idx_followee_id` (`followee_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注关系表'; 