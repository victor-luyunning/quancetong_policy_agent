import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_mcp_query(query_text, enable_mcp=True):
    """测试MCP增强查询"""
    print(f"\n{'='*60}")
    print(f"查询: {query_text}")
    print(f"MCP增强: {'启用' if enable_mcp else '禁用'}")
    print('='*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "query": query_text,
                "enable_mcp": enable_mcp
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ 意图: {result['intent']}")
            print(f"\n💬 最终回答:\n{result['final_answer']}")
            
            # 显示MCP增强结果
            if result.get('mcp_enhancements'):
                print(f"\n🔧 MCP工具增强:")
                mcp = result['mcp_enhancements']
                
                if mcp.get('quickchart'):
                    print(f"  📊 QuickChart图表:")
                    for chart_name, chart_data in mcp['quickchart'].items():
                        if chart_data.get('success'):
                            print(f"    - {chart_name}: {chart_data.get('chart_url')}")
                
                if mcp.get('amap'):
                    print(f"  🗺️ 高德地图:")
                    print(f"    - 标注数量: {mcp['amap'].get('total_markers', 0)}")
                
                if mcp.get('fetch'):
                    print(f"  🌐 实时政策:")
                    print(f"    - 抓取数量: {mcp['fetch'].get('total', 0)}")
                
                if mcp.get('context7'):
                    ctx = mcp['context7']
                    print(f"  💭 上下文:")
                    print(f"    - 需要上下文: {ctx.get('need_context')}")
                    if ctx.get('related_conversation'):
                        print(f"    - 关联问题: {ctx['related_conversation']['query']}")
            
            if result.get('conversation_id'):
                print(f"\n🆔 对话ID: {result['conversation_id']}")
            
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
    print("\n" + "="*60)
    print("泉策通智能体 - MCP工具测试")
    print("="*60)
    
    # 测试1: 区域对比（应该触发QuickChart）
    test_mcp_query("济南和青岛的家电补贴政策对比", enable_mcp=True)
    
    input("\n按回车继续...")
    
    # 测试2: 企业信号灯（应该触发QuickChart + Amap）
    test_mcp_query("家电行业有哪些值得招商的企业？", enable_mcp=True)
    
    input("\n按回车继续...")
    
    # 测试3: 上下文对话
    test_mcp_query("济南市家电补贴政策是什么？", enable_mcp=True)
    input("\n按回车继续...")
    test_mcp_query("那个政策的申领流程是怎样的？", enable_mcp=True)
    
    print("\n✅ 所有测试完成！")
