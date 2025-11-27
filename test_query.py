import requests
import json
import sys

def test_query(query_text):
    """测试单个查询"""
    url = "http://127.0.0.1:8000/query"
    
    print(f"\n{'='*60}")
    print(f"查询: {query_text}")
    print('='*60)
    
    try:
        response = requests.post(
            url,
            json={"query": query_text},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ 意图识别: {result['intent']}")
            
            print(f"\n📍 实体提取:")
            for key, value in result['entities'].items():
                if value:
                    print(f"   {key}: {value}")
            
            print(f"\n📊 工作流结果:")
            for key, value in result['result'].items():
                if value and key != 'all_hits':
                    if isinstance(value, (list, dict)):
                        print(f"   {key}: {json.dumps(value, ensure_ascii=False, indent=4)}")
                    else:
                        print(f"   {key}: {value}")
            
            print(f"\n💬 最终回答:")
            print(f"   {result['final_answer']}")
            
            if result.get('citations'):
                print(f"\n📚 引用来源:")
                print(f"   {result['citations']}")
            
            print('\n' + '='*60)
            return True
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行参数查询
        query = " ".join(sys.argv[1:])
        test_query(query)
    else:
        # 默认测试用例
        print("\n" + "="*60)
        print("泉策通智能体 - 查询测试")
        print("="*60)
        
        test_cases = [
            "济南市2025年电冰箱以旧换新政策是什么？",
            "在济南买了3000元的空调，能领多少补贴？",
            "济南和青岛的手机购买补贴政策对比",
            "汽车行业有哪些值得招商的企业？"
        ]
        
        for query in test_cases:
            test_query(query)
            input("\n按回车继续下一个测试...")
        
        print("\n✅ 所有测试完成！")
