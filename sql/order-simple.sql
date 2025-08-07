-- ==========================================
-- 订单模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 订单主表（去连表化设计，支持四种商品类型和双支付模式）
DROP TABLE IF EXISTS `t_order`;
CREATE TABLE `t_order` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_no`     VARCHAR(50)  NOT NULL                COMMENT '订单号',
  `user_id`      BIGINT       NOT NULL                COMMENT '用户ID',
  `user_nickname` VARCHAR(100)                        COMMENT '用户昵称（冗余）',
  
  -- 商品信息（冗余字段，避免连表）
  `goods_id`     BIGINT       NOT NULL                COMMENT '商品ID',
  `goods_name`   VARCHAR(200)                         COMMENT '商品名称（冗余）',
  `goods_type`   VARCHAR(20)  NOT NULL                COMMENT '商品类型：coin、goods、subscription、content',
  `goods_cover`  VARCHAR(500)                         COMMENT '商品封面（冗余）',
  `goods_category_name` VARCHAR(100)                  COMMENT '商品分类名称（冗余）',
  
  -- 商品特殊信息（根据类型使用）
  `coin_amount`  BIGINT                               COMMENT '金币数量（金币类商品：购买后获得金币数）',
  `content_id`   BIGINT                               COMMENT '内容ID（内容类商品）',
  `content_title` VARCHAR(200)                        COMMENT '内容标题（内容类商品冗余）',
  `subscription_duration` INT                         COMMENT '订阅时长天数（订阅类商品）',
  `subscription_type` VARCHAR(50)                     COMMENT '订阅类型（订阅类商品）',
  
  `quantity`     INT          NOT NULL DEFAULT 1     COMMENT '购买数量',
  
  -- 双支付模式：现金支付 vs 金币支付
  `payment_mode` VARCHAR(20)  NOT NULL                COMMENT '支付模式：cash-现金支付、coin-金币支付',
  `cash_amount`  DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '现金金额（现金支付时使用）',
  `coin_cost`    BIGINT       NOT NULL DEFAULT 0     COMMENT '消耗金币数（金币支付时使用）',
  `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '订单总金额（现金）',
  `discount_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '优惠金额',
  `final_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '实付金额（现金）',
  
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT '订单状态：pending、paid、shipped、completed、cancelled',
  `pay_status`   VARCHAR(20)  NOT NULL DEFAULT 'unpaid' COMMENT '支付状态：unpaid、paid、refunded',
  `pay_method`   VARCHAR(20)                          COMMENT '支付方式：alipay、wechat、balance、coin',
  `pay_time`     DATETIME                             COMMENT '支付时间',
  
  `create_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_goods_id` (`goods_id`),
  KEY `idx_goods_type` (`goods_type`),
  KEY `idx_payment_mode` (`payment_mode`),
  KEY `idx_status` (`status`),
  KEY `idx_pay_status` (`pay_status`),
  KEY `idx_content_id` (`content_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单主表（支持四种商品类型和双支付模式）';