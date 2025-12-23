import os
import json
import httpx
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from .quickchart_agent import generate_comparison_chart, generate_company_score_chart
from .mermaid_agent import generate_mermaid_flowchart
from .amap_agent import generate_industry_map, get_city_boundary
from .fetch_agent import fetch_latest_policy, check_policy_updates
from .context_manager import ContextManager, check_context_relevance
from .time_agent import get_current_time, validate_policy_periods

load_dotenv()

API_BASE = os.getenv("DASHSCOPE_API_BASE_URL", "")
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
CHAT_MODEL = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus")

# 时间MCP（用于时间感知校验）
MCP_TIME_URL = "https://mcp.api-inference.modelscope.net/487f79a94fb641/mcp"


class MCPToolOrchestrator:
    """MCP工具编排器（多智能体协调）"""
    
    def __init__(self):
        self.context_manager = ContextManager()
    
    async def decide_tools_to_use(self, intent: str, entities: Dict, workflow_result: Dict) -> List[str]:
        """
        决策需要使用哪些MCP工具（大模型驱动）
        
        Args:
            intent: 意图
            entities: 实体
            workflow_result: 工作流结果
        
        Returns:
            需要调用的工具列表 ["quickchart", "amap", "fetch", "context7", "time"]
        """
        # 构建决策prompt
        prompt = f"""你是一个智能工具调度助手，需要判断以下查询需要使用哪些辅助工具。

可用工具：
1. quickchart - 生成图表（对比图、柱状图、流程图）
2. amap - 地图可视化（产业分布地图）
3. fetch - 实时政策查询更新
4. context7 - 上下文对话管理

当前查询信息：
- 意图: {intent}
- 实体: {json.dumps(entities, ensure_ascii=False)}
- 工作流结果类型: {list(workflow_result.keys())}

判断规则：
- 如果是区域对比(regional_compare)或企业信号灯(investment_signal)且有多个数据点 -> 需要quickchart
- 如果是企业信号灯且需要展示地理分布 -> 需要amap
- 如果查询包含"最新""更新""现在"等时间词 -> 需要fetch
- 如果查询包含"刚才""那个""继续"等上下文词 -> 需要context7

请严格按JSON格式输出：
{{
    "tools": ["tool1", "tool2"],
    "reasoning": "选择原因"
}}"""

        try:
            url = f"{API_BASE}/chat/completions"
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": "你是工具决策助手，只返回JSON格式结果。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                tools = result.get("tools", [])
                # 强制为政策解析加入时间MCP
                if intent == "policy_parse" and "time" not in tools:
                    tools.append("time")
                return tools
        except Exception as e:
            print(f"[工具决策] LLM调用失败: {e}")
            # 降级为规则决策
            return self._fallback_tool_decision(intent, entities, workflow_result)
    
    def _fallback_tool_decision(self, intent: str, entities: Dict, workflow_result: Dict) -> List[str]:
        """降级规则决策"""
        tools = []
        
        # 规则1: 区域对比 -> quickchart
        if intent == "regional_compare" and workflow_result.get("comparison_table"):
            tools.append("quickchart")
        
        # 规则2: 企业信号灯 -> quickchart + amap
        if intent == "investment_signal" and workflow_result.get("recommended_companies"):
            tools.append("quickchart")
            if len(workflow_result.get("recommended_companies", [])) > 0:
                tools.append("amap")
        
        # 规则3: 政策解析 -> 可选fetch（检查是否需要实时更新）
        if intent == "policy_parse":
            # 时间感知：默认加入time校验（判断命中政策是否在有效期内）
            tools.append("time")
            # 暂不默认调用fetch
            pass
        
        return tools
    
    async def execute_tools(
        self,
        tools: List[str],
        intent: str,
        entities: Dict,
        workflow_result: Dict,
        raw_query: str
    ) -> Dict[str, Any]:
        """
        执行选定的MCP工具
        
        Returns:
            {
                "quickchart": {...},
                "amap": {...},
                "fetch": {...},
                "context7": {...}
            }
        """
        results = {}
        
        # 执行QuickChart
        if "quickchart" in tools:
            results["quickchart"] = await self._execute_quickchart(intent, workflow_result)
        
        # 执行Amap
        if "amap" in tools:
            results["amap"] = await self._execute_amap(intent, workflow_result)
        
        # 执行Fetch
        if "fetch" in tools:
            results["fetch"] = await self._execute_fetch(entities)
        
        # 执行Time（时间感知）
        if "time" in tools:
            results["time"] = await self._execute_time_validation(workflow_result)
        
        return results
    
    async def _execute_quickchart(self, intent: str, workflow_result: Dict) -> Dict[str, Any]:
        """执行图表生成"""
        charts = {}
        
        if intent == "regional_compare":
            # 区域对比图（雷达图）
            comparison_table = workflow_result.get("comparison_table", [])
            if comparison_table:
                chart_data = [
                    {"category": item["region"], "value": self._extract_amount(item.get("benefit_amount", "0"))}
                    for item in comparison_table
                ]
                charts["comparison"] = await generate_comparison_chart(chart_data, "radar")
        
        elif intent == "investment_signal":
            # 企业评分柱状图
            companies = workflow_result.get("recommended_companies", [])
            if companies:
                charts["company_scores"] = await generate_company_score_chart(
                    [{"name": c["company_name"], "score": c["total_score"]} for c in companies[:5]]
                )
        
        elif intent == "policy_parse":
            # 申领流程图（使用Mermaid）
            procedures = workflow_result.get("procedures")
            if procedures:
                steps = procedures.split("→") if "→" in procedures else procedures.split(";")
                charts["process_flow"] = await generate_mermaid_flowchart(steps[:6], "LR")
        
        return charts
    
    async def _execute_amap(self, intent: str, workflow_result: Dict) -> Dict[str, Any]:
        """执行地图生成"""
        if intent == "investment_signal":
            companies = workflow_result.get("recommended_companies", [])
            if companies:
                # 构建地图数据
                map_data = []
                for comp in companies[:10]:
                    location = comp.get("location", "")
                    city = location.split()[1] if len(location.split()) > 1 else ""
                    map_data.append({
                        "name": comp["company_name"],
                        "city": city,
                        "industry": comp.get("industry", ""),
                        "score": comp.get("total_score", 0)
                    })
                
                return await generate_industry_map(map_data)
        
        return {}
    
    async def _execute_fetch(self, entities: Dict) -> Dict[str, Any]:
        """执行实时政策抓取"""
        keyword = f"{entities.get('location', '')} {entities.get('product', '')} 补贴政策"
        return await fetch_latest_policy(keyword.strip())
    
    async def _execute_context7(self, raw_query: str) -> Dict[str, Any]:
        """执行上下文查询"""
        return await check_context_relevance(raw_query, self.context_manager)
    
    async def _execute_time_validation(self, workflow_result: Dict) -> Dict[str, Any]:
        """调用时间MCP并校验政策有效期（封装于 time_agent）"""
        try:
            all_hits = workflow_result.get("all_hits") or []
            res = await validate_policy_periods(all_hits)
            if res.get("success"):
                return res
            # 失败时也返回当前时间（若可获取）
            now_res = await get_current_time()
            if now_res.get("success"):
                res["now"] = now_res.get("now")
            return res
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_amount(self, amount_str: str) -> float:
        """从补贴金额字符串中提取数值"""
        import re
        if not amount_str:
            return 0
        match = re.search(r'(\d+)', amount_str)
        return float(match.group(1)) if match else 0
    
    def save_conversation(self, query: str, intent: str, result: Dict[str, Any]) -> str:
        """保存对话记录"""
        return self.context_manager.save_conversation(query, intent, result)
