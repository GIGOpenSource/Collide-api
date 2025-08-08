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
    `ad_type`         VARCHAR(50)  NOT NULL                COMMENT '广告类型：banner、sidebar、popup、feed',
    
    -- 广告素材（核心字段）
    `image_url`       VARCHAR(1000) NOT NULL               COMMENT '广告图片URL',
    `click_url`       VARCHAR(1000) NOT NULL               COMMENT '点击跳转链接',
    
    -- 可选字段
    `alt_text`        VARCHAR(200)                         COMMENT '图片替代文本',
    `target_type`     VARCHAR(30)  NOT NULL DEFAULT '_blank' COMMENT '链接打开方式：_blank、_self',
    
    -- 状态管理
    `is_active`       TINYINT(1)   NOT NULL DEFAULT 1      COMMENT '是否启用（1启用，0禁用）',
    `sort_order`      INT          NOT NULL DEFAULT 0      COMMENT '排序权重（数值越大优先级越高）',
    
    -- 时间字段
    `create_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_ad_type` (`ad_type`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告表';