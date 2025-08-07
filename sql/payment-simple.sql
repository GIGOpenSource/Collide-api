-- ==========================================
-- 支付模块数据库设计 - 大白鲨支付对接版
-- 基于大白鲨支付接口文档v1.1.5设计
-- 支持去连表化设计原则，保留核心功能
-- ==========================================

USE collide;

-- 支付渠道配置表（为将来扩展多渠道做准备）
DROP TABLE IF EXISTS `t_payment_channel`;
CREATE TABLE `t_payment_channel` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '渠道ID',
  `channel_code`    VARCHAR(50)  NOT NULL                COMMENT '渠道代码：shark_pay',
  `channel_name`    VARCHAR(100) NOT NULL                COMMENT '渠道名称：大白鲨支付',
  `provider`        VARCHAR(50)  NOT NULL                COMMENT '支付提供商：shark',
  `channel_type`    VARCHAR(20)  NOT NULL                COMMENT '渠道类型：H5、APP、PC',
  
  -- 配置信息
  `merchant_id`     VARCHAR(50)  NOT NULL                COMMENT '商户编号',
  `app_secret`      VARCHAR(200) NOT NULL                COMMENT '商户密钥',
  `api_gateway`     VARCHAR(200) NOT NULL                COMMENT 'API网关地址',
  `timeout`         INT          DEFAULT 30000           COMMENT '超时时间（毫秒）',
  `retry_times`     INT          DEFAULT 3               COMMENT '重试次数',
  
  -- 状态和限制
  `status`          VARCHAR(20)  DEFAULT 'active'        COMMENT '状态：active、inactive、maintenance',
  `priority`        INT          DEFAULT 100             COMMENT '优先级（数字越大优先级越高）',
  `daily_limit`     DECIMAL(15,2) DEFAULT 999999999.99  COMMENT '日限额',
  `single_limit`    DECIMAL(10,2) DEFAULT 50000.00      COMMENT '单笔限额',
  
  -- 费率设置
  `fee_type`        VARCHAR(20)  DEFAULT 'percentage'    COMMENT '费率类型：percentage、fixed',
  `fee_rate`        DECIMAL(8,4) DEFAULT 0.0060         COMMENT '费率（百分比或固定金额）',
  `min_fee`         DECIMAL(8,2) DEFAULT 0.01           COMMENT '最小手续费',
  `max_fee`         DECIMAL(8,2) DEFAULT 50.00          COMMENT '最大手续费',
  
  `create_time`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_channel_code` (`channel_code`),
  KEY `idx_provider_status` (`provider`, `status`),
  KEY `idx_priority` (`priority` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付渠道配置表';

-- 支付订单表（基于大白鲨支付接口设计）
-- 注意：info玩家信息字段组是可选的，根据业务需要传递
DROP TABLE IF EXISTS `t_payment_order`;
CREATE TABLE `t_payment_order` (
  `id`                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `order_no`          VARCHAR(64)  NOT NULL                COMMENT '商户订单号（对应tradeNo，必填）',
  `platform_order_no` VARCHAR(64)                         COMMENT '大白鲨平台订单号（对应oid）',
  `user_id`           BIGINT       NOT NULL                COMMENT '用户ID',
  `user_nickname`     VARCHAR(100)                         COMMENT '用户昵称（冗余）',
  
  -- 支付信息
  `channel_code`      VARCHAR(50)  NOT NULL                COMMENT '使用的支付渠道代码',
  `channel_name`      VARCHAR(100)                         COMMENT '支付渠道名称（冗余）',
  `pay_type`          VARCHAR(50)  NOT NULL                COMMENT '支付类型：alipay、wechat、unionCard等',
  `pay_mode`          VARCHAR(20)                          COMMENT '支付模式：url、sdk、card',
  
  -- 金额相关
  `amount`            DECIMAL(12,2) NOT NULL               COMMENT '订单金额（元）',
  `actual_amount`     DECIMAL(12,2)                        COMMENT '实际到账金额',
  `fee_amount`        DECIMAL(8,2)  DEFAULT 0.00           COMMENT '手续费金额',
  `currency`          VARCHAR(10)   DEFAULT 'CNY'          COMMENT '货币类型',
  
  -- 状态和时间
  `status`            VARCHAR(20)   DEFAULT 'pending'      COMMENT '订单状态：pending、paid、failed、cancelled、expired',
  `pay_url`           TEXT                                 COMMENT '支付链接或参数（JSON）',
  `pay_time`          DATETIME                             COMMENT '支付完成时间',
  `expire_time`       DATETIME                             COMMENT '订单过期时间',
  `notify_time`       DATETIME                             COMMENT '回调通知时间',
  
  -- 玩家信息（大白鲨支付info字段，可选）
  `player_id`         VARCHAR(32)                          COMMENT '玩家ID（info.playerId）',
  `player_ip`         VARCHAR(32)                          COMMENT '玩家IP（info.playerIp）',
  `device_id`         VARCHAR(32)                          COMMENT '玩家设备ID（info.deviceId）',
  `device_type`       VARCHAR(32)                          COMMENT '设备类型：ios、android、pc（info.deviceType）',
  `player_name`       VARCHAR(32)                          COMMENT '玩家姓名（info.name）',
  `player_tel`        VARCHAR(32)                          COMMENT '玩家手机号（info.tel）',
  `player_pay_act`    VARCHAR(32)                          COMMENT '玩家付款账号（info.payAct）',
  
  -- 回调和扩展
  `notify_url`        VARCHAR(200)                         COMMENT '异步通知地址',
  `return_url`        VARCHAR(200)                         COMMENT '同步跳转地址',
  `payload`           VARCHAR(100)                         COMMENT '扩展参数（如过滤赔付渠道）',
  `extend_params`     JSON                                 COMMENT '其他扩展参数',
  
  -- 签名和请求信息
  `request_sign`      VARCHAR(64)                          COMMENT '请求签名',
  `response_sign`     VARCHAR(64)                          COMMENT '响应签名',
  `request_time`      BIGINT                               COMMENT 'UTC时间戳(13位)',
  
  `create_time`       TIMESTAMP     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`       TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  UNIQUE KEY `uk_platform_order` (`platform_order_no`),
  KEY `idx_user_status` (`user_id`, `status`),
  KEY `idx_channel_status` (`channel_code`, `status`),
  KEY `idx_player_id` (`player_id`),
  KEY `idx_create_time` (`create_time` DESC),
  KEY `idx_pay_time` (`pay_time` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付订单表';

-- 支付回调日志表
DROP TABLE IF EXISTS `t_payment_notify_log`;
CREATE TABLE `t_payment_notify_log` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `order_no`        VARCHAR(64)  NOT NULL                COMMENT '商户订单号',
  `platform_order_no` VARCHAR(64)                        COMMENT '平台订单号',
  `channel_code`    VARCHAR(50)  NOT NULL                COMMENT '支付渠道代码',
  
  -- 回调信息
  `notify_type`     VARCHAR(20)  NOT NULL                COMMENT '通知类型：payment、refund',
  `notify_data`     TEXT         NOT NULL                COMMENT '原始回调数据',
  `notify_sign`     VARCHAR(64)                          COMMENT '回调签名',
  `sign_verify`     TINYINT(1)   DEFAULT 0               COMMENT '签名验证结果：0失败、1成功',
  
  -- 处理结果
  `process_status`  VARCHAR(20)  DEFAULT 'pending'       COMMENT '处理状态：pending、success、failed',
  `process_result`  TEXT                                 COMMENT '处理结果描述',
  `retry_times`     INT          DEFAULT 0               COMMENT '重试次数',
  `response_code`   VARCHAR(10)                          COMMENT '响应状态码',
  `response_data`   TEXT                                 COMMENT '响应数据',
  
  -- 时间信息
  `notify_time`     DATETIME     NOT NULL                COMMENT '回调时间',
  `process_time`    DATETIME                             COMMENT '处理完成时间',
  `create_time`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_order_no` (`order_no`),
  KEY `idx_platform_order` (`platform_order_no`),
  KEY `idx_channel_status` (`channel_code`, `process_status`),
  KEY `idx_notify_time` (`notify_time` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付回调日志表';

-- 支付统计表（可选，用于快速统计查询）
DROP TABLE IF EXISTS `t_payment_statistics`;
CREATE TABLE `t_payment_statistics` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `stat_date`       DATE         NOT NULL                COMMENT '统计日期',
  `channel_code`    VARCHAR(50)  NOT NULL                COMMENT '支付渠道代码',
  `pay_type`        VARCHAR(50)  NOT NULL                COMMENT '支付类型',
  
  -- 统计数据
  `total_orders`    INT          DEFAULT 0               COMMENT '总订单数',
  `success_orders`  INT          DEFAULT 0               COMMENT '成功订单数',
  `failed_orders`   INT          DEFAULT 0               COMMENT '失败订单数',
  `total_amount`    DECIMAL(15,2) DEFAULT 0.00           COMMENT '总金额',
  `success_amount`  DECIMAL(15,2) DEFAULT 0.00           COMMENT '成功金额',
  `total_fee`       DECIMAL(10,2) DEFAULT 0.00           COMMENT '总手续费',
  
  -- 成功率统计
  `success_rate`    DECIMAL(5,4) DEFAULT 0.0000         COMMENT '成功率',
  `avg_amount`      DECIMAL(10,2) DEFAULT 0.00           COMMENT '平均金额',
  
  `create_time`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stat_channel_type_date` (`stat_date`, `channel_code`, `pay_type`),
  KEY `idx_date_channel` (`stat_date` DESC, `channel_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付统计表';