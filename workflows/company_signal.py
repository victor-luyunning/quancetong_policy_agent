# workflows/company_signal.py - 企业投资信号灯
import os
import json
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
COMPANY_FILES = {
    "appliance": os.path.join(DATA_DIR, "companies", "companies_appliance.jsonl"),
    "digital": os.path.join(DATA_DIR, "companies", "companies_digital.jsonl"),
    "car": os.path.join(DATA_DIR, "companies", "companies_auto.jsonl"),
    "retail_catering": os.path.join(DATA_DIR, "companies", "companies_retail.jsonl")
}


def _load_companies(industry: str) -> List[Dict[str, Any]]:
    """加载企业库"""
    if industry not in COMPANY_FILES:
        return []
    
    fpath = COMPANY_FILES[industry]
    if not os.path.exists(fpath):
        print(f"[企业信号灯] 企业文件不存在: {fpath}")
        return []
    
    companies = []
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                companies.append(obj)
            except Exception as e:
                print(f"[企业信号灯] 解析企业数据失败: {e}")
                continue
    return companies


def _score_company(company: Dict[str, Any]) -> float:
    """企业评分（简化版）"""
    score = 0.0
    
    # 创新分
    innovation = company.get("innovation_score", 0)
    score += innovation * 0.3
    
    # 扩展意愿
    expansion = company.get("expansion_willingness", "low")
    if expansion == "high":
        score += 30
    elif expansion == "medium":
        score += 15
    
    # 渠道数量
    channels = len(company.get("existing_channels", []))
    score += min(channels * 5, 20)
    
    return round(score, 2)


async def analyze_company_signal(raw_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    企业投资信号灯工作流
    
    返回格式（扁平化）：
    {
        "recommended_companies": List[Dict],  # 推荐企业列表
        "industry_summary": str,              # 行业总结
        "investment_signal": str,             # 信号灯（红/黄/绿）
        "kb_citations": str
    }
    """
    
    industry = entities.get("industry")
    location = entities.get("location") or "山东省"
    
    if not industry:
        return {
            "recommended_companies": [],
            "industry_summary": "未指定行业",
            "investment_signal": "黄灯",
            "kb_citations": "",
            "error": "缺少行业信息"
        }
    
    # 加载企业库
    companies = _load_companies(industry)
    
    if not companies:
        return {
            "recommended_companies": [],
            "industry_summary": f"{industry}行业暂无企业数据",
            "investment_signal": "黄灯",
            "kb_citations": ""
        }
    
    # 过滤地域（如果有）
    filtered = []
    for comp in companies:
        comp_city = comp.get("city", "")
        comp_province = comp.get("province", "")
        if location in comp_city or location in comp_province or comp_city in location or comp_province in location:
            filtered.append(comp)
    
    # 如果地域过滤后为空，使用全部
    if not filtered:
        filtered = companies
    
    # 计算评分并排序
    for comp in filtered:
        comp["score"] = _score_company(comp)
    
    filtered.sort(key=lambda x: x["score"], reverse=True)
    
    # 取Top 10
    top_companies = filtered[:10]
    
    # 构建推荐列表
    recommended = []
    for comp in top_companies:
        recommended.append({
            "company_name": comp.get("name"),
            "industry": comp.get("industry"),
            "location": f"{comp.get('province')} {comp.get('city')}",
            "main_products": ", ".join(comp.get("main_products", [])),
            "innovation_score": comp.get("innovation_score"),
            "expansion_willingness": comp.get("expansion_willingness"),
            "total_score": comp.get("score")
        })
    
    # 行业总结
    avg_score = sum(c["score"] for c in top_companies) / len(top_companies) if top_companies else 0
    industry_summary = f"{industry}行业共{len(companies)}家企业，平均评分{avg_score:.2f}，推荐Top {len(top_companies)}家"
    
    # 投资信号灯
    if avg_score >= 70:
        investment_signal = "绿灯（推荐投资）"
    elif avg_score >= 40:
        investment_signal = "黄灯（谨慎评估）"
    else:
        investment_signal = "红灯（暂不建议）"
    
    return {
        "recommended_companies": recommended,
        "industry_summary": industry_summary,
        "investment_signal": investment_signal,
        "kb_citations": ""
    }
