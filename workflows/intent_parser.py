# workflows/intent_parser.py - 意图解析（LLM驱动）
import os
import json
import re
import httpx
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

API_BASE = os.getenv("DASHSCOPE_API_BASE_URL", "")
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
CHAT_MODEL = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus")


async def parse_intent(raw_text: str) -> Dict[str, Any]:
    """
    使用大模型进行意图识别和实体抽取
    
    返回格式（扁平化JSON）：
    {
        "intent": "policy_parse" | "personal_welfare" | "regional_compare" | "investment_signal",
        "entity_location": str | None,
        "entity_product": str | None,
        "entity_company": str | None,
        "entity_industry": str | None,
        "entity_time": str | None,
        "price_paid": float | None,
        "energy_efficiency_level": str | None
    }
    """
    
    # 构建LLM Prompt
    system_prompt = """你是一个政策咨询智能体的意图识别模块。你需要分析用户查询，识别意图并提取实体信息。

**意图类型（4种）**：
1. policy_parse（政策智能解析）：查询政策内容、申请条件、申请流程、截止时间等
2. personal_welfare（个人福利计算）：计算个人能领多少补贴，通常包含购买价格信息
3. regional_compare（区域政策对比）：对比不同地区的政策差异
4. investment_signal（企业投资信号灯）：评估企业适配性、招商推荐

**实体类型**：
- entity_location：地点（济南、青岛、山东省等）
- entity_product：产品（空调、手机、汽车等）
- entity_company：公司名称
- entity_industry：行业（appliance/digital/car/retail_catering）
- entity_time：时间（2025年、今年等）
- price_paid：购买价格（数值，单位：元）
- energy_efficiency_level：能效等级（一级能效、二级能效等）

**输出要求**：
必须严格按照JSON格式输出，不要有任何其他文字。格式如下：
{
    "intent": "意图类型",
    "entity_location": "地点或null",
    "entity_product": "产品或null",
    "entity_company": "公司或null",
    "entity_industry": "行业或null",
    "entity_time": "时间或null",
    "price_paid": 价格数值或null,
    "energy_efficiency_level": "能效等级或null"
}

**行业识别规则**：
- appliance（家电）：冰箱、洗衣机、电视、空调、热水器、油烟机等
- digital（数码）：手机、平板、智能手表、手环等
- car（汽车）：新能源汽车、燃油车、新车、乘用车等
- retail_catering（零售餐饮）：零售、餐饮、消费券等

**价格提取规则**：
- "花了3000元" -> 3000
- "2.5万" -> 25000
- 没有价格信息时返回null"""

    user_prompt = f"用户查询：{raw_text}\n\n请分析并输出JSON："
    
    try:
        url = f"{API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            # 提取LLM返回的JSON
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            result = json.loads(content)
            
            # 验证必要字段
            if "intent" not in result:
                result["intent"] = "policy_parse"
            
            # 确保所有字段存在
            default_result = {
                "intent": "policy_parse",
                "entity_location": None,
                "entity_product": None,
                "entity_company": None,
                "entity_industry": None,
                "entity_time": None,
                "price_paid": None,
                "energy_efficiency_level": None
            }
            default_result.update(result)
            
            return default_result
            
    except Exception as e:
        print(f"[意图解析] LLM调用失败: {e}")
        # 降级为简单规则识别
        return _fallback_intent_parse(raw_text)


def _fallback_intent_parse(raw_text: str) -> Dict[str, Any]:
    """降级方案：基于规则的意图识别"""
    intent = "policy_parse"
    
    # 简单规则判断
    if any(kw in raw_text for kw in ["能领多少", "补贴金额", "买了", "花了"]) and re.search(r'\d+', raw_text):
        intent = "personal_welfare"
    elif any(kw in raw_text for kw in ["对比", "比较", "哪个好"]):
        intent = "regional_compare"
    elif any(kw in raw_text for kw in ["企业", "公司", "招商", "投资"]) and "我们" not in raw_text:
        intent = "investment_signal"
    
    # 实体提取
    location_match = re.search(r"(济南|青岛|烟台|潍坊|淄博|临沂|济宁|威海|泰安|日照|德州|滨州|聊城|菏泽|东营|枣庄|山东省|山东)", raw_text)
    product_match = re.search(r"(家电|冰箱|洗衣机|电视|空调|手机|平板|智能手表|手环|汽车|新能源汽车|零售|餐饮)", raw_text)
    company_match = re.search(r"(小米|华为|比亚迪|海尔|格力|美的|海信)", raw_text)
    time_match = re.search(r"(2025年|2026年|今年|明年)", raw_text)
    
    price_match = re.search(r"(\d+\.?\d*)\s*(万)?元", raw_text)
    price_paid = None
    if price_match:
        price_val = float(price_match.group(1))
        price_paid = price_val * 10000 if price_match.group(2) else price_val
    
    energy_match = re.search(r"(一级|二级|三级)能效", raw_text)
    energy_level = energy_match.group(0) if energy_match else None
    
    # 行业识别
    industry = None
    if any(kw in raw_text for kw in ["冰箱", "洗衣机", "电视", "空调", "家电"]):
        industry = "appliance"
    elif any(kw in raw_text for kw in ["手机", "平板", "智能手表", "手环"]):
        industry = "digital"
    elif any(kw in raw_text for kw in ["汽车", "新能源汽车", "燃油车"]):
        industry = "car"
    elif any(kw in raw_text for kw in ["零售", "餐饮", "消费券"]):
        industry = "retail_catering"
    
    return {
        "intent": intent,
        "entity_location": location_match.group(0) if location_match else None,
        "entity_product": product_match.group(0) if product_match else None,
        "entity_company": company_match.group(0) if company_match else None,
        "entity_industry": industry,
        "entity_time": time_match.group(0) if time_match else None,
        "price_paid": price_paid,
        "energy_efficiency_level": energy_level
    }
