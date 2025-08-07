-- ==========================================
-- 内容模块简洁版 SQL
-- 基于无连表设计原则，保留核心功能
-- ==========================================

USE collide;

-- 内容主表（去连表化设计）
DROP TABLE IF EXISTS `t_content`;
CREATE TABLE `t_content` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '内容ID',
    `title`           VARCHAR(200) NOT NULL                COMMENT '内容标题',
    `description`     TEXT                                 COMMENT '内容描述',
    `content_type`    VARCHAR(50)  NOT NULL                COMMENT '内容类型：NOVEL、COMIC、VIDEO、ARTICLE、AUDIO',
    `content_data`    VARCHAR(500)                         COMMENT '内容数据URL',
    `cover_url`       VARCHAR(500)                         COMMENT '封面图片URL',
    `tags`            TEXT                                 COMMENT '标签，逗号分隔或JSON格式',
    
    -- 作者信息（冗余字段，避免连表）
    `author_id`       BIGINT       NOT NULL                COMMENT '作者用户ID',
    `author_nickname` VARCHAR(50)                          COMMENT '作者昵称（冗余）',
    `author_avatar`   VARCHAR(500)                         COMMENT '作者头像URL（冗余）',
    
    -- 分类信息（冗余字段，避免连表）
    `category_id`     BIGINT                               COMMENT '分类ID',
    `category_name`   VARCHAR(100)                         COMMENT '分类名称（冗余）',
    
    -- 状态相关字段
    `status`          VARCHAR(50)  NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT、PUBLISHED、OFFLINE',
    `review_status`   VARCHAR(50)  NOT NULL DEFAULT 'PENDING' COMMENT '审核状态：PENDING、APPROVED、REJECTED',
    
    -- 统计字段（冗余存储，避免聚合查询）
    `view_count`      BIGINT       NOT NULL DEFAULT 0     COMMENT '查看数',
    `like_count`      BIGINT       NOT NULL DEFAULT 0     COMMENT '点赞数',
    `comment_count`   BIGINT       NOT NULL DEFAULT 0     COMMENT '评论数',
    `share_count`     BIGINT       NOT NULL DEFAULT 0     COMMENT '分享数',
    `favorite_count`  BIGINT       NOT NULL DEFAULT 0     COMMENT '收藏数',
    `score_count`     BIGINT       NOT NULL DEFAULT 0     COMMENT '评分数',
    `score_total`     BIGINT       NOT NULL DEFAULT 0     COMMENT '总评分',
    
    -- 时间字段
    `publish_time`    DATETIME                             COMMENT '发布时间',
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内容主表';

-- 内容章节表（用于小说、漫画等多章节内容）
DROP TABLE IF EXISTS `t_content_chapter`;
CREATE TABLE `t_content_chapter` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '章节ID',
    `content_id`   BIGINT       NOT NULL                COMMENT '内容ID',
    `chapter_num`  INT          NOT NULL                COMMENT '章节号',
    `title`        VARCHAR(200) NOT NULL                COMMENT '章节标题',
    `content`      LONGTEXT                             COMMENT '章节内容',
    `word_count`   INT          NOT NULL DEFAULT 0     COMMENT '字数',
    `status`       VARCHAR(20)  NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT、PUBLISHED',
    `create_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_content_chapter` (`content_id`, `chapter_num`)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内容章节表';

-- 用户内容购买记录表（记录用户购买的付费内容）
DROP TABLE IF EXISTS `t_user_content_purchase`;
CREATE TABLE `t_user_content_purchase` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '购买记录ID',
    `user_id`      BIGINT       NOT NULL                COMMENT '用户ID',
    `content_id`   BIGINT       NOT NULL                COMMENT '内容ID',
    
    -- 内容信息冗余（避免连表查询）
    `content_title`     VARCHAR(200)                    COMMENT '内容标题（冗余）',
    `content_type`      VARCHAR(50)                     COMMENT '内容类型（冗余）',
    `content_cover_url` VARCHAR(500)                    COMMENT '内容封面（冗余）',
    
    -- 作者信息（保留author_id用于业务逻辑）
    `author_id`         BIGINT                          COMMENT '作者ID',
    `author_nickname`   VARCHAR(50)                     COMMENT '作者昵称（冗余）',
    
    -- 购买相关信息
    `order_id`          BIGINT                          COMMENT '关联订单ID',
    `order_no`          VARCHAR(50)                     COMMENT '订单号（冗余）',
    `coin_amount`       BIGINT       NOT NULL           COMMENT '支付金币数量',
    `original_price`    BIGINT                          COMMENT '原价金币',
    `discount_amount`   BIGINT       DEFAULT 0          COMMENT '优惠金币数量',
    
    -- 购买状态
    `status`            VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE、EXPIRED、REFUNDED',
    `purchase_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '购买时间',
    `expire_time`       DATETIME                        COMMENT '过期时间（为空表示永久有效）',
    
    -- 访问统计
    `access_count`      INT          NOT NULL DEFAULT 0 COMMENT '访问次数',
    `last_access_time`  DATETIME                        COMMENT '最后访问时间',
    
    -- 时间字段
    `create_time`       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_content` (`user_id`, `content_id`)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户内容购买记录表';

-- 内容付费配置表（记录内容的付费信息）
DROP TABLE IF EXISTS `t_content_payment`;
CREATE TABLE `t_content_payment` (
    `id`              BIGINT      NOT NULL AUTO_INCREMENT COMMENT '配置ID',
    `content_id`      BIGINT      NOT NULL                COMMENT '内容ID',
    
    -- 付费类型配置
    `payment_type`    VARCHAR(20) NOT NULL DEFAULT 'FREE' COMMENT '付费类型：FREE、COIN_PAY、VIP_FREE、TIME_LIMITED',
    `coin_price`      BIGINT      NOT NULL DEFAULT 0      COMMENT '金币价格',
    `original_price`  BIGINT                              COMMENT '原价（用于折扣显示）',
    
    -- 权限配置
    `vip_free`        TINYINT     NOT NULL DEFAULT 0      COMMENT '会员免费：0否，1是',
    `vip_only`        TINYINT     NOT NULL DEFAULT 0      COMMENT '是否只有VIP才能购买：0否，1是',
    `trial_enabled`   TINYINT     NOT NULL DEFAULT 0      COMMENT '是否支持试读：0否，1是',
    `trial_content`   TEXT                                COMMENT '试读内容',
    `trial_word_count` INT         NOT NULL DEFAULT 0     COMMENT '试读字数',
    
    -- 时效配置
    `is_permanent`    TINYINT     NOT NULL DEFAULT 1      COMMENT '是否永久有效：0否，1是',
    `valid_days`      INT                                 COMMENT '有效天数（非永久时使用）',
    
    -- 销售统计
    `total_sales`     BIGINT      NOT NULL DEFAULT 0      COMMENT '总销量',
    `total_revenue`   BIGINT      NOT NULL DEFAULT 0      COMMENT '总收入（金币）',
    
    -- 状态配置
    `status`          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE、INACTIVE',
    
    -- 时间字段
    `create_time`     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_content_id` (`content_id`)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内容付费配置表'; 