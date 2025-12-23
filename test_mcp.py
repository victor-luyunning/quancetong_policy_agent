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
            
            # 提取并单独显示URL
            answer = result['final_answer']
            import re
            
            # 提取图表URL
            if '📊' in answer:
                chart_urls = re.findall(r'https://quickchart\.io/chart\?[^\s\n]+', answer)
                if chart_urls:
                    print("\n" + "="*80)
                    print("📊 提取到的图表URL:")
                    for i, url in enumerate(chart_urls, 1):
                        print(f"\n图表{i}: {url}")
            
            # 提取地图URL
            if '🗺️' in answer:
                # 匹配高德地图URL
                amap_urls = re.findall(r'https://restapi\.amap\.com/[^\s\n]+', answer)
                # 匹配QuickChart地图URL
                quickchart_map_urls = re.findall(r'地图链接:\s*(https://quickchart\.io/chart\?[^\s\n]+)', answer)
                
                if amap_urls or quickchart_map_urls:
                    print("\n" + "="*80)
                    print("🗺️ 提取到的地图URL:")
                    for i, url in enumerate(amap_urls, 1):
                        print(f"\n高德地图{i}: {url}")
                    for i, url in enumerate(quickchart_map_urls, 1):
                        print(f"\n坐标地图{i}: {url}")
            
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
                    amap_data = mcp['amap']
                    if amap_data.get('success'):
                        print(f"    - 标注数量: {amap_data.get('total_markers', 0)}")
                        if amap_data.get('map_image_url'):
                            print(f"    - 地图URL: {amap_data['map_image_url']}")
                            print(f"    - 地图来源: {amap_data.get('map_source', 'unknown')}")
                        if amap_data.get('cities_covered'):
                            print(f"    - 覆盖城市: {', '.join(amap_data['cities_covered'])}")
                    else:
                        print(f"    - 生成失败: {amap_data.get('error', '未知错误')}")
                
                if mcp.get('fetch'):
                    print(f"  🌐 实时政策:")
                    print(f"    - 抓取数量: {mcp['fetch'].get('total', 0)}")
                
                if mcp.get('context7'):
                    ctx = mcp['context7']
                    print(f"  💭 上下文:")
                    print(f"    - 需要上下文: {ctx.get('need_context')}")
                    if ctx.get('related_conversation'):
                        print(f"    - 关联问题: {ctx['related_conversation']['query']}")
                
                if mcp.get('time'):
                    print(f"  ⏱️ 时间感知:")
                    time_res = mcp['time']
                    if time_res.get('success'):
                        now = time_res.get('now')
                        active = time_res.get('active_hits', [])
                        inactive = time_res.get('inactive_hits', [])
                        print(f"    - 当前时间: {now}")
                        print(f"    - 有效政策: {', '.join(active) if active else '无'}")
                        print(f"    - 失效政策: {', '.join(inactive) if inactive else '无'}")
                    else:
                        print(f"    - 失败: {time_res.get('error', '未知错误')}")
            
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
    test_mcp_query("济南和青岛的汽车补贴政策对比", enable_mcp=True)
    
    input("\n按回车继续...")
    
    # 测试2: 企业信号灯（应该触发QuickChart + Amap）
    test_mcp_query("餐饮行业有哪些值得招商的企业？", enable_mcp=True)
    
    input("\n按回车继续...")
    
    # 测试3: 上下文对话 + 流程图（应该触发Mermaid）
    test_mcp_query("济南市电视机补贴政策是什么？", enable_mcp=True)
    input("\n按回车继续...")
    test_mcp_query("那个政策的申领流程是怎样的？", enable_mcp=True)
    
    input("\n按回车继续...")
    # 测试4: 时间感知（policy_parse 应触发 time MCP）
    test_mcp_query("济南买汽车有什么补贴政策吗", enable_mcp=True)
    
    print("\n✅ 所有测试完成！")
