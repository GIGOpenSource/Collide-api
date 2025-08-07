"""
内容模块 API 测试示例
展示各种查询条件的用法
"""
import requests
import json
from datetime import datetime, timedelta

# API基础配置
BASE_URL = "http://localhost:8080/api/v1/content"
HEADERS = {
    "Content-Type": "application/json",
    # 模拟网关传递的用户信息
    "X-User-Id": "1",
    "X-Username": "testuser",
    "X-User-Role": "user"
}


def test_content_queries():
    """测试各种内容查询功能"""
    
    print("🚀 内容模块 API 测试")
    print("=" * 50)
    
    # 1. 基础内容列表查询
    print("\n📋 1. 获取基础内容列表")
    response = requests.get(f"{BASE_URL}/", params={
        "page": 1,
        "size": 10
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"总数: {data['data']['total']}")
        print(f"内容数量: {len(data['data']['datas'])}")
    
    # 2. 按内容类型筛选
    print("\n📚 2. 按内容类型筛选 (NOVEL)")
    response = requests.get(f"{BASE_URL}/", params={
        "content_type": "NOVEL",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"小说数量: {len(data['data']['datas'])}")
    
    # 3. 按统计数据筛选 - 热门内容
    print("\n🔥 3. 按浏览量筛选热门内容")
    response = requests.get(f"{BASE_URL}/", params={
        "min_view_count": 1000,
        "sort_by": "view_count",
        "sort_order": "desc",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"热门内容数量: {len(data['data']['datas'])}")
        for item in data['data']['datas']:
            print(f"  - {item['title']}: {item['view_count']} 浏览")
    
    # 4. 按点赞数筛选
    print("\n👍 4. 按点赞数筛选")
    response = requests.get(f"{BASE_URL}/", params={
        "min_like_count": 100,
        "sort_by": "like_count",
        "sort_order": "desc",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"高点赞内容数量: {len(data['data']['datas'])}")
        for item in data['data']['datas']:
            print(f"  - {item['title']}: {item['like_count']} 点赞")
    
    # 5. 按评分筛选
    print("\n⭐ 5. 按评分筛选高质量内容")
    response = requests.get(f"{BASE_URL}/", params={
        "min_score": 4.0,
        "sort_by": "score",
        "sort_order": "desc",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"高评分内容数量: {len(data['data']['datas'])}")
        for item in data['data']['datas']:
            avg_score = item.get('average_score', 0)
            print(f"  - {item['title']}: {avg_score} 分")
    
    # 6. 时间范围筛选
    print("\n📅 6. 按发布时间筛选最近内容")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/", params={
        "publish_date_start": start_date,
        "sort_by": "publish_time",
        "sort_order": "desc",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"最近30天内容数量: {len(data['data']['datas'])}")
    
    # 7. 标签筛选
    print("\n🏷️ 7. 按标签筛选")
    response = requests.get(f"{BASE_URL}/", params={
        "tags": "玄幻,修仙",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"标签匹配内容数量: {len(data['data']['datas'])}")
    
    # 8. 关键词搜索
    print("\n🔍 8. 关键词搜索")
    response = requests.get(f"{BASE_URL}/search", params={
        "q": "传奇",
        "sort_by": "view_count",
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"搜索结果数量: {len(data['data']['datas'])}")
        for item in data['data']['datas']:
            print(f"  - {item['title']}")
    
    # 9. 热门内容接口
    print("\n🔥 9. 热门内容接口")
    response = requests.get(f"{BASE_URL}/hot", params={
        "days": 7,
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"7天内热门内容数量: {len(data['data']['datas'])}")
    
    # 10. 最新内容接口
    print("\n🆕 10. 最新内容接口")
    response = requests.get(f"{BASE_URL}/latest", params={
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"最新内容数量: {len(data['data']['datas'])}")
    
    # 11. 推荐内容接口
    print("\n⭐ 11. 推荐内容接口")
    response = requests.get(f"{BASE_URL}/recommended", params={
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"推荐内容数量: {len(data['data']['datas'])}")
    
    # 12. 趋势内容接口
    print("\n📈 12. 趋势内容接口")
    response = requests.get(f"{BASE_URL}/trending", params={
        "page": 1,
        "size": 5
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"趋势内容数量: {len(data['data']['datas'])}")
    
    # 13. 组合筛选 - 高质量小说
    print("\n📖 13. 组合筛选 - 高质量小说")
    response = requests.get(f"{BASE_URL}/", params={
        "content_type": "NOVEL",
        "min_view_count": 500,
        "min_like_count": 50,
        "min_score": 3.5,
        "sort_by": "score",
        "sort_order": "desc",
        "page": 1,
        "size": 3
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"高质量小说数量: {len(data['data']['datas'])}")
        for item in data['data']['datas']:
            print(f"  - {item['title']}: {item['view_count']}浏览, {item['like_count']}点赞, {item.get('average_score', 0)}分")


def test_my_content():
    """测试我的内容接口"""
    print("\n📝 我的内容管理测试")
    print("-" * 30)
    
    # 获取我的内容列表
    response = requests.get(f"{BASE_URL}/my/contents", 
                          headers=HEADERS,
                          params={
                              "page": 1,
                              "size": 5
                          })
    print(f"我的内容列表状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"我的内容数量: {len(data['data']['datas'])}")
    
    # 按状态筛选我的内容
    response = requests.get(f"{BASE_URL}/my/contents",
                          headers=HEADERS,
                          params={
                              "status": "PUBLISHED",
                              "min_view_count": 100,
                              "sort_by": "view_count",
                              "sort_order": "desc",
                              "page": 1,
                              "size": 3
                          })
    print(f"我的已发布热门内容状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"我的已发布热门内容数量: {len(data['data']['datas'])}")


def test_content_operations():
    """测试内容操作接口"""
    print("\n🛠️ 内容操作测试")
    print("-" * 30)
    
    # 创建内容
    create_data = {
        "title": "测试内容标题",
        "description": "这是一个测试内容的描述",
        "content_type": "ARTICLE",
        "cover_url": "https://example.com/cover.jpg",
        "tags": "测试,API,内容",
        "category_id": 1,
        "category_name": "科技文章"
    }
    
    response = requests.post(f"{BASE_URL}/", 
                           headers=HEADERS,
                           json=create_data)
    print(f"创建内容状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        content_id = data['data']['id']
        print(f"创建成功，内容ID: {content_id}")
        
        # 获取内容详情
        response = requests.get(f"{BASE_URL}/{content_id}")
        print(f"获取内容详情状态码: {response.status_code}")
        
        # 更新统计数据
        response = requests.post(f"{BASE_URL}/{content_id}/stats",
                               json={
                                   "increment_type": "view",
                                   "increment_value": 10
                               })
        print(f"更新浏览量状态码: {response.status_code}")
        
        # 内容评分
        response = requests.post(f"{BASE_URL}/{content_id}/score",
                               headers=HEADERS,
                               json={"score": 5})
        print(f"内容评分状态码: {response.status_code}")
        
        # 获取内容统计信息
        response = requests.get(f"{BASE_URL}/{content_id}/stats")
        print(f"获取统计信息状态码: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"统计信息: 浏览{stats['view_count']}, 点赞{stats['like_count']}, 评分{stats.get('average_score', 0)}")


if __name__ == "__main__":
    print("⚠️  请确保服务已启动并生成了测试数据")
    print("运行命令: python scripts/content_data_generator.py")
    print()
    
    try:
        test_content_queries()
        test_my_content()
        test_content_operations()
        
        print("\n" + "=" * 50)
        print("✅ 内容模块 API 测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保服务已启动 (python start.py)")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
