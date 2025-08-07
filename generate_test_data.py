#!/usr/bin/env python3
"""
快速生成测试数据脚本
使用方法：
    python generate_test_data.py              # 生成默认数量的测试数据
    python generate_test_data.py --users 100  # 生成100个用户
    python generate_test_data.py --clear      # 清空现有数据后重新生成
    python generate_test_data.py --clear-only # 只清空数据
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.fake_data_generator import main

if __name__ == "__main__":
    print("🎭 Collide User Service 测试数据生成器")
    print("=" * 50)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)