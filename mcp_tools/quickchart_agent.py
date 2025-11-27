import httpx
import json
from typing import Dict, Any, List

MCP_QUICKCHART_URL = "https://mcp.api-inference.modelscope.net/1765b0ae2e674b/mcp"


async def generate_comparison_chart(data: List[Dict], chart_type: str = "column") -> Dict[str, Any]:
    """
    生成对比图表（区域政策对比、企业评分对比等）
    
    Args:
        data: 对比数据 [{"category": "济南", "value": 2000}, {"category": "青岛", "value": 1800}]
        chart_type: 图表类型 column/bar/radar
    
    Returns:
        {"success": bool, "chart_url": str, "chart_data": dict}
    """
    try:
        # QuickChart支持的图表类型
        chart_config = {
            "type": chart_type,
            "data": {
                "labels": [item["category"] for item in data],
                "datasets": [{
                    "label": "数值对比",
                    "data": [item["value"] for item in data],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)"
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "政策对比分析"
                    }
                }
            }
        }
        
        # 生成图表URL（QuickChart标准格式）
        chart_url = f"https://quickchart.io/chart?c={json.dumps(chart_config)}"
        
        return {
            "success": True,
            "chart_url": chart_url,
            "chart_data": chart_config
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def generate_company_score_chart(companies: List[Dict]) -> Dict[str, Any]:
    """
    生成企业评分柱状图
    
    Args:
        companies: [{"name": "海尔", "score": 85}, {"name": "美的", "score": 78}]
    
    Returns:
        图表配置和URL
    """
    chart_config = {
        "type": "bar",
        "data": {
            "labels": [c["name"] for c in companies],
            "datasets": [{
                "label": "企业评分",
                "data": [c["score"] for c in companies],
                "backgroundColor": [
                    "rgba(255, 99, 132, 0.6)",
                    "rgba(54, 162, 235, 0.6)",
                    "rgba(255, 206, 86, 0.6)",
                    "rgba(75, 192, 192, 0.6)",
                    "rgba(153, 102, 255, 0.6)"
                ]
            }]
        },
        "options": {
            "indexAxis": "y",
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "企业投资信号灯评分"
                }
            }
        }
    }
    
    chart_url = f"https://quickchart.io/chart?c={json.dumps(chart_config)}"
    
    return {
        "success": True,
        "chart_url": chart_url,
        "chart_data": chart_config
    }


async def generate_process_flowchart(steps: List[str]) -> Dict[str, Any]:
    """
    生成补贴申领流程图
    
    Args:
        steps: ["注册登录", "提交资料", "审核", "发放补贴"]
    
    Returns:
        流程图配置
    """
    # 使用mermaid格式生成流程图
    mermaid_code = "graph LR\n"
    for i, step in enumerate(steps):
        if i < len(steps) - 1:
            mermaid_code += f"    {chr(65+i)}[{step}] --> {chr(65+i+1)}[{steps[i+1]}]\n"
    
    # QuickChart支持Mermaid图表
    chart_url = f"https://quickchart.io/chart?cht=gv&chl={mermaid_code}"
    
    return {
        "success": True,
        "chart_url": chart_url,
        "mermaid_code": mermaid_code
    }
