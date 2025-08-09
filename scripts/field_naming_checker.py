#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collide API 数据库字段命名检查器
用于检查所有SQL文件中的字段命名是否符合规范
"""

import os
import re
import glob
from typing import Dict, List, Tuple, Set

class FieldNamingChecker:
    def __init__(self):
        # 字段命名规范定义
        self.field_patterns = {
            # 基础字段
            'id': r'`id`\s+BIGINT\s+NOT NULL AUTO_INCREMENT',
            'create_time': r'`create_time`\s+TIMESTAMP\s+NOT NULL DEFAULT CURRENT_TIMESTAMP',
            'update_time': r'`update_time`\s+TIMESTAMP\s+NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            'status': r'`status`\s+VARCHAR\([0-9]+\)\s+NOT NULL',
            
            # 用户相关字段
            'user_id': r'`user_id`\s+BIGINT',
            'user_nickname': r'`user_nickname`\s+VARCHAR\([0-9]+\)',
            'user_avatar': r'`user_avatar`\s+VARCHAR\([0-9]+\)',
            'user_username': r'`user_username`\s+VARCHAR\([0-9]+\)',
            
            # 内容相关字段
            'content_id': r'`content_id`\s+BIGINT',
            'content_title': r'`content_title`\s+VARCHAR\([0-9]+\)',
            'content_type': r'`content_type`\s+VARCHAR\([0-9]+\)',
            'content_cover_url': r'`content_cover_url`\s+VARCHAR\([0-9]+\)',
            
            # 作者相关字段
            'author_id': r'`author_id`\s+BIGINT',
            'author_nickname': r'`author_nickname`\s+VARCHAR\([0-9]+\)',
            'author_avatar': r'`author_avatar`\s+VARCHAR\([0-9]+\)',
            
            # 分类相关字段
            'category_id': r'`category_id`\s+BIGINT',
            'category_name': r'`category_name`\s+VARCHAR\([0-9]+\)',
            
            # 统计字段
            'view_count': r'`view_count`\s+BIGINT',
            'like_count': r'`like_count`\s+BIGINT',
            'comment_count': r'`comment_count`\s+BIGINT',
            'share_count': r'`share_count`\s+BIGINT',
            'favorite_count': r'`favorite_count`\s+BIGINT',
            'reply_count': r'`reply_count`\s+INT',
            'follower_count': r'`follower_count`\s+BIGINT',
            'following_count': r'`following_count`\s+BIGINT',
            'content_count': r'`content_count`\s+BIGINT',
            'sales_count': r'`sales_count`\s+BIGINT',
            'access_count': r'`access_count`\s+INT',
            
            # 评分相关字段
            'score_count': r'`score_count`\s+BIGINT',
            'score_total': r'`score_total`\s+BIGINT',
            
            # 价格相关字段
            'price': r'`price`\s+DECIMAL\([0-9,]+\)',
            'original_price': r'`original_price`\s+DECIMAL\([0-9,]+\)',
            'coin_price': r'`coin_price`\s+BIGINT',
            'coin_amount': r'`coin_amount`\s+BIGINT',
            'discount_amount': r'`discount_amount`\s+BIGINT',
            
            # 关系字段
            'follower_id': r'`follower_id`\s+BIGINT',
            'followee_id': r'`followee_id`\s+BIGINT',
            'follower_nickname': r'`follower_nickname`\s+VARCHAR\([0-9]+\)',
            'followee_nickname': r'`followee_nickname`\s+VARCHAR\([0-9]+\)',
            'like_type': r'`like_type`\s+VARCHAR\([0-9]+\)',
            'target_id': r'`target_id`\s+BIGINT',
            'target_title': r'`target_title`\s+VARCHAR\([0-9]+\)',
            'target_author_id': r'`target_author_id`\s+BIGINT',
            'comment_type': r'`comment_type`\s+VARCHAR\([0-9]+\)',
            'parent_comment_id': r'`parent_comment_id`\s+BIGINT',
            'reply_to_user_id': r'`reply_to_user_id`\s+BIGINT',
            'reply_to_user_nickname': r'`reply_to_user_nickname`\s+VARCHAR\([0-9]+\)',
            
            # 消息相关字段
            'sender_id': r'`sender_id`\s+BIGINT',
            'receiver_id': r'`receiver_id`\s+BIGINT',
            'message_type': r'`message_type`\s+VARCHAR\([0-9]+\)',
            'reply_to_id': r'`reply_to_id`\s+BIGINT',
            
            # 任务相关字段
            'task_id': r'`task_id`\s+BIGINT',
            'task_name': r'`task_name`\s+VARCHAR\([0-9]+\)',
            'task_type': r'`task_type`\s+TINYINT',
            'task_category': r'`task_category`\s+TINYINT',
            'task_action': r'`task_action`\s+TINYINT',
            'task_date': r'`task_date`\s+DATE',
            'target_count': r'`target_count`\s+INT',
            'current_count': r'`current_count`\s+INT',
            
            # 奖励相关字段
            'reward_type': r'`reward_type`\s+TINYINT',
            'reward_name': r'`reward_name`\s+VARCHAR\([0-9]+\)',
            'reward_amount': r'`reward_amount`\s+INT',
            'reward_source': r'`reward_source`\s+TINYINT',
            
            # 商品相关字段
            'goods_type': r'`goods_type`\s+VARCHAR\([0-9]+\)',
            'seller_id': r'`seller_id`\s+BIGINT',
            'seller_name': r'`seller_name`\s+VARCHAR\([0-9]+\)',
            'stock': r'`stock`\s+INT',
            
            # 订单相关字段
            'order_id': r'`order_id`\s+BIGINT',
            'order_no': r'`order_no`\s+VARCHAR\([0-9]+\)',
            
            # 时间相关字段
            'publish_time': r'`publish_time`\s+DATETIME',
            'read_time': r'`read_time`\s+TIMESTAMP',
            'complete_time': r'`complete_time`\s+TIMESTAMP',
            'reward_time': r'`reward_time`\s+TIMESTAMP',
            'grant_time': r'`grant_time`\s+TIMESTAMP',
            'expire_time': r'`expire_time`\s+TIMESTAMP',
            'last_login_time': r'`last_login_time`\s+DATETIME',
            'last_access_time': r'`last_access_time`\s+DATETIME',
            'last_message_time': r'`last_message_time`\s+TIMESTAMP',
        }
        
        # 索引命名规范
        self.index_patterns = {
            'unique_key': r'UNIQUE KEY `uk_[a-z_]+`',
            'index': r'KEY `idx_[a-z_]+`',
        }
        
        # 表命名规范
        self.table_pattern = r'CREATE TABLE `t_[a-z_]+`'
        
    def check_sql_file(self, file_path: str) -> Dict:
        """检查单个SQL文件的字段命名规范"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        results = {
            'file': file_path,
            'tables': [],
            'issues': [],
            'warnings': [],
            'passed': True
        }
        
        # 检查表命名
        tables = re.findall(r'CREATE TABLE `([^`]+)`', content)
        for table in tables:
            if not table.startswith('t_'):
                results['issues'].append(f"表名 '{table}' 不符合 t_ 前缀规范")
                results['passed'] = False
            else:
                results['tables'].append(table)
        
        # 检查字段命名
        for field_name, pattern in self.field_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if not matches:
                # 检查是否有类似字段但命名不规范
                similar_fields = re.findall(rf'`[a-z_]*{field_name.split("_")[-1]}[a-z_]*`\s+[A-Z]+', content, re.IGNORECASE)
                if similar_fields:
                    results['warnings'].append(f"发现类似字段但命名可能不规范: {similar_fields}")
        
        # 检查索引命名
        for index_type, pattern in self.index_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if not matches:
                # 检查是否有索引但命名不规范
                all_indexes = re.findall(r'(UNIQUE KEY|KEY)\s+`[^`]+`', content)
                for index in all_indexes:
                    if not re.search(r'`(uk_|idx_)[a-z_]+`', index):
                        results['warnings'].append(f"索引命名可能不规范: {index}")
        
        # 检查必需字段
        required_fields = ['id', 'create_time', 'update_time']
        for field in required_fields:
            if field == 'create_time':
                # 更宽松的create_time检查
                if not re.search(r'`create_time`\s+TIMESTAMP', content, re.IGNORECASE):
                    results['issues'].append(f"缺少必需字段: {field}")
                    results['passed'] = False
            elif field == 'update_time':
                # 更宽松的update_time检查
                if not re.search(r'`update_time`\s+TIMESTAMP', content, re.IGNORECASE):
                    results['issues'].append(f"缺少必需字段: {field}")
                    results['passed'] = False
            else:
                if not re.search(self.field_patterns[field], content, re.IGNORECASE):
                    results['issues'].append(f"缺少必需字段: {field}")
                    results['passed'] = False
        
        return results
    
    def check_all_sql_files(self, sql_dir: str = 'sql') -> List[Dict]:
        """检查所有SQL文件"""
        sql_files = glob.glob(os.path.join(sql_dir, '*.sql'))
        results = []
        
        for sql_file in sql_files:
            if 'simple' in sql_file:  # 只检查simple版本的文件
                result = self.check_sql_file(sql_file)
                results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成检查报告"""
        report = []
        report.append("# Collide API 数据库字段命名检查报告\n")
        
        total_files = len(results)
        passed_files = sum(1 for r in results if r['passed'])
        failed_files = total_files - passed_files
        
        report.append(f"## 总体统计\n")
        report.append(f"- 检查文件数: {total_files}")
        report.append(f"- 通过文件数: {passed_files}")
        report.append(f"- 失败文件数: {failed_files}")
        report.append(f"- 通过率: {passed_files/total_files*100:.1f}%\n")
        
        # 详细结果
        for result in results:
            report.append(f"## {os.path.basename(result['file'])}\n")
            
            if result['tables']:
                report.append(f"**发现的表:** {', '.join(result['tables'])}\n")
            
            if result['issues']:
                report.append("**问题:**")
                for issue in result['issues']:
                    report.append(f"- ❌ {issue}")
                report.append("")
            
            if result['warnings']:
                report.append("**警告:**")
                for warning in result['warnings']:
                    report.append(f"- ⚠️ {warning}")
                report.append("")
            
            if not result['issues'] and not result['warnings']:
                report.append("✅ 所有检查通过\n")
        
        return '\n'.join(report)

def main():
    """主函数"""
    checker = FieldNamingChecker()
    
    print("开始检查SQL文件字段命名规范...")
    results = checker.check_all_sql_files()
    
    # 生成报告
    report = checker.generate_report(results)
    
    # 输出报告
    print(report)
    
    # 保存报告到文件
    with open('sql/field_naming_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n检查完成！报告已保存到 sql/field_naming_report.md")
    
    # 返回退出码
    failed_count = sum(1 for r in results if not r['passed'])
    exit(1 if failed_count > 0 else 0)

if __name__ == '__main__':
    main() 