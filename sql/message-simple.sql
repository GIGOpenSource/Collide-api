-- ==========================================
-- Collide 私信留言板模块 - 简洁版
-- 用户间私信功能，支持实时消息和留言板
-- 设计原则：简洁、高效、易扩展
-- ==========================================

USE collide;

-- ==========================================
-- 私信消息表
-- ==========================================

-- 私信消息主表
DROP TABLE IF EXISTS `t_message`;
CREATE TABLE `t_message` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    `sender_id`     BIGINT       NOT NULL                COMMENT '发送者ID',
    `receiver_id`   BIGINT       NOT NULL                COMMENT '接收者ID',
    `content`       TEXT         NOT NULL                COMMENT '消息内容',
    `message_type`  VARCHAR(20)  NOT NULL DEFAULT 'text' COMMENT '消息类型：text、image、file、system',
    `extra_data`    JSON                                 COMMENT '扩展数据（图片URL、文件信息等）',
    `status`        VARCHAR(20)  NOT NULL DEFAULT 'sent' COMMENT '消息状态：sent、delivered、read、deleted',
    `read_time`     TIMESTAMP    NULL                    COMMENT '已读时间',
    `reply_to_id`   BIGINT       NULL                    COMMENT '回复的消息ID（引用消息）',
    `is_pinned`     TINYINT(1)   NOT NULL DEFAULT 0     COMMENT '是否置顶（留言板功能）',
    `create_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_sender_receiver` (`sender_id`, `receiver_id`),
    KEY `idx_receiver_status` (`receiver_id`, `status`),
    KEY `idx_create_time` (`create_time`),
    KEY `idx_reply_to` (`reply_to_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='私信消息表';

-- ==========================================
-- 会话统计表（可选，用于优化查询）
-- ==========================================

-- 用户会话统计表
DROP TABLE IF EXISTS `t_message_session`;
CREATE TABLE `t_message_session` (
    `id`                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '会话ID',
    `user_id`           BIGINT       NOT NULL                COMMENT '用户ID',
    `other_user_id`     BIGINT       NOT NULL                COMMENT '对方用户ID',
    `last_message_id`   BIGINT       NULL                    COMMENT '最后一条消息ID',
    `last_message_time` TIMESTAMP    NULL                    COMMENT '最后消息时间',
    `unread_count`      INT          NOT NULL DEFAULT 0     COMMENT '未读消息数',
    `is_archived`       TINYINT(1)   NOT NULL DEFAULT 0     COMMENT '是否归档',
    `create_time`       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_other` (`user_id`, `other_user_id`),
    KEY `idx_user_time` (`user_id`, `last_message_time`),
    KEY `idx_last_message` (`last_message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户会话统计表';

-- ==========================================
-- 消息设置表（可选）
-- ==========================================

-- 用户消息设置表
DROP TABLE IF EXISTS `t_message_setting`;
CREATE TABLE `t_message_setting` (
    `id`                    BIGINT       NOT NULL AUTO_INCREMENT COMMENT '设置ID',
    `user_id`               BIGINT       NOT NULL                COMMENT '用户ID',
    `allow_stranger_msg`    TINYINT(1)   NOT NULL DEFAULT 1     COMMENT '是否允许陌生人发消息',
    `auto_read_receipt`     TINYINT(1)   NOT NULL DEFAULT 1     COMMENT '是否自动发送已读回执',
    `message_notification`  TINYINT(1)   NOT NULL DEFAULT 1     COMMENT '是否开启消息通知',
    `create_time`           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户消息设置表';

-- ==========================================
-- 初始化数据
-- ==========================================

-- 插入默认系统消息类型配置（可选）
INSERT INTO `t_message` (`sender_id`, `receiver_id`, `content`, `message_type`, `status`) VALUES
(0, 0, '欢迎使用Collide私信功能！', 'system', 'read');

-- ==========================================
-- 常用查询示例
-- ==========================================

-- 1. 获取用户会话列表（最近聊天的人）
-- SELECT DISTINCT 
--     CASE 
--         WHEN sender_id = #{userId} THEN receiver_id 
--         ELSE sender_id 
--     END AS other_user_id,
--     MAX(create_time) AS last_time,
--     COUNT(CASE WHEN receiver_id = #{userId} AND status != 'read' THEN 1 END) AS unread_count
-- FROM t_message 
-- WHERE sender_id = #{userId} OR receiver_id = #{userId}
-- GROUP BY other_user_id
-- ORDER BY last_time DESC;

-- 2. 获取两人之间的消息记录
-- SELECT * FROM t_message 
-- WHERE (sender_id = #{userId1} AND receiver_id = #{userId2}) 
--    OR (sender_id = #{userId2} AND receiver_id = #{userId1})
-- ORDER BY create_time ASC;

-- 3. 获取用户未读消息数
-- SELECT COUNT(*) FROM t_message 
-- WHERE receiver_id = #{userId} AND status != 'read';

-- 4. 获取用户留言板消息（置顶+最新）
-- SELECT * FROM t_message 
-- WHERE receiver_id = #{userId} 
-- ORDER BY is_pinned DESC, create_time DESC;

-- ==========================================
-- 索引优化说明
-- ==========================================

-- 1. idx_sender_receiver: 用于查询两人间的对话
-- 2. idx_receiver_status: 用于查询接收者的未读消息
-- 3. idx_create_time: 用于按时间排序
-- 4. idx_reply_to: 用于查询回复关系

-- ==========================================
-- 功能特性说明
-- ==========================================

-- 1. 私信功能：
--    - 支持文本、图片、文件等多种消息类型
--    - 消息状态追踪（已发送、已送达、已读）
--    - 支持消息回复和引用

-- 2. 留言板功能：
--    - 通过 is_pinned 字段实现置顶
--    - 支持在用户个人页面留言

-- 3. 设置功能：
--    - 隐私设置（是否允许陌生人发消息）
--    - 通知设置（消息提醒开关）

-- 4. 性能优化：
--    - 通过 t_message_session 表优化会话列表查询
--    - 合理的索引设计支持高并发查询

-- ==========================================
-- 扩展建议
-- ==========================================

-- 1. 消息加密：可在应用层实现端到端加密
-- 2. 消息撤回：可增加 is_recalled 字段
-- 3. 群聊功能：可扩展支持多人聊天
-- 4. 消息搜索：配合搜索引擎实现全文检索
-- 5. 消息推送：集成第三方推送服务