# app.py - 统一智能体入口服务
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import json
from typing import Optional, Dict, Any

# 导入各工作流模块
from workflows.intent_parser import parse_intent
from workflows.policy_parser import parse_policy
from workflows.welfare_calculator import calculate_welfare
from workflows.regional_comparator import compare_regions
from workflows.company_signal import analyze_company_signal
from workflows.llm_writer import generate_final_text

app = FastAPI(title="泉策通智能体服务", version="2.0")


class QueryRequest(BaseModel):
    """统一查询请求"""
    query: str
    user_context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """统一查询响应"""
    success: bool
    intent: str
    raw_text: str
    entities: Dict[str, Any]
    result: Dict[str, Any]
    final_answer: str
    citations: Optional[str] = None
    error: Optional[str] = None


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    统一智能体查询接口
    
    工作流：
    1. 意图解析（LLM）
    2. 根据意图路由到对应工作流
    3. LLM润色生成最终回答
    """
    try:
        raw_text = request.query.strip()
        if not raw_text:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
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
            # 政策智能解析
            workflow_result = await parse_policy(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        elif intent == "personal_welfare":
            # 个人福利计算
            workflow_result = await calculate_welfare(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        elif intent == "regional_compare":
            # 区域政策对比
            workflow_result = await compare_regions(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        elif intent == "investment_signal":
            # 企业投资信号灯
            workflow_result = await analyze_company_signal(raw_text, entities)
            kb_citations = workflow_result.get("kb_citations", "")
            
        else:
            raise HTTPException(status_code=400, detail=f"未知意图: {intent}")
        
        # Step 3: LLM润色生成最终回答
        final_answer = await generate_final_text(
            intent=intent,
            raw_text=raw_text,
            entities=entities,
            workflow_result=workflow_result,
            kb_citations=kb_citations
        )
        
        # 返回统一响应
        return QueryResponse(
            success=True,
            intent=intent,
            raw_text=raw_text,
            entities=entities,
            result=workflow_result,
            final_answer=final_answer,
            citations=kb_citations
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
        "service": "泉策通智能体",
        "version": "2.0"
    }


@app.get("/")
def root():
    """根路径"""
    return {
        "service": "泉策通智能体服务",
        "version": "2.0",
        "endpoints": {
            "query": "POST /query",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
