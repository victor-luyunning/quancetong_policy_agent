import requests
import json
import sys
import csv
from datetime import datetime
import time

def test_query(query_text, show_details=True):
    """测试单个查询"""
    url = "http://146.56.198.222:8001/query"
    
    if show_details:
        print(f"\n{'='*60}")
        print(f"查询: {query_text}")
        print('='*60)
    
    try:
        start_time = time.time()
        response = requests.post(
            url,
            json={"query": query_text},
            timeout=30
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if show_details:
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
                
                print(f"\n⏱️ 响应时间: {response_time:.2f}秒")
                print('\n' + '='*60)
            
            return {
                'success': True,
                'result': result,
                'response_time': response_time,
                'error': None
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            if show_details:
                print(f"\n❌ 请求失败: {error_msg}")
            return {
                'success': False,
                'result': None,
                'response_time': response_time,
                'error': error_msg
            }
            
    except Exception as e:
        error_msg = str(e)
        if show_details:
            print(f"\n❌ 错误: {error_msg}")
        return {
            'success': False,
            'result': None,
            'response_time': 0,
            'error': error_msg
        }


def batch_test_from_dataset(dataset_file, output_csv):
    """从数据集批量测试并输出CSV结果"""
    print(f"\n{'='*60}")
    print("泉策通智能体 - 批量测试")
    print('='*60)
    
    # 读取测试数据集
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        print(f"\n✅ 成功加载 {len(test_cases)} 个测试用例")
    except Exception as e:
        print(f"\n❌ 加载数据集失败: {e}")
        return
    
    # 准备CSV输出
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_csv:
        output_csv = f"test_results_{timestamp}.csv"
    
    results = []
    success_count = 0
    
    # 批量测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'='*60}")
        print(f"测试进度: {i}/{len(test_cases)}")
        print(f"ID: {test_case['id']} | 分类: {test_case['category']}")
        print('='*60)
        
        question = test_case['question']
        expected_answer = test_case.get('expected_answer', '')
        
        # 执行测试
        test_result = test_query(question, show_details=True)
        
        if test_result['success']:
            success_count += 1
            api_result = test_result['result']
            
            # 记录结果
            result_record = {
                'id': test_case['id'],
                'question': question,
                'expected_answer': expected_answer,
                'category': test_case['category'],
                'campaign_id': test_case.get('campaign_id', ''),
                'intent': api_result.get('intent', ''),
                'entities': json.dumps(api_result.get('entities', {}), ensure_ascii=False),
                'final_answer': api_result.get('final_answer', ''),
                'citations': api_result.get('citations', ''),
                'response_time': f"{test_result['response_time']:.2f}",
                'status': '成功',
                'error': ''
            }
        else:
            result_record = {
                'id': test_case['id'],
                'question': question,
                'expected_answer': expected_answer,
                'category': test_case['category'],
                'campaign_id': test_case.get('campaign_id', ''),
                'intent': '',
                'entities': '',
                'final_answer': '',
                'citations': '',
                'response_time': f"{test_result['response_time']:.2f}",
                'status': '失败',
                'error': test_result['error']
            }
        
        results.append(result_record)
        
        # 避免请求过快
        time.sleep(0.5)
    
    # 写入CSV
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                'id', 'question', 'expected_answer', 'category', 'campaign_id',
                'intent', 'entities', 'final_answer', 'citations',
                'response_time', 'status', 'error'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n\n{'='*60}")
        print("测试完成！")
        print('='*60)
        print(f"✅ 总测试用例: {len(test_cases)}")
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {len(test_cases) - success_count}")
        print(f"📊 成功率: {success_count/len(test_cases)*100:.2f}%")
        print(f"\n📁 结果已保存到: {output_csv}")
        print('='*60)
        
    except Exception as e:
        print(f"\n❌ 保存CSV失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch":
            # 批量测试模式
            dataset_file = sys.argv[2] if len(sys.argv) > 2 else "test_questions_dataset.json"
            output_file = sys.argv[3] if len(sys.argv) > 3 else None
            batch_test_from_dataset(dataset_file, output_file)
        else:
            # 单个查询测试
            query = " ".join(sys.argv[1:])
            test_query(query, show_details=True)
    else:
        # 交互式菜单
        print("\n" + "="*60)
        print("泉策通智能体 - 测试工具")
        print("="*60)
        print("\n请选择测试模式:")
        print("1. 批量测试（从数据集文件）")
        print("2. 单个查询测试")
        print("3. 默认测试用例")
        
        choice = input("\n请输入选项 (1/2/3): ").strip()
        
        if choice == "1":
            dataset_file = input("\n请输入数据集文件路径 (默认: test_questions_dataset.json): ").strip()
            if not dataset_file:
                dataset_file = "test_questions_dataset.json"
            
            output_file = input("请输入输出CSV文件名 (默认: 自动生成): ").strip()
            if not output_file:
                output_file = None
            
            batch_test_from_dataset(dataset_file, output_file)
            
        elif choice == "2":
            query = input("\n请输入查询内容: ").strip()
            if query:
                test_query(query, show_details=True)
            else:
                print("\n❌ 查询内容不能为空")
                
        elif choice == "3":
            test_cases = [
                "济南市2025年电冰箱以旧换新政策是什么？",
                "在济南买了3000元的空调,能领多少补贴？",
                "济南和青岛的手机购买补贴政策对比",
                "汽车行业有哪些值得招商的企业？"
            ]
            
            for query in test_cases:
                test_query(query, show_details=True)
                input("\n按回车继续下一个测试...")
            
            print("\n✅ 所有测试完成！")
        else:
            print("\n❌ 无效的选项")
