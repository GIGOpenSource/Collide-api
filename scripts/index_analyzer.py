#!/usr/bin/env python3
"""
索引分析和监控脚本
用于分析数据库索引使用情况和性能优化建议
"""
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = "mysql+aiomysql://root:password@localhost:3306/collide_db"


class IndexAnalyzer:
    """索引分析器"""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def get_table_info(self) -> Dict:
        """获取表信息"""
        async with self.async_session() as session:
            # 获取所有表
            result = await session.execute(text("""
                SELECT 
                    TABLE_NAME,
                    TABLE_ROWS,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    (DATA_LENGTH + INDEX_LENGTH) as TOTAL_SIZE
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = 'collide_db'
                ORDER BY TABLE_NAME
            """))
            
            tables = {}
            for row in result.fetchall():
                tables[row[0]] = {
                    "table_name": row[0],
                    "table_rows": row[1] or 0,
                    "data_length": row[2] or 0,
                    "index_length": row[3] or 0,
                    "total_size": row[4] or 0
                }
            
            return tables

    async def get_index_info(self) -> Dict:
        """获取索引信息"""
        async with self.async_session() as session:
            # 获取所有索引
            result = await session.execute(text("""
                SELECT 
                    TABLE_NAME,
                    INDEX_NAME,
                    COLUMN_NAME,
                    SEQ_IN_INDEX,
                    CARDINALITY,
                    NULLABLE,
                    INDEX_TYPE
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = 'collide_db'
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
            """))
            
            indexes = {}
            for row in result.fetchall():
                table_name = row[0]
                index_name = row[1]
                
                if table_name not in indexes:
                    indexes[table_name] = {}
                
                if index_name not in indexes[table_name]:
                    indexes[table_name][index_name] = {
                        "index_name": index_name,
                        "columns": [],
                        "cardinality": row[4] or 0,
                        "index_type": row[6]
                    }
                
                indexes[table_name][index_name]["columns"].append({
                    "column_name": row[2],
                    "seq_in_index": row[3],
                    "nullable": row[5]
                })
            
            return indexes

    async def get_slow_queries(self) -> List[Dict]:
        """获取慢查询信息"""
        async with self.async_session() as session:
            # 检查是否启用了慢查询日志
            result = await session.execute(text("SHOW VARIABLES LIKE 'slow_query_log'"))
            slow_log_enabled = result.fetchone()[1] == 'ON'
            
            if not slow_log_enabled:
                return []
            
            # 获取慢查询日志文件路径
            result = await session.execute(text("SHOW VARIABLES LIKE 'slow_query_log_file'"))
            slow_log_file = result.fetchone()[1]
            
            # 这里可以解析慢查询日志文件
            # 简化处理，返回空列表
            return []

    async def analyze_index_usage(self) -> Dict:
        """分析索引使用情况"""
        async with self.async_session() as session:
            # 获取索引使用统计
            result = await session.execute(text("""
                SELECT 
                    OBJECT_SCHEMA,
                    OBJECT_NAME,
                    INDEX_NAME,
                    COUNT_FETCH,
                    COUNT_INSERT,
                    COUNT_UPDATE,
                    COUNT_DELETE
                FROM performance_schema.table_io_waits_summary_by_index_usage
                WHERE OBJECT_SCHEMA = 'collide_db'
                ORDER BY COUNT_FETCH DESC
            """))
            
            usage_stats = {}
            for row in result.fetchall():
                table_name = row[1]
                index_name = row[2]
                
                if table_name not in usage_stats:
                    usage_stats[table_name] = {}
                
                usage_stats[table_name][index_name] = {
                    "index_name": index_name,
                    "count_fetch": row[3] or 0,
                    "count_insert": row[4] or 0,
                    "count_update": row[5] or 0,
                    "count_delete": row[6] or 0
                }
            
            return usage_stats

    async def generate_optimization_report(self) -> Dict:
        """生成优化报告"""
        tables = await self.get_table_info()
        indexes = await self.get_index_info()
        usage_stats = await self.analyze_index_usage() # Corrected to use analyze_index_usage
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tables": len(tables),
                "total_indexes": sum(len(table_indexes) for table_indexes in indexes.values()),
                "total_data_size": sum(table["data_length"] for table in tables.values()),
                "total_index_size": sum(table["index_length"] for table in tables.values())
            },
            "tables": {},
            "recommendations": []
        }
        
        # 分析每个表
        for table_name, table_info in tables.items():
            table_indexes = indexes.get(table_name, {})
            table_usage = usage_stats.get(table_name, {})
            
            report["tables"][table_name] = {
                "table_info": table_info,
                "indexes": table_indexes,
                "usage_stats": table_usage,
                "analysis": self._analyze_table(table_name, table_info, table_indexes, table_usage)
            }
        
        # 生成优化建议
        report["recommendations"] = self._generate_recommendations(report["tables"])
        
        return report

    def _analyze_table(self, table_name: str, table_info: Dict, indexes: Dict, usage_stats: Dict) -> Dict:
        """分析单个表"""
        analysis = {
            "index_count": len(indexes),
            "unused_indexes": [],
            "missing_indexes": [],
            "performance_score": 0
        }
        
        # 检查未使用的索引
        for index_name in indexes:
            if index_name not in usage_stats or usage_stats[index_name]["count_fetch"] == 0:
                analysis["unused_indexes"].append(index_name)
        
        # 检查缺失的索引（基于常见查询模式）
        missing_indexes = self._check_missing_indexes(table_name, indexes)
        analysis["missing_indexes"] = missing_indexes
        
        # 计算性能评分
        total_fetches = sum(stats["count_fetch"] for stats in usage_stats.values())
        unused_count = len(analysis["unused_indexes"])
        missing_count = len(analysis["missing_indexes"])
        
        if total_fetches > 0:
            analysis["performance_score"] = max(0, 100 - unused_count * 10 - missing_count * 5)
        else:
            analysis["performance_score"] = 50  # 新表默认评分
        
        return analysis

    def _check_missing_indexes(self, table_name: str, indexes: Dict) -> List[str]:
        """检查缺失的索引"""
        missing = []
        
        # 基于表名和常见查询模式检查
        if table_name == "t_users":
            if "idx_users_username" not in indexes:
                missing.append("idx_users_username (username)")
            if "idx_users_email" not in indexes:
                missing.append("idx_users_email (email)")
            if "idx_users_status" not in indexes:
                missing.append("idx_users_status (status)")
        
        elif table_name == "t_content":
            if "idx_content_author_id" not in indexes:
                missing.append("idx_content_author_id (author_id)")
            if "idx_content_status" not in indexes:
                missing.append("idx_content_status (status)")
            if "idx_content_create_time" not in indexes:
                missing.append("idx_content_create_time (create_time)")
        
        elif table_name == "t_comment":
            if "idx_comment_type_target" not in indexes:
                missing.append("idx_comment_type_target (comment_type, target_id)")
            if "idx_comment_user_id" not in indexes:
                missing.append("idx_comment_user_id (user_id)")
        
        elif table_name == "t_like":
            if "idx_like_user_type_target" not in indexes:
                missing.append("idx_like_user_type_target (user_id, like_type, target_id)")
        
        elif table_name == "t_follow":
            if "idx_follow_follower_followee" not in indexes:
                missing.append("idx_follow_follower_followee (follower_id, followee_id)")
        
        return missing

    def _generate_recommendations(self, tables: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        total_unused = sum(table["analysis"]["unused_indexes"] for table in tables.values())
        total_missing = sum(table["analysis"]["missing_indexes"] for table in tables.values())
        
        if total_unused > 0:
            recommendations.append(f"发现 {total_unused} 个未使用的索引，建议删除以提升写入性能")
        
        if total_missing > 0:
            recommendations.append(f"发现 {total_missing} 个缺失的索引，建议添加以提升查询性能")
        
        # 检查大表
        for table_name, table_data in tables.items():
            table_info = table_data["table_info"]
            if table_info["table_rows"] > 100000:
                recommendations.append(f"表 {table_name} 数据量较大 ({table_info['table_rows']} 行)，建议定期维护索引")
        
        # 检查索引大小
        for table_name, table_data in tables.items():
            table_info = table_data["table_info"]
            if table_info["index_length"] > table_info["data_length"] * 0.5:
                recommendations.append(f"表 {table_name} 索引大小占比较高，建议优化索引结构")
        
        return recommendations

    async def export_report(self, filename: str = None):
        """导出分析报告"""
        if filename is None:
            filename = f"index_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = await self.generate_optimization_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"分析报告已导出到: {filename}")
        return report

    async def print_summary(self):
        """打印分析摘要"""
        report = await self.generate_optimization_report()
        
        print("=" * 60)
        print("数据库索引分析报告")
        print("=" * 60)
        print(f"分析时间: {report['timestamp']}")
        print(f"总表数: {report['summary']['total_tables']}")
        print(f"总索引数: {report['summary']['total_indexes']}")
        print(f"数据大小: {report['summary']['total_data_size'] / 1024 / 1024:.2f} MB")
        print(f"索引大小: {report['summary']['total_index_size'] / 1024 / 1024:.2f} MB")
        print()
        
        print("表分析结果:")
        print("-" * 60)
        for table_name, table_data in report["tables"].items():
            analysis = table_data["analysis"]
            print(f"{table_name}:")
            print(f"  索引数: {analysis['index_count']}")
            print(f"  未使用索引: {len(analysis['unused_indexes'])}")
            print(f"  缺失索引: {len(analysis['missing_indexes'])}")
            print(f"  性能评分: {analysis['performance_score']}/100")
            print()
        
        print("优化建议:")
        print("-" * 60)
        for i, recommendation in enumerate(report["recommendations"], 1):
            print(f"{i}. {recommendation}")
        
        print("=" * 60)


async def main():
    """主函数"""
    analyzer = IndexAnalyzer(DATABASE_URL)
    
    try:
        await analyzer.print_summary()
        await analyzer.export_report()
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
    finally:
        await analyzer.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main()) 