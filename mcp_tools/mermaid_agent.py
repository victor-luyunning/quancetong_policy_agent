import httpx
import json
import urllib.parse
from typing import Dict, Any, List

MCP_MERMAID_URL = "https://mcp.api-inference.modelscope.net/e6c6353933ea44/mcp"


async def generate_mermaid_flowchart(steps: List[str], flow_type: str = "LR") -> Dict[str, Any]:
    """
    使用Mermaid MCP生成流程图
    
    Args:
        steps: 流程步骤列表 ["注册登录", "提交资料", "审核", "发放补贴"]
        flow_type: 流程方向 LR(左右)/TD(上下)/RL(右左)/BT(下上)
    
    Returns:
        {"success": bool, "chart_url": str, "mermaid_code": str}
    """
    try:
        # 构建Mermaid代码
        mermaid_code = f"graph {flow_type}\n"
        
        # 为每个步骤生成节点
        for i, step in enumerate(steps):
            node_id = chr(65 + i)  # A, B, C, ...
            # 简化步骤名称（避免过长）
            step_name = step.strip().replace("审核流程：", "").replace("企业流程：", "")[:15]
            
            if i == 0:
                # 第一个节点（开始）
                mermaid_code += f"    {node_id}([{step_name}])\n"
            elif i == len(steps) - 1:
                # 最后一个节点（结束）
                mermaid_code += f"    {node_id}[/{step_name}/]\n"
            else:
                # 中间节点
                mermaid_code += f"    {node_id}[{step_name}]\n"
        
        # 添加连接线
        for i in range(len(steps) - 1):
            current = chr(65 + i)
            next_node = chr(65 + i + 1)
            mermaid_code += f"    {current} --> {next_node}\n"
        
        # 添加样式
        mermaid_code += f"""
    classDef startEnd fill:#5DADE2,stroke:#2874A6,stroke-width:2px,color:#fff
    classDef process fill:#52BE80,stroke:#27AE60,stroke-width:2px,color:#fff
    class A startEnd
    class {chr(65 + len(steps) - 1)} startEnd
"""
        
        # 使用QuickChart渲染Mermaid
        # QuickChart支持Mermaid: https://quickchart.io/documentation/mermaid/
        encoded_mermaid = urllib.parse.quote(mermaid_code)
        chart_url = f"https://quickchart.io/chart?cht=mermaid&chl={encoded_mermaid}&w=800&h=300"
        
        return {
            "success": True,
            "chart_url": chart_url,
            "mermaid_code": mermaid_code,
            "flow_type": flow_type
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def generate_mermaid_sequence(participants: List[str], interactions: List[Dict]) -> Dict[str, Any]:
    """
    生成时序图（适合展示多方交互流程）
    
    Args:
        participants: 参与者列表 ["用户", "系统", "审核员"]
        interactions: 交互列表 [{"from": "用户", "to": "系统", "message": "提交申请"}]
    
    Returns:
        图表配置和URL
    """
    try:
        mermaid_code = "sequenceDiagram\n"
        
        # 声明参与者
        for p in participants:
            mermaid_code += f"    participant {p}\n"
        
        # 添加交互
        for interaction in interactions:
            from_p = interaction.get("from", "")
            to_p = interaction.get("to", "")
            msg = interaction.get("message", "")
            mermaid_code += f"    {from_p}->>{to_p}: {msg}\n"
        
        encoded_mermaid = urllib.parse.quote(mermaid_code)
        chart_url = f"https://quickchart.io/chart?cht=mermaid&chl={encoded_mermaid}&w=800&h=400"
        
        return {
            "success": True,
            "chart_url": chart_url,
            "mermaid_code": mermaid_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
