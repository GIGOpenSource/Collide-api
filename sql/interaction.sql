DROP TABLE IF EXISTS `t_interaction`;
CREATE TABLE `t_interaction` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '互动ID',
  `interaction_type`   VARCHAR(20)  NOT NULL                COMMENT '互动类型：COMMENT、LIKE、FOLLOW',
  `target_id`   BIGINT       NOT NULL                COMMENT '目标对象ID',
  `user_id`     BIGINT       NOT NULL                COMMENT '点赞用户ID',

  -- 目标对象信息（冗余字段，避免连表）
  `target_title`    VARCHAR(200)                     COMMENT '目标对象标题（冗余）',
  `target_author_id` BIGINT                          COMMENT '目标对象作者ID（冗余）',

  -- 用户信息（冗余字段，避免连表）
  `user_nickname`   VARCHAR(100)                     COMMENT '用户昵称（冗余）',
  `user_avatar`     VARCHAR(500)                     COMMENT '用户头像（冗余）',

  `status`      VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active、cancelled',
  `create_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_target` (`user_id`, `interaction_type`, `target_id`),
  KEY `idx_target_id` (`target_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_interaction_type` (`interaction_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='互动主表';