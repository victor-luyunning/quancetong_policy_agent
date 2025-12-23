import httpx
import json
from typing import Dict, Any, List

MCP_QUICKCHART_URL = "https://mcp.api-inference.modelscope.net/1765b0ae2e674b/mcp"


async def generate_comparison_chart(data: List[Dict], chart_type: str = "radar") -> Dict[str, Any]:
    """
    生成对比图表（区域政策对比、企业评分对比等）- 雷达图版
    
    Args:
        data: 对比数据 [{"category": "济南", "value": 2000}, {"category": "青岛", "value": 1800}]
        chart_type: 图表类型 radar/column/bar
    
    Returns:
        {"success": bool, "chart_url": str, "chart_data": dict}
    """
    try:
        import urllib.parse
        
        # 渐变色配色方案
        colors = [
            "rgba(52, 152, 219, 0.6)",  # 蓝色
            "rgba(46, 204, 113, 0.6)",  # 绿色
            "rgba(155, 89, 182, 0.6)",  # 紫色
            "rgba(241, 196, 15, 0.6)",  # 黄色
            "rgba(231, 76, 60, 0.6)"    # 红色
        ]
        
        # 雷达图配置
        if chart_type == "radar":
            chart_config = {
                "type": "radar",
                "data": {
                    "labels": [item["category"] for item in data],
                    "datasets": [{
                        "label": "补贴金额（元）",
                        "data": [item["value"] for item in data],
                        "backgroundColor": "rgba(52, 152, 219, 0.2)",
                        "borderColor": "rgba(52, 152, 219, 1)",
                        "borderWidth": 2,
                        "pointBackgroundColor": "rgba(52, 152, 219, 1)",
                        "pointBorderColor": "#fff",
                        "pointHoverBackgroundColor": "#fff",
                        "pointHoverBorderColor": "rgba(52, 152, 219, 1)"
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "📊 区域政策补贴对比（雷达图）",
                            "font": {
                                "size": 18,
                                "weight": "bold"
                            },
                            "color": "#2c3e50",
                            "padding": 20
                        },
                        "legend": {
                            "display": True,
                            "position": "bottom"
                        }
                    },
                    "scales": {
                        "r": {
                            "beginAtZero": True,
                            "ticks": {
                                "font": {"size": 11}
                            },
                            "grid": {
                                "color": "rgba(0, 0, 0, 0.1)"
                            },
                            "pointLabels": {
                                "font": {"size": 12, "weight": "bold"}
                            }
                        }
                    }
                }
            }
        else:
            # 柱状图配置（降级方案）
            chart_config = {
                "type": chart_type,
                "data": {
                    "labels": [item["category"] for item in data],
                    "datasets": [{
                        "label": "补贴金额（元）",
                        "data": [item["value"] for item in data],
                        "backgroundColor": colors[:len(data)],
                        "borderColor": [c.replace('0.6', '1') for c in colors[:len(data)]],
                        "borderWidth": 2,
                        "borderRadius": 8
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "📊 区域政策补贴对比",
                            "font": {
                                "size": 18,
                                "weight": "bold"
                            },
                            "color": "#2c3e50",
                            "padding": 20
                        },
                        "legend": {
                            "display": True,
                            "position": "bottom"
                        }
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True,
                            "ticks": {
                                "font": {"size": 11}
                            },
                            "grid": {
                                "color": "rgba(0, 0, 0, 0.05)"
                            }
                        },
                        "x": {
                            "ticks": {"font": {"size": 12}}
                        }
                    }
                }
            }
        
        chart_json = json.dumps(chart_config, ensure_ascii=False)
        chart_url = f"https://quickchart.io/chart?w=600&h=400&c={urllib.parse.quote(chart_json)}"
        
        return {
            "success": True,
            "chart_url": chart_url,
            "chart_type": chart_type,
            "chart_data": chart_config
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def generate_company_score_chart(companies: List[Dict]) -> Dict[str, Any]:
    """
    生成企业评分柱状图（横向柱状图，渐变配色）
    
    Args:
        companies: [{"name": "海尔", "score": 85}, {"name": "美的", "score": 78}]
    
    Returns:
        图表配置和URL
    """
    import urllib.parse
    
    # 渐变配色（从高到低）
    gradient_colors = [
        "rgba(231, 76, 60, 0.85)",    # 红色系（第1名）
        "rgba(230, 126, 34, 0.85)",   # 橙色系（第2名）
        "rgba(241, 196, 15, 0.85)",   # 黄色系（第3名）
        "rgba(52, 152, 219, 0.85)",   # 蓝色系（第4名）
        "rgba(155, 89, 182, 0.85)"    # 紫色系（第5名）
    ]
    
    # 企业名称简化（避免过长）
    labels = []
    for c in companies:
        name = c["name"]
        if len(name) > 20:
            name = name[:18] + "..."
        labels.append(name)
    
    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "综合评分",
                "data": [c["score"] for c in companies],
                "backgroundColor": gradient_colors[:len(companies)],
                "borderColor": [c.replace('0.85', '1') for c in gradient_colors[:len(companies)]],
                "borderWidth": 2,
                "borderRadius": 6
            }]
        },
        "options": {
            "indexAxis": "y",
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "🏆 企业投资信号灯评分排行",
                    "font": {
                        "size": 18,
                        "weight": "bold"
                    },
                    "color": "#2c3e50",
                    "padding": 20
                },
                "legend": {
                    "display": False
                }
            },
            "scales": {
                "x": {
                    "beginAtZero": True,
                    "max": 100,
                    "ticks": {
                        "font": {"size": 11}
                    },
                    "grid": {
                        "color": "rgba(0, 0, 0, 0.05)"
                    }
                },
                "y": {
                    "ticks": {
                        "font": {"size": 11}
                    }
                }
            }
        }
    }
    
    chart_json = json.dumps(chart_config, ensure_ascii=False)
    chart_url = f"https://quickchart.io/chart?w=700&h=450&c={urllib.parse.quote(chart_json)}"
    
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
