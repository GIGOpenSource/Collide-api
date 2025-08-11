-- ==========================================
-- Collide 广告系统 - 极简版
-- 只保留核心功能：广告类型 + 图片 + 链接
-- 设计原则：简洁、实用、易维护
-- ==========================================

USE collide;

-- ==========================================
-- 广告表（唯一核心表）
-- ==========================================

-- 广告表（存储广告的核心信息）
DROP TABLE IF EXISTS `t_ad`;
CREATE TABLE `t_ad` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '广告ID',
    `ad_name`         VARCHAR(200) NOT NULL                COMMENT '广告名称',
    `ad_title`        VARCHAR(300) NOT NULL                COMMENT '广告标题',
    `ad_description`  VARCHAR(500)                         COMMENT '广告描述',
    
    -- 广告类型（核心字段）
    `ad_type`         VARCHAR(50)  NOT NULL                COMMENT '广告类型：banner、sidebar、popup、feed、game',
    
    -- 广告素材（核心字段）
    `image_url`       VARCHAR(1000) NOT NULL               COMMENT '广告图片URL',
    `click_url`       VARCHAR(1000) NOT NULL               COMMENT '点击跳转链接',
    
    -- 可选字段
    `alt_text`        VARCHAR(200)                         COMMENT '图片替代文本',
    `target_type`     VARCHAR(30)  NOT NULL DEFAULT '_blank' COMMENT '链接打开方式：_blank、_self',
    
    -- 游戏广告专用字段
    `game_intro`      TEXT                                 COMMENT '游戏简介',
    `game_detail`     LONGTEXT                             COMMENT '游戏详情（支持富文本）',
    `game_company`    VARCHAR(200)                         COMMENT '游戏公司名字',
    `game_type`       VARCHAR(100)                         COMMENT '游戏类型（如：RPG、MOBA、卡牌等，多个类型用逗号分隔）',
    `game_rating`     DECIMAL(2,1)                         COMMENT '游戏评分（0.0-5.0）',
    `game_size`       VARCHAR(50)                          COMMENT '游戏大小（如：1.2GB）',
    `game_version`    VARCHAR(50)                          COMMENT '游戏版本号',
    `game_platform`   VARCHAR(100)                         COMMENT '游戏平台（如：iOS、Android、PC，多个平台用逗号分隔）',
    `game_tags`       VARCHAR(500)                         COMMENT '游戏标签（多个标签用逗号分隔）',
    `game_download_count` BIGINT DEFAULT 0                COMMENT '游戏下载次数',
    `game_rating_count` BIGINT DEFAULT 0                   COMMENT '游戏评分人数',
    
    -- 下载相关字段
    `is_free_download` TINYINT(1)  NOT NULL DEFAULT 1      COMMENT '是否支持普通用户免费下载（1是，0否）',
    `is_vip_download`  TINYINT(1)  NOT NULL DEFAULT 0      COMMENT '是否支持VIP免费下载（1是，0否）',
    `is_coin_download` TINYINT(1)  NOT NULL DEFAULT 0      COMMENT '是否支持金币购买下载（1是，0否）',
    `coin_price`       BIGINT      DEFAULT 0               COMMENT '金币价格（当支持金币购买时）',
    `original_coin_price` BIGINT   DEFAULT 0               COMMENT '原价金币（用于折扣显示）',
    `download_url`     VARCHAR(1000)                       COMMENT '下载链接',
    `download_platform` VARCHAR(100)                       COMMENT '下载平台（如：App Store、Google Play、官网等，多个平台用逗号分隔）',
    `download_size`    VARCHAR(50)                         COMMENT '下载包大小（如：1.2GB）',
    `download_version` VARCHAR(50)                         COMMENT '下载版本号',
    `download_requirements` TEXT                           COMMENT '下载要求（如：系统版本、内存要求等）',
    
    -- 状态管理
    `is_active`       TINYINT(1)   NOT NULL DEFAULT 1      COMMENT '是否启用（1启用，0禁用）',
    `sort_order`      INT          NOT NULL DEFAULT 0      COMMENT '排序权重（数值越大优先级越高）',
    
    -- 时间字段
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_ad_type` (`ad_type`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_sort_order` (`sort_order`),
    KEY `idx_game_type` (`game_type`),
    KEY `idx_game_company` (`game_company`),
    KEY `idx_game_rating` (`game_rating`),
    KEY `idx_is_free_download` (`is_free_download`),
    KEY `idx_is_vip_download` (`is_vip_download`),
    KEY `idx_is_coin_download` (`is_coin_download`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告表';

-- ==========================================
-- 游戏图片表（存储游戏的多张图片）
-- ==========================================

-- 游戏图片表
DROP TABLE IF EXISTS `t_game_image`;
CREATE TABLE `t_game_image` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '图片ID',
    `ad_id`           BIGINT       NOT NULL                COMMENT '关联的广告ID',
    `image_url`       VARCHAR(1000) NOT NULL               COMMENT '图片URL',
    `image_type`      VARCHAR(50)                  COMMENT '图片类型：cover（封面）、banner（横幅）、screenshot（截图）、icon（图标）',
    `image_title`     VARCHAR(200)                         COMMENT '图片标题',
    `image_description` VARCHAR(500)                       COMMENT '图片描述',
    `alt_text`        VARCHAR(200)                         COMMENT '图片替代文本',
    `sort_order`      INT          NOT NULL DEFAULT 0      COMMENT '排序权重（数值越大优先级越高）',
    `is_active`       TINYINT(1)   NOT NULL DEFAULT 1      COMMENT '是否启用（1启用，0禁用）',
    
    -- 时间字段
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_ad_id` (`ad_id`),
    KEY `idx_image_type` (`image_type`),
    KEY `idx_sort_order` (`sort_order`),
    KEY `idx_is_active` (`is_active`),
    FOREIGN KEY (`ad_id`) REFERENCES `t_ad`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='游戏图片表';