-- ========================================
-- SQL索引优化文件
-- 提升查询性能的索引配置
-- ========================================

-- ================ 用户表索引 ================

-- 用户名唯一索引（登录查询）
CREATE UNIQUE INDEX idx_users_username ON t_users(username);

-- 邮箱唯一索引（登录查询）
CREATE UNIQUE INDEX idx_users_email ON t_users(email);

-- 手机号唯一索引（登录查询）
CREATE UNIQUE INDEX idx_users_phone ON t_users(phone);

-- 用户状态索引（筛选查询）
CREATE INDEX idx_users_status ON t_users(status);

-- 用户角色索引（权限查询）
CREATE INDEX idx_users_role ON t_users(role);

-- 用户创建时间索引（排序查询）
CREATE INDEX idx_users_create_time ON t_users(create_time);

-- 用户昵称索引（搜索查询）
CREATE INDEX idx_users_nickname ON t_users(nickname);

-- 复合索引：状态+创建时间（常用查询组合）
CREATE INDEX idx_users_status_create_time ON t_users(status, create_time);

-- 复合索引：角色+状态（权限筛选）
CREATE INDEX idx_users_role_status ON t_users(role, status);

-- ================ 内容表索引 ================

-- 内容类型索引（分类查询）
CREATE INDEX idx_content_content_type ON t_content(content_type);

-- 分类ID索引（分类查询）
CREATE INDEX idx_content_category_id ON t_content(category_id);

-- 作者ID索引（作者内容查询）
CREATE INDEX idx_content_author_id ON t_content(author_id);

-- 内容状态索引（状态筛选）
CREATE INDEX idx_content_status ON t_content(status);

-- 审核状态索引（审核查询）
CREATE INDEX idx_content_review_status ON t_content(review_status);

-- 发布时间索引（时间排序）
CREATE INDEX idx_content_publish_time ON t_content(publish_time);

-- 创建时间索引（时间排序）
CREATE INDEX idx_content_create_time ON t_content(create_time);

-- 更新时间索引（时间排序）
CREATE INDEX idx_content_update_time ON t_content(update_time);

-- 浏览量索引（热门排序）
CREATE INDEX idx_content_view_count ON t_content(view_count);

-- 点赞数索引（热门排序）
CREATE INDEX idx_content_like_count ON t_content(like_count);

-- 收藏数索引（热门排序）
CREATE INDEX idx_content_favorite_count ON t_content(favorite_count);

-- 评论数索引（热门排序）
CREATE INDEX idx_content_comment_count ON t_content(comment_count);

-- 评分索引（评分排序）
CREATE INDEX idx_content_score ON t_content(score);

-- 付费状态索引（付费筛选）
CREATE INDEX idx_content_is_free ON t_content(is_free);

-- VIP免费状态索引（VIP筛选）
CREATE INDEX idx_content_is_vip_free ON t_content(is_vip_free);

-- 复合索引：状态+审核状态（常用组合）
CREATE INDEX idx_content_status_review ON t_content(status, review_status);

-- 复合索引：类型+状态（分类筛选）
CREATE INDEX idx_content_type_status ON t_content(content_type, status);

-- 复合索引：作者+状态（作者内容）
CREATE INDEX idx_content_author_status ON t_content(author_id, status);

-- 复合索引：分类+状态（分类内容）
CREATE INDEX idx_content_category_status ON t_content(category_id, status);

-- 复合索引：创建时间+状态（时间筛选）
CREATE INDEX idx_content_create_status ON t_content(create_time, status);

-- 复合索引：发布时间+状态（发布筛选）
CREATE INDEX idx_content_publish_status ON t_content(publish_time, status);

-- 复合索引：浏览量+状态（热门筛选）
CREATE INDEX idx_content_view_status ON t_content(view_count, status);

-- 复合索引：点赞数+状态（热门筛选）
CREATE INDEX idx_content_like_status ON t_content(like_count, status);

-- 复合索引：评分+状态（评分筛选）
CREATE INDEX idx_content_score_status ON t_content(score, status);

-- ================ 评论表索引 ================

-- 评论类型索引（类型筛选）
CREATE INDEX idx_comment_comment_type ON t_comment(comment_type);

-- 目标ID索引（目标查询）
CREATE INDEX idx_comment_target_id ON t_comment(target_id);

-- 父评论ID索引（层级查询）
CREATE INDEX idx_comment_parent_id ON t_comment(parent_comment_id);

-- 用户ID索引（用户评论）
CREATE INDEX idx_comment_user_id ON t_comment(user_id);

-- 回复用户ID索引（回复查询）
CREATE INDEX idx_comment_reply_user_id ON t_comment(reply_to_user_id);

-- 评论状态索引（状态筛选）
CREATE INDEX idx_comment_status ON t_comment(status);

