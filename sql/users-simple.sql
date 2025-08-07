-- ==========================================
-- 用户模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 用户统一信息表（去连表设计）
DROP TABLE IF EXISTS `t_user`;
CREATE TABLE `t_user` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username`        VARCHAR(50)  NOT NULL                COMMENT '用户名',
    `nickname`        VARCHAR(100) NOT NULL                COMMENT '昵称',
    `avatar`          VARCHAR(500)                         COMMENT '头像URL',
    `email`           VARCHAR(100)                         COMMENT '邮箱',
    `phone`           VARCHAR(20)                          COMMENT '手机号',
    `password_hash`   VARCHAR(255) NOT NULL                COMMENT '密码哈希',
    `role`            VARCHAR(20)  NOT NULL DEFAULT 'user' COMMENT '用户角色：user、blogger、admin、vip',
    `status`          VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '用户状态：active、inactive、suspended、banned',
    
    -- 扩展信息字段
    `bio`             TEXT                                 COMMENT '个人简介',
    `birthday`        DATE                                 COMMENT '生日',
    `gender`          VARCHAR(10)  DEFAULT 'unknown'       COMMENT '性别：male、female、unknown',
    `location`        VARCHAR(100)                         COMMENT '所在地',
    
    -- 统计字段（冗余设计，避免连表）
    `follower_count`  BIGINT       NOT NULL DEFAULT 0     COMMENT '粉丝数',
    `following_count` BIGINT       NOT NULL DEFAULT 0     COMMENT '关注数',
    `content_count`   BIGINT       NOT NULL DEFAULT 0     COMMENT '内容数',
    `like_count`      BIGINT       NOT NULL DEFAULT 0     COMMENT '获得点赞数',
    
    -- VIP相关字段
    `vip_expire_time` DATETIME                             COMMENT 'VIP过期时间',
    
    -- 登录相关
    `last_login_time` DATETIME                             COMMENT '最后登录时间',
    `login_count`     BIGINT       NOT NULL DEFAULT 0     COMMENT '登录次数',
    
    -- 邀请相关
    `invite_code`     VARCHAR(20)                          COMMENT '邀请码',
    `inviter_id`      BIGINT                               COMMENT '邀请人ID',
    `invited_count`   BIGINT       NOT NULL DEFAULT 0     COMMENT '邀请人数',
    
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    UNIQUE KEY `uk_phone` (`phone`),
    UNIQUE KEY `uk_invite_code` (`invite_code`),
    KEY `idx_role` (`role`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户统一信息表';

-- 用户钱包表（扩展版：支持任务金币系统）
DROP TABLE IF EXISTS `t_user_wallet`;
CREATE TABLE `t_user_wallet` (
    `id`               BIGINT        NOT NULL AUTO_INCREMENT COMMENT '钱包ID',
    `user_id`          BIGINT        NOT NULL                COMMENT '用户ID',
    
    -- 现金资产字段
    `balance`          DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '现金余额',
    `frozen_amount`    DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '冻结金额',
    
    -- 虚拟货币字段（任务系统）
    `coin_balance`     BIGINT        NOT NULL DEFAULT 0      COMMENT '金币余额（任务奖励虚拟货币）',
    `coin_total_earned` BIGINT       NOT NULL DEFAULT 0      COMMENT '累计获得金币',
    `coin_total_spent` BIGINT        NOT NULL DEFAULT 0      COMMENT '累计消费金币',
    
    -- 统计字段
    `total_income`     DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '总收入',
    `total_expense`    DECIMAL(15,2) NOT NULL DEFAULT 0.00   COMMENT '总支出',
    
    `status`           VARCHAR(20)   NOT NULL DEFAULT 'active' COMMENT '状态：active、frozen',
    `create_time`      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_coin_balance` (`coin_balance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户钱包表（支持现金+金币）';

-- 用户拉黑表（无连表设计）
DROP TABLE IF EXISTS `t_user_block`;
CREATE TABLE `t_user_block` (
    `id`               BIGINT      NOT NULL AUTO_INCREMENT COMMENT '拉黑记录ID',
    `user_id`          BIGINT      NOT NULL                COMMENT '拉黑者用户ID',
    `blocked_user_id`  BIGINT      NOT NULL                COMMENT '被拉黑用户ID',
    
    -- 冗余用户信息，避免连表查询
    `user_username`    VARCHAR(50) NOT NULL                COMMENT '拉黑者用户名',
    `blocked_username` VARCHAR(50) NOT NULL                COMMENT '被拉黑用户名',
    
    `status`           VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '拉黑状态：active、cancelled',
    `reason`           VARCHAR(200)                        COMMENT '拉黑原因',
    
    `create_time`      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '拉黑时间',
    `update_time`      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_blocked` (`user_id`, `blocked_user_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_blocked_user_id` (`blocked_user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户拉黑关系表';

-- ==========================================
-- 钱包操作存储过程
-- ==========================================

DELIMITER $$

-- 金币奖励发放（任务系统调用）
DROP PROCEDURE IF EXISTS `grant_coin_reward`$$
CREATE PROCEDURE `grant_coin_reward`(
    IN p_user_id BIGINT,
    IN p_amount BIGINT,
    IN p_source VARCHAR(50)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 更新用户金币余额
    INSERT INTO `t_user_wallet` (`user_id`, `coin_balance`, `coin_total_earned`)
    VALUES (p_user_id, p_amount, p_amount)
    ON DUPLICATE KEY UPDATE
        `coin_balance` = `coin_balance` + p_amount,
        `coin_total_earned` = `coin_total_earned` + p_amount,
        `update_time` = CURRENT_TIMESTAMP;
    
    COMMIT;
END$$

-- 金币消费（商城等系统调用）
DROP PROCEDURE IF EXISTS `consume_coin`$$
CREATE PROCEDURE `consume_coin`(
    IN p_user_id BIGINT,
    IN p_amount BIGINT,
    IN p_reason VARCHAR(100),
    OUT p_result INT
)
BEGIN
    DECLARE v_current_balance BIGINT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_result = -1;
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 检查余额是否充足
    SELECT `coin_balance` INTO v_current_balance
    FROM `t_user_wallet`
    WHERE `user_id` = p_user_id
    FOR UPDATE;
    
    IF v_current_balance IS NULL THEN
        -- 用户钱包不存在，创建钱包
        INSERT INTO `t_user_wallet` (`user_id`) VALUES (p_user_id);
        SET v_current_balance = 0;
    END IF;
    
    IF v_current_balance < p_amount THEN
        SET p_result = 0; -- 余额不足
        ROLLBACK;
    ELSE
        -- 扣减金币
        UPDATE `t_user_wallet`
        SET `coin_balance` = `coin_balance` - p_amount,
            `coin_total_spent` = `coin_total_spent` + p_amount,
            `update_time` = CURRENT_TIMESTAMP
        WHERE `user_id` = p_user_id;
        
        SET p_result = 1; -- 成功
        COMMIT;
    END IF;
END$$

-- 现金充值
DROP PROCEDURE IF EXISTS `recharge_balance`$$
CREATE PROCEDURE `recharge_balance`(
    IN p_user_id BIGINT,
    IN p_amount DECIMAL(15,2),
    IN p_payment_method VARCHAR(50)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 更新用户现金余额
    INSERT INTO `t_user_wallet` (`user_id`, `balance`, `total_income`)
    VALUES (p_user_id, p_amount, p_amount)
    ON DUPLICATE KEY UPDATE
        `balance` = `balance` + p_amount,
        `total_income` = `total_income` + p_amount,
        `update_time` = CURRENT_TIMESTAMP;
    
    COMMIT;
END$$

DELIMITER ;

-- ==========================================
-- 初始化管理员用户
-- ==========================================

INSERT INTO `t_user` (`username`, `nickname`, `email`, `password_hash`, `role`, `status`) VALUES
('admin', '系统管理员', 'admin@collide.com', '$2a$10$encrypted_password_hash', 'admin', 'active'),
('blogger', '博主示例', 'blogger@collide.com', '$2a$10$encrypted_password_hash', 'blogger', 'active');

-- 初始化管理员钱包
INSERT INTO `t_user_wallet` (`user_id`, `balance`, `coin_balance`, `coin_total_earned`) VALUES
(1, 1000.00, 500, 500),
(2, 100.00, 100, 100);

-- ==========================================
-- 钱包系统使用说明
-- ==========================================

-- 1. 资产类型说明：
--    - balance: 现金余额（单位：元，支持小数点后2位）
--    - coin_balance: 金币余额（单位：个，整数）
--    - 1元 ≈ 100金币（可根据业务调整汇率）

-- 2. 任务奖励集成：
--    - 任务完成后调用: CALL grant_coin_reward(user_id, coin_amount, 'task_reward');
--    - 自动更新: coin_balance 和 coin_total_earned

-- 3. 金币消费：
--    - 商城购买调用: CALL consume_coin(user_id, coin_amount, 'purchase', @result);
--    - 返回值: 1=成功, 0=余额不足, -1=系统错误

-- 4. 现金充值：
--    - 充值调用: CALL recharge_balance(user_id, amount, 'alipay');
--    - 自动更新: balance 和 total_income

-- 5. 查询示例：
--    -- 获取用户完整钱包信息
--    SELECT user_id, balance, coin_balance, coin_total_earned, coin_total_spent, 
--           total_income, total_expense, status 
--    FROM t_user_wallet WHERE user_id = 1;
--    
--    -- 检查金币余额是否充足
--    SELECT coin_balance >= 50 as can_afford 
--    FROM t_user_wallet WHERE user_id = 1;
--    
--    -- 获取金币排行榜
--    SELECT u.username, w.coin_balance, w.coin_total_earned
--    FROM t_user u JOIN t_user_wallet w ON u.id = w.user_id
--    ORDER BY w.coin_balance DESC LIMIT 10; 