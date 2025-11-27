from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import json
from typing import Optional, Dict, Any

# 导入原有工作流模块
from workflows.intent_parser import parse_intent
from workflows.policy_parser import parse_policy
from workflows.welfare_calculator import calculate_welfare
from workflows.regional_comparator import compare_regions
from workflows.company_signal import analyze_company_signal
from workflows.llm_writer import generate_final_text

# 导入MCP工具编排器
from mcp_tools.tool_orchestrator import MCPToolOrchestrator

app = FastAPI(title="泉策通智能体服务（集成MCP）", version="2.1")

# 初始化MCP工具编排器
mcp_orchestrator = MCPToolOrchestrator()


class QueryRequest(BaseModel):
    """统一查询请求"""
    query: str
    user_context: Optional[Dict[str, Any]] = None
    enable_mcp: bool = True  # 是否启用MCP工具增强


class QueryResponse(BaseModel):
    """统一查询响应（增强版）"""
    success: bool
    intent: str
    raw_text: str
    entities: Dict[str, Any]
    result: Dict[str, Any]
    final_answer: str
    citations: Optional[str] = None
    error: Optional[str] = None
    
    # MCP增强字段
    mcp_enhancements: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    统一智能体查询接口（MCP增强版）
    
    工作流：
    1. 检查上下文相关性（Context7）
    2. 意图解析（LLM）
    3. 根据意图路由到对应工作流
    4. 决策是否需要MCP工具增强
    5. 执行MCP工具（QuickChart、Amap、Fetch）
    6. LLM润色生成最终回答
    7. 保存对话历史
    """
    try:
        raw_text = request.query.strip()
        if not raw_text:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        # Step 0: 上下文检查（如果启用MCP）
        context_info = None
        if request.enable_mcp:
            from mcp_tools.context_manager import check_context_relevance
            context_info = await check_context_relevance(raw_text, mcp_orchestrator.context_manager)
            
            # 如果需要上下文，融合历史信息
            if context_info.get("need_context") and context_info.get("related_conversation"):
                related = context_info["related_conversation"]
                raw_text = f"[上下文] 之前问题: {related['query']}\n当前问题: {raw_text}"
        
        # Step 1: 意图解析（LLM驱动）
        intent_result = await parse_intent(raw_text)
        intent = intent_result.get("intent")
        entities = {
            "location": intent_result.get("entity_location"),
            "product": intent_result.get("entity_product"),
            "company": intent_result.get("entity_company"),
            "industry": intent_result.get("entity_industry"),
            "time": intent_result.get("entity_time"),
            "price_paid": intent_result.get("price_paid"),
            "energy_level": intent_result.get("energy_efficiency_level")
        }
        
        # Step 2: 工作流路由
        workflow_result = {}
        kb_citations = ""
        
        if intent == "policy_parse":
            workflow_result = await parse_policy(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        elif intent == "personal_welfare":
            workflow_result = await calculate_welfare(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        elif intent == "regional_compare":
            workflow_result = await compare_regions(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        elif intent == "investment_signal":
            workflow_result = await analyze_company_signal(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        else:
            raise HTTPException(status_code=400, detail=f"未知意图: {intent}")
        
        # Step 3: MCP工具增强（如果启用）
        mcp_enhancements = None
        if request.enable_mcp:
            # 3.1 决策需要使用的工具
            tools_to_use = await mcp_orchestrator.decide_tools_to_use(
                intent, entities, workflow_result
            )
            
            # 3.2 执行工具
            if tools_to_use:
                mcp_enhancements = await mcp_orchestrator.execute_tools(
                    tools_to_use, intent, entities, workflow_result, raw_text
                )
        
        # Step 4: LLM润色生成最终回答（融合MCP结果）
        final_answer = await generate_final_text(
            intent=intent,
            raw_text=raw_text,
            entities=entities,
            workflow_result=workflow_result,
            kb_citations=kb_citations
        )
        
        # 如果有图表，在回答中添加提示
        if mcp_enhancements and mcp_enhancements.get("quickchart"):
            charts = mcp_enhancements["quickchart"]
            chart_hints = []
            for chart_type, chart_data in charts.items():
                if chart_data.get("success"):
                    chart_hints.append(f"\n📊 {chart_type}图表: {chart_data.get('chart_url')}")
            if chart_hints:
                final_answer += "\n\n" + "".join(chart_hints)
        
        # 如果有地图，添加地图提示
        if mcp_enhancements and mcp_enhancements.get("amap"):
            amap_data = mcp_enhancements["amap"]
            if amap_data.get("success"):
                final_answer += f"\n\n🗺️ 产业分布地图: 已标注{amap_data.get('total_markers', 0)}个企业"
        
        # Step 5: 保存对话历史
        conversation_id = None
        if request.enable_mcp:
            conversation_id = mcp_orchestrator.save_conversation(
                raw_text, intent, workflow_result
            )
        
        # 返回统一响应
        return QueryResponse(
            success=True,
            intent=intent,
            raw_text=request.query,
            entities=entities,
            result=workflow_result,
            final_answer=final_answer,
            citations=kb_citations,
            mcp_enhancements=mcp_enhancements,
            conversation_id=conversation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] {error_detail}")
        
        return QueryResponse(
            success=False,
            intent="unknown",
            raw_text=request.query,
            entities={},
            result={},
            final_answer=f"处理失败: {str(e)}",
            error=str(e)
        )


@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "泉策通智能体（MCP增强）",
        "version": "2.1",
        "mcp_tools": ["quickchart", "amap", "fetch", "context7"]
    }


@app.get("/")
def root():
    """根路径"""
    return {
        "service": "泉策通智能体服务（MCP增强版）",
        "version": "2.1",
        "endpoints": {
            "query": "POST /query",
            "health": "GET /health"
        },
        "mcp_enhancements": {
            "quickchart": "图表生成（对比图、柱状图、流程图）",
            "amap": "地图可视化（产业分布）",
            "fetch": "实时政策更新",
            "context7": "上下文对话管理"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