-- 创建时间索引（时间排序）
CREATE INDEX idx_comment_create_time ON t_comment(create_time);

-- 点赞数索引（热门排序）
CREATE INDEX idx_comment_like_count ON t_comment(like_count);

-- 回复数索引（回复排序）
CREATE INDEX idx_comment_reply_count ON t_comment(reply_count);

-- 复合索引：类型+目标ID（目标评论）
CREATE INDEX idx_comment_type_target ON t_comment(comment_type, target_id);

-- 复合索引：类型+目标ID+状态（活跃评论）
CREATE INDEX idx_comment_type_target_status ON t_comment(comment_type, target_id, status);

-- 复合索引：父评论ID+状态（子评论）
CREATE INDEX idx_comment_parent_status ON t_comment(parent_comment_id, status);

-- 复合索引：用户ID+状态（用户评论）
CREATE INDEX idx_comment_user_status ON t_comment(user_id, status);

-- 复合索引：创建时间+状态（时间筛选）
CREATE INDEX idx_comment_create_status ON t_comment(create_time, status);

-- ================ 点赞表索引 ================

-- 用户ID索引（用户点赞）
CREATE INDEX idx_like_user_id ON t_like(user_id);

-- 点赞类型索引（类型筛选）
CREATE INDEX idx_like_like_type ON t_like(like_type);

-- 目标ID索引（目标点赞）
CREATE INDEX idx_like_target_id ON t_like(target_id);

-- 点赞状态索引（状态筛选）
CREATE INDEX idx_like_status ON t_like(status);

-- 创建时间索引（时间排序）
CREATE INDEX idx_like_create_time ON t_like(create_time);

-- 复合索引：用户+类型+目标（唯一性检查）
CREATE UNIQUE INDEX idx_like_user_type_target ON t_like(user_id, like_type, target_id);

-- 复合索引：类型+目标ID+状态（目标点赞统计）
CREATE INDEX idx_like_type_target_status ON t_like(like_type, target_id, status);

-- 复合索引：用户ID+状态（用户点赞）
CREATE INDEX idx_like_user_status ON t_like(user_id, status);

-- ================ 关注表索引 ================

-- 关注者ID索引（关注者查询）
CREATE INDEX idx_follow_follower_id ON t_follow(follower_id);

-- 被关注者ID索引（被关注者查询）
CREATE INDEX idx_follow_followee_id ON t_follow(followee_id);

-- 关注状态索引（状态筛选）
CREATE INDEX idx_follow_status ON t_follow(status);

-- 创建时间索引（时间排序）
CREATE INDEX idx_follow_create_time ON t_follow(create_time);

-- 复合索引：关注者+被关注者（唯一性检查）
CREATE UNIQUE INDEX idx_follow_follower_followee ON t_follow(follower_id, followee_id);

-- 复合索引：关注者+状态（关注列表）
CREATE INDEX idx_follow_follower_status ON t_follow(follower_id, status);

-- 复合索引：被关注者+状态（粉丝列表）
CREATE INDEX idx_follow_followee_status ON t_follow(followee_id, status);

-- ================ 收藏表索引 ================

-- 用户ID索引（用户收藏）
CREATE INDEX idx_favorite_user_id ON t_favorite(user_id);

-- 收藏类型索引（类型筛选）
CREATE INDEX idx_favorite_favorite_type ON t_favorite(favorite_type);

-- 目标ID索引（目标收藏）
CREATE INDEX idx_favorite_target_id ON t_favorite(target_id);

-- 收藏状态索引（状态筛选）
CREATE INDEX idx_favorite_status ON t_favorite(status);

-- 创建时间索引（时间排序）
CREATE INDEX idx_favorite_create_time ON t_favorite(create_time);

-- 复合索引：用户+类型+目标（唯一性检查）
CREATE UNIQUE INDEX idx_favorite_user_type_target ON t_favorite(user_id, favorite_type, target_id);

-- 复合索引：类型+目标ID+状态（目标收藏统计）
CREATE INDEX idx_favorite_type_target_status ON t_favorite(favorite_type, target_id, status);

-- 复合索引：用户ID+状态（用户收藏）
CREATE INDEX idx_favorite_user_status ON t_favorite(user_id, status);

-- ================ 商品表索引 ================

-- 商品类型索引（类型筛选）
CREATE INDEX idx_goods_goods_type ON t_goods(goods_type);

-- 分类ID索引（分类查询）
CREATE INDEX idx_goods_category_id ON t_goods(category_id);

-- 商家ID索引（商家商品）
CREATE INDEX idx_goods_seller_id ON t_goods(seller_id);

-- 商品状态索引（状态筛选）
CREATE INDEX idx_goods_status ON t_goods(status);

