# test_service.py - 测试脚本
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """测试健康检查"""
    print("\n========== 测试健康检查 ==========")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_query(query_text: str):
    """测试查询接口"""
    print(f"\n========== 测试查询: {query_text} ==========")
    try:
        resp = requests.post(
            f"{BASE_URL}/query",
            json={"query": query_text},
            timeout=30
        )
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"意图: {result.get('intent')}")
        print(f"实体: {json.dumps(result.get('entities'), ensure_ascii=False, indent=2)}")
        print(f"结果: {json.dumps(result.get('result'), ensure_ascii=False, indent=2)}")
        print(f"\n最终回答:\n{result.get('final_answer')}")
        if result.get('citations'):
            print(f"\n引用: {result.get('citations')}")
        return resp.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("泉策通智能体服务测试")
    print("="*60)
    
    # 测试1: 健康检查
    if not test_health():
        print("\n❌ 服务未启动，请先运行 python app.py")
        return
    
    print("\n✅ 服务运行正常\n")
    
    # 测试2: 政策解析
    test_query("济南市2025年家电以旧换新政策是什么？")
    
    # 测试3: 福利计算
    test_query("在济南买了3000元的空调，能领多少补贴？")
    
    # 测试4: 区域对比
    test_query("济南和青岛的家电补贴政策哪个好？")
    
    # 测试5: 企业信号灯
    test_query("家电行业有哪些值得招商的企业？")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
