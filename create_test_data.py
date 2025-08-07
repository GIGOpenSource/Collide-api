#!/usr/bin/env python3
"""
创建测试数据 - 简化版本
使用方法:
    python create_test_data.py                    # 创建默认测试数据
    python create_test_data.py --scenario small   # 创建小量测试数据  
    python create_test_data.py --scenario large   # 创建大量测试数据
    python create_test_data.py --clear            # 清空并重新创建
    python create_test_data.py --preset-only      # 只创建预设用户
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🎭 Collide User Service 测试数据创建器")
    print("=" * 60)
    
    try:
        from scripts.advanced_data_generator import main as advanced_main
        advanced_main()
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断，程序退出")
        return 0
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())