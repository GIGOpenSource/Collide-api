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
  
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'normal' COMMENT '状态：normal、hidden、deleted',
  `create_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_dynamic_type` (`dynamic_type`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社交动态主表'; 