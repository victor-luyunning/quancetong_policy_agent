# workflows/policy_parser.py - 政策智能解析
from typing import Dict, Any
from .rag_retriever import retrieve_policies


async def parse_policy(raw_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    政策智能解析工作流
    
    返回格式（扁平化）：
    {
        "policy_title": str,
        "benefit_type": str,
        "benefit_amount": str,
        "region": str,
        "effective_period": str,
        "conditions": str,
        "procedures": str,
        "required_materials": str,
        "claiming_platform": str,
        "kb_citations": str
    }
    """
    
    # 调用RAG检索
    rag_result = await retrieve_policies(
        raw_text=raw_text,
        entity_location=entities.get("location"),
        entity_product=entities.get("product"),
        entity_industry=entities.get("industry"),
        entity_time=entities.get("time"),
        top_k=5
    )
    
    kb_hits = rag_result.get("kb_hits", [])
    kb_citations = rag_result.get("kb_citations", "")
    
    # 如果没有命中，返回空结果
    if not kb_hits:
        return {
            "policy_title": None,
            "benefit_type": None,
            "benefit_amount": None,
            "region": None,
            "effective_period": None,
            "conditions": None,
            "procedures": None,
            "required_materials": None,
            "claiming_platform": None,
            "kb_citations": "",
            "error": "未找到相关政策"
        }
    
    # 取第一条作为主要结果
    top_hit = kb_hits[0]
    
    # 构建地域信息
    region_parts = []
    if top_hit.get("region_city"):
        region_parts.append(top_hit["region_city"])
    if top_hit.get("region_province"):
        region_parts.append(top_hit["region_province"])
    region = " ".join(region_parts) if region_parts else None
    
    # 构建有效期
    effective_period = None
    if top_hit.get("effective_start") and top_hit.get("effective_end"):
        effective_period = f"{top_hit['effective_start']} 至 {top_hit['effective_end']}"
    
    return {
        "policy_title": top_hit.get("title"),
        "benefit_type": top_hit.get("benefit_type"),
        "benefit_amount": top_hit.get("benefit_amount"),
        "region": region,
        "effective_period": effective_period,
        "conditions": top_hit.get("conditions"),
        "procedures": top_hit.get("procedures"),
        "required_materials": top_hit.get("required_materials"),
        "claiming_platform": top_hit.get("claiming_platform"),
        "kb_citations": kb_citations,
        "all_hits": kb_hits  # 保留所有命中结果供LLM参考
    }
