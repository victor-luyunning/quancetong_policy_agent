# workflows/rag_retriever.py - RAG检索模块（统一政策+补充政策）
import os
import json
import httpx
import math
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

API_BASE = os.getenv("DASHSCOPE_API_BASE_URL", "")
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
EMBED_MODEL = os.getenv("DASHSCOPE_EMBED_MODEL", "text-embedding-v3")

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
POLICY_FILE = os.path.join(DATA_DIR, "policies", "policies.jsonl")
SUPPLEMENT_DIRS = {
    "appliance": os.path.join(DATA_DIR, "policies", "家电补贴政策"),
    "digital": os.path.join(DATA_DIR, "policies", "数码补贴政策"),
    "car": os.path.join(DATA_DIR, "policies", "汽车补贴政策"),
    "retail_catering": os.path.join(DATA_DIR, "policies", "零售餐饮补贴政策")
}


def _load_policies() -> List[Dict[str, Any]]:
    """加载主政策库（policies.jsonl）"""
    items = []
    if not os.path.exists(POLICY_FILE):
        print(f"[RAG] 警告：主政策文件不存在 {POLICY_FILE}")
        return items
    
    with open(POLICY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
            except Exception as e:
                print(f"[RAG] 解析JSONL失败: {e}")
                continue
    return items


def _load_supplement_policies(industry: str) -> List[str]:
    """加载补充政策文档（Markdown文件）"""
    if industry not in SUPPLEMENT_DIRS:
        return []
    
    supp_dir = SUPPLEMENT_DIRS[industry]
    if not os.path.exists(supp_dir):
        return []
    
    texts = []
    for fname in os.listdir(supp_dir):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(supp_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    texts.append({
                        "source": "supplement",
                        "title": fname.replace(".md", ""),
                        "content": content[:2000]  # 截取前2000字符
                    })
        except Exception:
            continue
    return texts


def _derive_region(campaign_id: str) -> Dict[str, str]:
    """从campaign_id推导地域"""
    if not campaign_id:
        return {"region_province": None, "region_city": None}
    if campaign_id.startswith("JN_"):
        return {"region_province": "山东省", "region_city": "济南市"}
    if campaign_id.startswith("SD_"):
        return {"region_province": "山东省", "region_city": None}
    return {"region_province": None, "region_city": None}


def _derive_benefit(obj: Dict[str, Any]) -> Dict[str, Any]:
    """提取福利信息"""
    name = obj.get("name")
    benefit_type = "补贴"
    benefit_amount = None
    
    common = obj.get("common_rules", {})
    std = (common or {}).get("subsidy_standard", {})
    price_cap = std.get("price_cap")
    if price_cap:
        benefit_amount = f"上限{price_cap}元"
    
    cid = obj.get("campaign_id", "")
    if "RETAIL_CATERING" in cid:
        benefit_type = "满减券"
        brackets = std.get("brackets", [])
        if brackets:
            b = brackets[0]
            benefit_amount = f"满{b.get('threshold')}减{b.get('reduction')}元"
    
    return {
        "title": name,
        "benefit_type": benefit_type,
        "benefit_amount": benefit_amount,
        "claiming_platform": (obj.get("claiming_platform") or "")
    }


def _doc_text(obj: Dict[str, Any]) -> str:
    """拼接用于向量化的文本"""
    parts = [
        obj.get("name") or "",
        json.dumps(obj.get("common_rules") or {}, ensure_ascii=False)
    ]
    return "\n".join([p for p in parts if p])


def _cosine(a: List[float], b: List[float]) -> float:
    """余弦相似度"""
    if not a or not b:
        return 0.0
    s = sum(ai * bi for ai, bi in zip(a, b))
    sa = math.sqrt(sum(ai * ai for ai in a))
    sb = math.sqrt(sum(bi * bi for bi in b))
    return (s / (sa * sb)) if (sa and sb) else 0.0


async def _embed_batch(texts: List[str]) -> List[List[float]]:
    """批量向量化"""
    if not API_BASE or not API_KEY:
        return [[0.0] * 10 for _ in texts]
    
    url = f"{API_BASE}/embeddings"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": EMBED_MODEL, "input": texts}
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload)
            jj = r.json()
            vecs = [item.get("embedding") for item in jj.get("data", [])]
            if len(vecs) == len(texts):
                return vecs
            return [[0.0] * 10 for _ in texts]
    except Exception as e:
        print(f"[RAG] 向量化失败: {e}")
        return [[0.0] * 10 for _ in texts]


def _filter_by_entities(
    items: List[Dict[str, Any]],
    entity_location: str = None,
    entity_product: str = None,
    entity_industry: str = None
) -> List[Dict[str, Any]]:
    """实体过滤"""
    if not items:
        return items
    
    if not entity_location and not entity_product and not entity_industry:
        return items
    
    industry_prefixes = {
        "appliance": ["APPLIANCE"],
        "digital": ["DIGITAL"],
        "car": ["CAR"],
        "retail_catering": ["RETAIL_CATERING"]
    }
    
    filtered = []
    for obj in items:
        cid = obj.get("campaign_id", "")
        region = _derive_region(cid)
        ok = True
        
        # 行业过滤
        if entity_industry:
            prefixes = industry_prefixes.get(entity_industry, [])
            industry_match = any(prefix in cid for prefix in prefixes)
            ok = ok and industry_match
        
        # 地域过滤
        if entity_location:
            loc = entity_location
            city = region.get("region_city") or ""
            province = region.get("region_province") or ""
            platform = obj.get("claiming_platform") or ""
            region_match = (
                loc in city or city in loc or
                loc in province or province in loc or
                loc in platform
            )
            ok = ok and region_match
        
        # 产品过滤
        if entity_product and ok:
            products = ((obj.get("common_rules") or {}).get("subsidy_products") or [])
            if products:
                product_match = any(entity_product in p for p in products)
                ok = ok and product_match
            else:
                ok = False
        
        if ok:
            filtered.append(obj)
    
    return filtered


async def retrieve_policies(
    raw_text: str,
    entity_location: str = None,
    entity_product: str = None,
    entity_industry: str = None,
    entity_time: str = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    统一RAG检索接口
    
    返回格式（扁平化）：
    {
        "kb_hits": List[Dict],  # 命中的政策列表
        "kb_citations": str      # 引用URL（|分隔）
    }
    """
    
    # 1. 加载主政策库
    items = _load_policies()
    candidates = _filter_by_entities(
        items,
        entity_location=entity_location,
        entity_product=entity_product,
        entity_industry=entity_industry
    )
    
    # 2. 向量召回
    texts = [_doc_text(o) for o in candidates]
    query_vec, *doc_vecs = await _embed_batch([raw_text] + texts)
    
    scored = []
    for o, dv in zip(candidates, doc_vecs):
        sim = _cosine(query_vec, dv)
        reg = _derive_region(o.get("campaign_id", ""))
        bene = _derive_benefit(o)
        
        # 提取详细信息
        common_rules = o.get("common_rules", {})
        claiming_platform = common_rules.get("claiming_platform") or ""
        required_docs = common_rules.get("required_documents", [])
        
        # 提取条件、流程、材料
        conditions = []
        std = common_rules.get("subsidy_standard", {})
        if std.get("energy_efficiency_requirement"):
            conditions.append(f"能效要求：{std['energy_efficiency_requirement']}")
        if std.get("quantity_limit"):
            ql = std["quantity_limit"]
            if ql.get("per_category"):
                conditions.append(f"每类限购{ql['per_category']}台")
        
        qual_rules = common_rules.get("qualification_rules", {})
        if qual_rules.get("real_name_auth"):
            conditions.append("实名认证")
        
        conditions_text = "; ".join(conditions) if conditions else None
        
        # 办理流程
        procedures = []
        audit = o.get("audit_process", [])
        if audit:
            procedures.append("审核流程：" + " → ".join(audit))
        procedures_text = " | ".join(procedures) if procedures else None
        
        # 所需材料
        materials_map = {
            "ID": "身份证明",
            "old_appliance_recycle_certificate": "旧机回收凭证",
            "new_purchase_invoice": "购买发票",
            "bank_account": "银行账户"
        }
        materials = [materials_map.get(doc, doc) for doc in required_docs]
        materials_text = ", ".join(materials) if materials else None
        
        hit = {
            "doc_id": o.get("campaign_id"),
            "title": bene.get("title"),
            "summary": bene.get("title"),
            "region_province": reg.get("region_province"),
            "region_city": reg.get("region_city"),
            "effective_start": o.get("start_date"),
            "effective_end": o.get("end_date"),
            "benefit_type": bene.get("benefit_type"),
            "benefit_amount": bene.get("benefit_amount"),
            "conditions": conditions_text,
            "procedures": procedures_text,
            "required_materials": materials_text,
            "claiming_platform": claiming_platform,
            "source_url": None,
            "score": round(sim, 6)
        }
        scored.append(hit)
    
    # 3. 排序与Top-K
    scored.sort(key=lambda x: x["score"], reverse=True)
    hits = scored[:top_k]
    
    # 4. 补充政策（可选）
    # 如果主库命中少于3条，从补充库召回
    if len(hits) < 3 and entity_industry:
        supplements = _load_supplement_policies(entity_industry)
        # 这里简化处理，补充政策作为文本提示，不做向量检索
        # 实际应用中可以进一步向量化
    
    citations = [h["source_url"] for h in hits if h.get("source_url")]
    kb_citations = "|".join(sorted(set([c for c in citations if c])))
    
    return {
        "kb_hits": hits,
        "kb_citations": kb_citations
    }
