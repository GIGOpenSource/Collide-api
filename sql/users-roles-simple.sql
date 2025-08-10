-- 角色表
DROP TABLE IF EXISTS `t_role`;
CREATE TABLE `t_role` (
    `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    `name`        VARCHAR(50)  NOT NULL                COMMENT '角色名称 (user, blogger, admin, vip)',
    `description` VARCHAR(200)                         COMMENT '角色描述',
    `create_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 插入默认角色
INSERT INTO `t_role` (`name`, `description`) VALUES
('user', '普通用户'),
('blogger', '博主/内容创作者'),
('admin', '管理员'),
('vip', '会员用户');

-- 用户角色关联表
DROP TABLE IF EXISTS `t_user_role`;
CREATE TABLE `t_user_role` (
    `id`          BIGINT    NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id`     BIGINT    NOT NULL                COMMENT '用户ID',
    `role_id`     INT       NOT NULL                COMMENT '角色ID',
    `create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_role_id` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';