-- 创建时间索引（时间排序）
CREATE INDEX idx_goods_create_time ON t_goods(create_time);

-- 更新时间索引（时间排序）
CREATE INDEX idx_goods_update_time ON t_goods(update_time);

-- 销量索引（销量排序）
CREATE INDEX idx_goods_sales_count ON t_goods(sales_count);

-- 查看数索引（热度排序）
CREATE INDEX idx_goods_view_count ON t_goods(view_count);

-- 价格索引（价格筛选）
CREATE INDEX idx_goods_price ON t_goods(price);

-- 金币价格索引（金币筛选）
CREATE INDEX idx_goods_coin_price ON t_goods(coin_price);

-- 内容ID索引（内容商品）
CREATE INDEX idx_goods_content_id ON t_goods(content_id);

-- 复合索引：类型+状态（类型筛选）
CREATE INDEX idx_goods_type_status ON t_goods(goods_type, status);

-- 复合索引：分类+状态（分类筛选）
CREATE INDEX idx_goods_category_status ON t_goods(category_id, status);

-- 复合索引：商家+状态（商家商品）
CREATE INDEX idx_goods_seller_status ON t_goods(seller_id, status);

-- 复合索引：创建时间+状态（时间筛选）
CREATE INDEX idx_goods_create_status ON t_goods(create_time, status);

-- 复合索引：销量+状态（热门筛选）
CREATE INDEX idx_goods_sales_status ON t_goods(sales_count, status);

-- 复合索引：价格+状态（价格筛选）
CREATE INDEX idx_goods_price_status ON t_goods(price, status);

-- ================ 任务表索引 ================

-- 任务模板索引
CREATE INDEX idx_task_template_task_type ON t_task_template(task_type);
CREATE INDEX idx_task_template_task_action ON t_task_template(task_action);
CREATE INDEX idx_task_template_is_active ON t_task_template(is_active);
CREATE INDEX idx_task_template_create_time ON t_task_template(create_time);

-- 用户任务记录索引
CREATE INDEX idx_user_task_record_user_id ON t_user_task_record(user_id);
CREATE INDEX idx_user_task_record_task_id ON t_user_task_record(task_id);
CREATE INDEX idx_user_task_record_task_date ON t_user_task_record(task_date);
CREATE INDEX idx_user_task_record_is_completed ON t_user_task_record(is_completed);
CREATE INDEX idx_user_task_record_user_task_date ON t_user_task_record(user_id, task_date);

-- 用户奖励记录索引
CREATE INDEX idx_user_reward_record_user_id ON t_user_reward_record(user_id);
CREATE INDEX idx_user_reward_record_task_record_id ON t_user_reward_record(task_record_id);
CREATE INDEX idx_user_reward_record_reward_date ON t_user_reward_record(reward_date);

-- ================ 消息表索引 ================

-- 消息表索引
CREATE INDEX idx_message_sender_id ON t_message(sender_id);
CREATE INDEX idx_message_receiver_id ON t_message(receiver_id);
CREATE INDEX idx_message_message_type ON t_message(message_type);
CREATE INDEX idx_message_status ON t_message(status);
CREATE INDEX idx_message_create_time ON t_message(create_time);
CREATE INDEX idx_message_sender_receiver ON t_message(sender_id, receiver_id);
CREATE INDEX idx_message_receiver_status ON t_message(receiver_id, status);

-- 消息会话表索引
CREATE INDEX idx_message_session_user_id ON t_message_session(user_id);
CREATE INDEX idx_message_session_other_user_id ON t_message_session(other_user_id);
CREATE INDEX idx_message_session_last_message_time ON t_message_session(last_message_time);

-- ================ 搜索表索引 ================

-- 搜索历史表索引
CREATE INDEX idx_search_history_user_id ON t_search_history(user_id);
CREATE INDEX idx_search_history_keyword ON t_search_history(keyword);
CREATE INDEX idx_search_history_search_type ON t_search_history(search_type);
CREATE INDEX idx_search_history_create_time ON t_search_history(create_time);
CREATE INDEX idx_search_history_user_time ON t_search_history(user_id, create_time);

-- 热搜表索引
CREATE INDEX idx_hot_search_keyword ON t_hot_search(keyword);
CREATE INDEX idx_hot_search_search_count ON t_hot_search(search_count);
CREATE INDEX idx_hot_search_create_time ON t_hot_search(create_time);

-- ================ 标签表索引 ================

-- 标签表索引
CREATE INDEX idx_tag_tag_type ON t_tag(tag_type);
CREATE INDEX idx_tag_usage_count ON t_tag(usage_count);
CREATE INDEX idx_tag_create_time ON t_tag(create_time);

