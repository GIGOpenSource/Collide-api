#!/usr/bin/env python3
"""
索引维护脚本
用于创建、删除和优化数据库索引
"""
import asyncio
import argparse
import sys
from typing import List, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = "mysql+aiomysql://root:password@localhost:3306/collide_db"


class IndexMaintenance:
    """索引维护器"""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def create_indexes_from_file(self, filename: str) -> Dict:
        """从文件创建索引"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割SQL语句
            statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
            
            results = {
                "success": [],
                "failed": [],
                "skipped": []
            }
            
            async with self.async_session() as session:
                for stmt in statements:
                    if stmt.startswith('--') or not stmt:
                        continue
                    
                    try:
                        await session.execute(text(stmt))
                        await session.commit()
                        results["success"].append(stmt)
                        print(f"✓ 成功创建索引: {stmt[:50]}...")
                    except Exception as e:
                        if "Duplicate key name" in str(e):
                            results["skipped"].append(stmt)
                            print(f"⚠ 索引已存在，跳过: {stmt[:50]}...")
                        else:
                            results["failed"].append({"stmt": stmt, "error": str(e)})
                            print(f"✗ 创建索引失败: {stmt[:50]}... - {e}")
            
            return results
            
        except FileNotFoundError:
            print(f"错误: 文件 {filename} 不存在")
            return {"success": [], "failed": [], "skipped": []}

    async def drop_index(self, table_name: str, index_name: str) -> bool:
        """删除指定索引"""
        try:
            async with self.async_session() as session:
                stmt = f"DROP INDEX {index_name} ON {table_name}"
                await session.execute(text(stmt))
                await session.commit()
                print(f"✓ 成功删除索引: {index_name} ON {table_name}")
                return True
        except Exception as e:
            print(f"✗ 删除索引失败: {index_name} ON {table_name} - {e}")
            return False

    async def drop_unused_indexes(self) -> Dict:
        """删除未使用的索引"""
        async with self.async_session() as session:
            # 获取索引使用统计
            result = await session.execute(text("""
                SELECT 
                    OBJECT_NAME as table_name,
                    INDEX_NAME as index_name,
                    COUNT_FETCH
                FROM performance_schema.table_io_waits_summary_by_index_usage
                WHERE OBJECT_SCHEMA = 'collide_db'
                AND INDEX_NAME IS NOT NULL
                AND INDEX_NAME != 'PRIMARY'
            """))
            
            unused_indexes = []
            for row in result.fetchall():
                if row[2] == 0:  # COUNT_FETCH = 0
                    unused_indexes.append({
                        "table_name": row[0],
                        "index_name": row[1]
                    })
            
            results = {"dropped": [], "failed": []}
            
            for index_info in unused_indexes:
                success = await self.drop_index(index_info["table_name"], index_info["index_name"])
                if success:
                    results["dropped"].append(index_info)
                else:
                    results["failed"].append(index_info)
            
            return results

    async def optimize_tables(self, table_names: List[str] = None) -> Dict:
        """优化表"""
        if table_names is None:
            # 获取所有表
            async with self.async_session() as session:
                result = await session.execute(text("""
                    SELECT TABLE_NAME 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = 'collide_db'
                """))
                table_names = [row[0] for row in result.fetchall()]
        
        results = {"optimized": [], "failed": []}
        
        async with self.async_session() as session:
            for table_name in table_names:
                try:
                    stmt = f"OPTIMIZE TABLE {table_name}"
                    await session.execute(text(stmt))
                    await session.commit()
                    results["optimized"].append(table_name)
                    print(f"✓ 成功优化表: {table_name}")
                except Exception as e:
                    results["failed"].append({"table": table_name, "error": str(e)})
                    print(f"✗ 优化表失败: {table_name} - {e}")
        
        return results

    async def analyze_tables(self, table_names: List[str] = None) -> Dict:
        """分析表"""
        if table_names is None:
            # 获取所有表
            async with self.async_session() as session:
                result = await session.execute(text("""
                    SELECT TABLE_NAME 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = 'collide_db'
                """))
                table_names = [row[0] for row in result.fetchall()]
        
        results = {"analyzed": [], "failed": []}
        
        async with self.async_session() as session:
            for table_name in table_names:
                try:
                    stmt = f"ANALYZE TABLE {table_name}"
                    await session.execute(text(stmt))
                    await session.commit()
                    results["analyzed"].append(table_name)
                    print(f"✓ 成功分析表: {table_name}")
                except Exception as e:
                    results["failed"].append({"table": table_name, "error": str(e)})
                    print(f"✗ 分析表失败: {table_name} - {e}")
        
        return results

    async def get_index_status(self) -> Dict:
        """获取索引状态"""
        async with self.async_session() as session:
            # 获取所有索引信息
            result = await session.execute(text("""
                SELECT 
                    TABLE_NAME,
                    INDEX_NAME,
                    COLUMN_NAME,
                    SEQ_IN_INDEX,
                    CARDINALITY,
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
                        "columns": [],
                        "cardinality": row[4] or 0,
                        "index_type": row[5]
                    }
                
                indexes[table_name][index_name]["columns"].append({
                    "column_name": row[2],
                    "seq_in_index": row[3]
                })
            
            return indexes

    async def print_index_status(self):
        """打印索引状态"""
        indexes = await self.get_index_status()
        
        print("=" * 80)
        print("数据库索引状态")
        print("=" * 80)
        
        for table_name, table_indexes in indexes.items():
            print(f"\n表: {table_name}")
            print("-" * 40)
            
            if not table_indexes:
                print("  无索引")
                continue
            
            for index_name, index_info in table_indexes.items():
                columns = ", ".join([col["column_name"] for col in index_info["columns"]])
                print(f"  {index_name}:")
                print(f"    列: {columns}")
                print(f"    基数: {index_info['cardinality']}")
                print(f"    类型: {index_info['index_type']}")
        
        print("\n" + "=" * 80)

    async def cleanup(self):
        """清理资源"""
        await self.engine.dispose()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库索引维护工具")
    parser.add_argument("--action", choices=["create", "drop", "optimize", "analyze", "status"], 
                       required=True, help="执行的操作")
    parser.add_argument("--file", help="索引文件路径（用于create操作）")
    parser.add_argument("--tables", nargs="+", help="指定表名列表")
    parser.add_argument("--drop-unused", action="store_true", help="删除未使用的索引")
    
    args = parser.parse_args()
    
    maintenance = IndexMaintenance(DATABASE_URL)
    
    try:
        if args.action == "create":
            if not args.file:
                print("错误: create操作需要指定--file参数")
                sys.exit(1)
            
            results = await maintenance.create_indexes_from_file(args.file)
            print(f"\n创建索引结果:")
            print(f"  成功: {len(results['success'])}")
            print(f"  失败: {len(results['failed'])}")
            print(f"  跳过: {len(results['skipped'])}")
        
        elif args.action == "drop":
            if args.drop_unused:
                results = await maintenance.drop_unused_indexes()
                print(f"\n删除未使用索引结果:")
                print(f"  成功删除: {len(results['dropped'])}")
                print(f"  删除失败: {len(results['failed'])}")
            else:
                print("错误: drop操作需要指定--drop-unused参数")
                sys.exit(1)
        
        elif args.action == "optimize":
            results = await maintenance.optimize_tables(args.tables)
            print(f"\n优化表结果:")
            print(f"  成功: {len(results['optimized'])}")
            print(f"  失败: {len(results['failed'])}")
        
        elif args.action == "analyze":
            results = await maintenance.analyze_tables(args.tables)
            print(f"\n分析表结果:")
            print(f"  成功: {len(results['analyzed'])}")
            print(f"  失败: {len(results['failed'])}")
        
        elif args.action == "status":
            await maintenance.print_index_status()
    
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        sys.exit(1)
    
    finally:
        await maintenance.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 