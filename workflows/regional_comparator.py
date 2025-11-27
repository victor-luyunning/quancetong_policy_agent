# workflows/regional_comparator.py - 区域政策对比
from typing import Dict, Any, List
from .rag_retriever import retrieve_policies


async def compare_regions(raw_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    区域政策对比工作流
    
    返回格式（扁平化）：
    {
        "regions_compared": List[str],   # 对比的地区列表
        "comparison_table": List[Dict],  # 对比表格
        "summary": str,                  # 对比总结
        "kb_citations": str
    }
    """
    
    # 提取多个地区
    location = entities.get("location")
    if not location:
        return {
            "regions_compared": [],
            "comparison_table": [],
            "summary": "未指定对比地区",
            "kb_citations": "",
            "error": "缺少地区信息"
        }
    
    # 支持多地区（|分隔）
    regions = location.split("|") if "|" in location else [location]
    
    # 为每个地区检索政策
    comparison_results = []
    all_citations = []
    
    for region in regions:
        rag_result = await retrieve_policies(
            raw_text=raw_text,
            entity_location=region,
            entity_product=entities.get("product"),
            entity_industry=entities.get("industry"),
            entity_time=entities.get("time"),
            top_k=3
        )
        
        kb_hits = rag_result.get("kb_hits", [])
        if kb_hits:
            top_hit = kb_hits[0]
            comparison_results.append({
                "region": region,
                "policy_title": top_hit.get("title"),
                "benefit_type": top_hit.get("benefit_type"),
                "benefit_amount": top_hit.get("benefit_amount"),
                "conditions": top_hit.get("conditions"),
                "claiming_platform": top_hit.get("claiming_platform"),
                "effective_period": f"{top_hit.get('effective_start')} - {top_hit.get('effective_end')}"
            })
        else:
            comparison_results.append({
                "region": region,
                "policy_title": "未找到政策",
                "benefit_type": None,
                "benefit_amount": None,
                "conditions": None,
                "claiming_platform": None,
                "effective_period": None
            })
        
        if rag_result.get("kb_citations"):
            all_citations.append(rag_result["kb_citations"])
    
    # 生成对比总结
    summary_parts = []
    for item in comparison_results:
        if item["policy_title"] != "未找到政策":
            summary_parts.append(
                f"{item['region']}：{item['benefit_amount']}，申领平台：{item['claiming_platform']}"
            )
    
    summary = "; ".join(summary_parts) if summary_parts else "各地区暂无可对比政策"
    
    kb_citations = "|".join(all_citations) if all_citations else ""
    
    return {
        "regions_compared": regions,
        "comparison_table": comparison_results,
        "summary": summary,
        "kb_citations": kb_citations
    }
