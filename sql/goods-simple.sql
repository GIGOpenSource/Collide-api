-- ==========================================
-- 商品模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 商品主表（去连表化设计，支持四种商品类型）
DROP TABLE IF EXISTS `t_goods`;
CREATE TABLE `t_goods`
(
    `id`             BIGINT         NOT NULL AUTO_INCREMENT COMMENT '商品ID',
    `name`           VARCHAR(200)   NOT NULL COMMENT '商品名称',
    `description`    TEXT NULL COMMENT '商品描述',
    `category_id`    BIGINT         NOT NULL COMMENT '分类ID',
    `category_name`  VARCHAR(100) NULL COMMENT '分类名称（冗余）',
    
    -- 商品类型和定价策略
    `goods_type`     VARCHAR(20)    NOT NULL COMMENT '商品类型：coin-金币、goods-商品、subscription-订阅、content-内容',
    `price`          DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '现金价格（内容类型为0）',
    `original_price` DECIMAL(10, 2) NULL COMMENT '原价',
    `coin_price`     BIGINT         NOT NULL DEFAULT 0 COMMENT '金币价格（内容类型专用，其他类型为0）',
    `coin_amount`    BIGINT         NULL COMMENT '金币数量（仅金币类商品：购买后获得的金币数）',
    
    -- 特殊字段
    `content_id`     BIGINT         NULL COMMENT '关联内容ID（仅内容类型有效）',
    `content_title`  VARCHAR(200)   NULL COMMENT '内容标题（冗余，仅内容类型）',
    `subscription_duration` INT     NULL COMMENT '订阅时长（天数，仅订阅类型有效）',
    `subscription_type` VARCHAR(50) NULL COMMENT '订阅类型（VIP、PREMIUM等，仅订阅类型有效）',
    
    `stock`          INT            NOT NULL DEFAULT -1 COMMENT '库存数量（-1表示无限库存，适用于虚拟商品）',
    `cover_url`      VARCHAR(500) NULL COMMENT '商品封面图',
    `images`         TEXT NULL COMMENT '商品图片，JSON数组格式',

    -- 商家信息（冗余字段，避免连表）
    `seller_id`      BIGINT         NOT NULL COMMENT '商家ID',
    `seller_name`    VARCHAR(100)   NOT NULL COMMENT '商家名称（冗余）',

    -- 状态和统计
    `status`         VARCHAR(20)    NOT NULL DEFAULT 'active' COMMENT '状态：active、inactive、sold_out',
    `sales_count`    BIGINT         NOT NULL DEFAULT 0 COMMENT '销量（冗余统计）',
    `view_count`     BIGINT         NOT NULL DEFAULT 0 COMMENT '查看数（冗余统计）',

    `create_time`    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    -- 注意：详细的索引设计请参考 goods-indexes-mysql8.4.sql
    -- 这里保留基础索引，生产环境请执行索引优化文件
    KEY `idx_goods_type` (`goods_type`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_seller_id` (`seller_id`),
    KEY `idx_status` (`status`),
    KEY `idx_content_id` (`content_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='商品主表（支持金币、商品、订阅、内容四种类型）';