-- 用户兴趣标签表索引
CREATE INDEX idx_user_interest_tag_user_id ON t_user_interest_tag(user_id);
CREATE INDEX idx_user_interest_tag_tag_id ON t_user_interest_tag(tag_id);
CREATE INDEX idx_user_interest_tag_interest_score ON t_user_interest_tag(interest_score);
CREATE INDEX idx_user_interest_tag_user_tag ON t_user_interest_tag(user_id, tag_id);

-- 内容标签表索引
CREATE INDEX idx_content_tag_content_id ON t_content_tag(content_id);
CREATE INDEX idx_content_tag_tag_id ON t_content_tag(tag_id);
CREATE INDEX idx_content_tag_content_tag ON t_content_tag(content_id, tag_id);

-- ================ 广告表索引 ================

-- 广告表索引
CREATE INDEX idx_ad_ad_type ON t_ad(ad_type);
CREATE INDEX idx_ad_target_type ON t_ad(target_type);
CREATE INDEX idx_ad_is_active ON t_ad(is_active);
CREATE INDEX idx_ad_sort_order ON t_ad(sort_order);
CREATE INDEX idx_ad_create_time ON t_ad(create_time);
CREATE INDEX idx_ad_type_active ON t_ad(ad_type, is_active);

-- ================ 章节表索引 ================

-- 章节表索引
CREATE INDEX idx_chapter_content_id ON t_chapter(content_id);
CREATE INDEX idx_chapter_chapter_num ON t_chapter(chapter_num);
CREATE INDEX idx_chapter_status ON t_chapter(status);
CREATE INDEX idx_chapter_create_time ON t_chapter(create_time);
CREATE INDEX idx_chapter_content_num ON t_chapter(content_id, chapter_num);
CREATE INDEX idx_chapter_content_status ON t_chapter(content_id, status);

-- ================ 付费配置表索引 ================

-- 内容付费配置表索引
CREATE INDEX idx_content_payment_content_id ON t_content_payment(content_id);
CREATE INDEX idx_content_payment_payment_type ON t_content_payment(payment_type);
CREATE INDEX idx_content_payment_content_type ON t_content_payment(content_id, payment_type);

-- 用户内容购买记录表索引
CREATE INDEX idx_user_content_purchase_user_id ON t_user_content_purchase(user_id);
CREATE INDEX idx_user_content_purchase_content_id ON t_user_content_purchase(content_id);
CREATE INDEX idx_user_content_purchase_status ON t_user_content_purchase(status);
CREATE INDEX idx_user_content_purchase_purchase_time ON t_user_content_purchase(purchase_time);
CREATE INDEX idx_user_content_purchase_user_content ON t_user_content_purchase(user_id, content_id);

-- ================ 分类表索引 ================

-- 分类表索引
CREATE INDEX idx_category_parent_id ON t_category(parent_id);
CREATE INDEX idx_category_category_type ON t_category(category_type);
CREATE INDEX idx_category_sort_order ON t_category(sort_order);
CREATE INDEX idx_category_is_active ON t_category(is_active);
CREATE INDEX idx_category_create_time ON t_category(create_time);
CREATE INDEX idx_category_parent_active ON t_category(parent_id, is_active);

-- ================ 社交动态表索引 ================

-- 社交动态表索引
CREATE INDEX idx_social_dynamic_user_id ON t_social_dynamic(user_id);
CREATE INDEX idx_social_dynamic_dynamic_type ON t_social_dynamic(dynamic_type);
CREATE INDEX idx_social_dynamic_status ON t_social_dynamic(status);
CREATE INDEX idx_social_dynamic_create_time ON t_social_dynamic(create_time);
CREATE INDEX idx_social_dynamic_like_count ON t_social_dynamic(like_count);
CREATE INDEX idx_social_dynamic_comment_count ON t_social_dynamic(comment_count);
CREATE INDEX idx_social_dynamic_user_status ON t_social_dynamic(user_id, status);
CREATE INDEX idx_social_dynamic_type_status ON t_social_dynamic(dynamic_type, status);

-- ========================================
-- 索引优化说明
-- ========================================

/*
索引优化策略：

1. **单列索引**：
   - 主键自动创建唯一索引
   - 外键建议创建索引
   - 经常用于WHERE条件的字段
   - 经常用于ORDER BY的字段

2. **复合索引**：
   - 多字段组合查询
   - 遵循最左前缀原则
   - 考虑查询频率和选择性

3. **唯一索引**：
   - 用户名、邮箱、手机号等唯一字段
   - 业务逻辑唯一约束

4. **覆盖索引**：
   - 包含查询所需的所有字段
   - 减少回表查询

5. **索引选择**：
   - 高选择性字段优先
   - 考虑数据分布
   - 避免过多索引影响写入性能

6. **维护建议**：
   - 定期分析索引使用情况
   - 删除未使用的索引
   - 监控索引大小和性能
*/ 