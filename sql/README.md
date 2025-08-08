# SQL索引优化文档

## 概述

本文档介绍了Collide API项目的数据库索引优化策略，包括索引设计、创建、维护和监控。

## 索引文件说明

### `indexes.sql`
包含所有表的索引创建语句，按模块分类：

- **用户表索引**: 用户名、邮箱、手机号唯一索引，状态、角色等查询索引
- **内容表索引**: 类型、分类、作者、状态等复合索引
- **评论表索引**: 类型+目标ID、用户ID、父评论ID等索引
- **点赞表索引**: 用户+类型+目标唯一索引
- **关注表索引**: 关注者+被关注者唯一索引
- **收藏表索引**: 用户+类型+目标唯一索引
- **商品表索引**: 类型、分类、价格、销量等索引
- **其他模块索引**: 任务、消息、搜索、标签、广告等

## 索引优化策略

### 1. 单列索引
- **主键索引**: 自动创建，用于唯一标识
- **外键索引**: 提升关联查询性能
- **查询字段索引**: 经常用于WHERE条件的字段
- **排序字段索引**: 经常用于ORDER BY的字段

### 2. 复合索引
- **多字段查询**: 支持多条件组合查询
- **最左前缀**: 遵循MySQL最左前缀原则
- **选择性优先**: 高选择性字段放在前面

### 3. 唯一索引
- **业务唯一性**: 用户名、邮箱、手机号等
- **数据完整性**: 防止重复数据插入

### 4. 覆盖索引
- **减少回表**: 包含查询所需的所有字段
- **提升性能**: 避免额外的数据页访问

## 索引维护工具

### 1. 索引分析器 (`scripts/index_analyzer.py`)

**功能**:
- 分析表结构和索引使用情况
- 检测未使用的索引
- 识别缺失的索引
- 生成优化建议报告

**使用方法**:
```bash
# 运行分析
python3 scripts/index_analyzer.py

# 导出报告
python3 scripts/index_analyzer.py --export report.json
```

**输出示例**:
```
============================================================
数据库索引分析报告
============================================================
分析时间: 2024-01-15T10:30:00
总表数: 15
总索引数: 89
数据大小: 256.45 MB
索引大小: 45.67 MB

表分析结果:
------------------------------------------------------------
t_users:
  索引数: 8
  未使用索引: 1
  缺失索引: 0
  性能评分: 85/100

优化建议:
------------------------------------------------------------
1. 发现 3 个未使用的索引，建议删除以提升写入性能
2. 发现 2 个缺失的索引，建议添加以提升查询性能
3. 表 t_content 数据量较大 (150000 行)，建议定期维护索引
```

### 2. 索引维护器 (`scripts/index_maintenance.py`)

**功能**:
- 批量创建索引
- 删除未使用的索引
- 优化表结构
- 分析表统计信息

**使用方法**:
```bash
# 创建索引
python3 scripts/index_maintenance.py --action create --file sql/indexes.sql

# 删除未使用的索引
python3 scripts/index_maintenance.py --action drop --drop-unused

# 优化指定表
python3 scripts/index_maintenance.py --action optimize --tables t_users t_content

# 分析表统计信息
python3 scripts/index_maintenance.py --action analyze --tables t_users t_content

# 查看索引状态
python3 scripts/index_maintenance.py --action status
```

## 性能监控

### 1. 慢查询监控
```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

### 2. 索引使用统计
```sql
-- 查看索引使用情况
SELECT 
    OBJECT_NAME as table_name,
    INDEX_NAME as index_name,
    COUNT_FETCH,
    COUNT_INSERT,
    COUNT_UPDATE,
    COUNT_DELETE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA = 'collide_db'
ORDER BY COUNT_FETCH DESC;
```

### 3. 表性能分析
```sql
-- 查看表大小和索引信息
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH,
    (DATA_LENGTH + INDEX_LENGTH) as TOTAL_SIZE
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'collide_db'
ORDER BY TOTAL_SIZE DESC;
```

## 最佳实践

### 1. 索引设计原则
- **选择性**: 高选择性字段优先
- **查询模式**: 基于实际查询需求设计
- **数据分布**: 考虑数据的分布特征
- **维护成本**: 平衡查询性能和写入性能

### 2. 索引维护策略
- **定期分析**: 每周运行索引分析
- **监控使用**: 关注索引使用统计
- **清理无用**: 删除未使用的索引
- **优化表**: 定期执行OPTIMIZE TABLE

### 3. 性能优化建议
- **避免过多索引**: 影响写入性能
- **合理使用复合索引**: 减少索引数量
- **监控慢查询**: 及时发现问题
- **定期维护**: 保持索引效率

## 常见问题

### 1. 索引创建失败
**原因**: 索引已存在或语法错误
**解决**: 检查索引是否存在，修正SQL语法

### 2. 查询性能下降
**原因**: 索引失效或统计信息过期
**解决**: 重新分析表统计信息，检查索引使用情况

### 3. 写入性能下降
**原因**: 索引过多或索引设计不合理
**解决**: 删除未使用的索引，优化索引结构

## 监控脚本

### 定期维护脚本
```bash
#!/bin/bash
# 每周执行的索引维护脚本

# 1. 分析索引使用情况
python3 scripts/index_analyzer.py

# 2. 删除未使用的索引
python3 scripts/index_maintenance.py --action drop --drop-unused

# 3. 优化大表
python3 scripts/index_maintenance.py --action optimize --tables t_content t_users

# 4. 分析表统计信息
python3 scripts/index_maintenance.py --action analyze
```

## 总结

通过合理的索引设计和维护，可以显著提升数据库查询性能。建议：

1. **定期监控**: 使用提供的工具定期分析索引使用情况
2. **及时优化**: 根据分析结果及时调整索引结构
3. **性能测试**: 在索引变更后进行性能测试
4. **文档维护**: 保持索引设计文档的更新

通过以上策略，可以确保数据库在数据量增长的同时保持良好的查询性能。 