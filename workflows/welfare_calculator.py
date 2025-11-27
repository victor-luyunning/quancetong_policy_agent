# workflows/welfare_calculator.py - 个人福利计算
import json
from typing import Dict, Any
from .rag_retriever import retrieve_policies


async def calculate_welfare(raw_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    个人福利计算工作流
    
    返回格式（扁平化）：
    {
        "subsidy_amount": float,         # 可领金额
        "subsidy_breakdown": str,        # 补贴明细
        "total_benefit": float,          # 总福利
        "constraints": str,              # 约束条件
        "required_materials": str,       # 所需材料
        "claiming_platform": str,        # 申领平台
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
    
    if not kb_hits:
        return {
            "subsidy_amount": 0,
            "subsidy_breakdown": "未找到匹配政策",
            "total_benefit": 0,
            "constraints": None,
            "required_materials": None,
            "claiming_platform": None,
            "kb_citations": "",
            "error": "未找到相关政策"
        }
    
    # 获取价格信息
    price_paid = entities.get("price_paid")
    if not price_paid:
        return {
            "subsidy_amount": 0,
            "subsidy_breakdown": "缺少购买价格信息，无法计算",
            "total_benefit": 0,
            "constraints": kb_hits[0].get("conditions"),
            "required_materials": kb_hits[0].get("required_materials"),
            "claiming_platform": kb_hits[0].get("claiming_platform"),
            "kb_citations": kb_citations,
            "error": "缺少价格信息"
        }
    
    # 根据第一条政策计算补贴
    top_hit = kb_hits[0]
    
    # 提取补贴规则（简化计算）
    # 实际应从 kb_hits 的原始数据中提取计算规则
    # 这里先用简单规则演示
    
    subsidy_amount = 0
    breakdown_parts = []
    
    # 示例：家电补贴 = 15% + 5%（以旧换新）
    if entities.get("industry") == "appliance":
        base_rate = 0.15
        trade_in_rate = 0.05
        
        base_subsidy = price_paid * base_rate
        trade_in_subsidy = price_paid * trade_in_rate
        
        subsidy_amount = base_subsidy + trade_in_subsidy
        breakdown_parts.append(f"基础补贴15%: {base_subsidy:.2f}元")
        breakdown_parts.append(f"以旧换新5%: {trade_in_subsidy:.2f}元")
        
        # 上限限制（从政策中提取）
        if "2000" in (top_hit.get("benefit_amount") or ""):
            if subsidy_amount > 2000:
                subsidy_amount = 2000
                breakdown_parts.append("（已达上限2000元）")
    
    elif entities.get("industry") == "digital":
        # 数码产品补贴规则
        base_rate = 0.10
        subsidy_amount = price_paid * base_rate
        breakdown_parts.append(f"购新补贴10%: {subsidy_amount:.2f}元")
        
        # 上限
        if subsidy_amount > 500:
            subsidy_amount = 500
            breakdown_parts.append("（已达上限500元）")
    
    elif entities.get("industry") == "car":
        # 汽车补贴规则（固定金额）
        subsidy_amount = 5000  # 示例
        breakdown_parts.append(f"置换补贴: {subsidy_amount:.2f}元")
    
    else:
        # 其他行业
        subsidy_amount = 0
        breakdown_parts.append("暂无补贴规则")
    
    subsidy_breakdown = "; ".join(breakdown_parts)
    
    return {
        "subsidy_amount": round(subsidy_amount, 2),
        "subsidy_breakdown": subsidy_breakdown,
        "total_benefit": round(subsidy_amount, 2),
        "constraints": top_hit.get("conditions"),
        "required_materials": top_hit.get("required_materials"),
        "claiming_platform": top_hit.get("claiming_platform"),
        "kb_citations": kb_citations,
        "all_hits": kb_hits
    }
