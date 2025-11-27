# workflows/llm_writer.py - LLM润色生成最终回答
import os
import json
import httpx
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

API_BASE = os.getenv("DASHSCOPE_API_BASE_URL", "")
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
CHAT_MODEL = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus")


async def generate_final_text(
    intent: str,
    raw_text: str,
    entities: Dict[str, Any],
    workflow_result: Dict[str, Any],
    kb_citations: str
) -> str:
    """
    使用LLM生成最终用户可读的回答
    
    根据不同意图使用不同的模板
    """
    
    # 构建上下文信息
    context_parts = []
    
    if intent == "policy_parse":
        # 政策解析模板
        context_parts.append("## 政策解析结果")
        context_parts.append(f"政策名称：{workflow_result.get('policy_title', '未知')}")
        context_parts.append(f"福利类型：{workflow_result.get('benefit_type', '未知')}")
        context_parts.append(f"补贴金额：{workflow_result.get('benefit_amount', '未知')}")
        context_parts.append(f"适用地区：{workflow_result.get('region', '未知')}")
        context_parts.append(f"有效期：{workflow_result.get('effective_period', '未知')}")
        if workflow_result.get('conditions'):
            context_parts.append(f"申请条件：{workflow_result['conditions']}")
        if workflow_result.get('procedures'):
            context_parts.append(f"办理流程：{workflow_result['procedures']}")
        if workflow_result.get('required_materials'):
            context_parts.append(f"所需材料：{workflow_result['required_materials']}")
        if workflow_result.get('claiming_platform'):
            context_parts.append(f"申领平台：{workflow_result['claiming_platform']}")
    
    elif intent == "personal_welfare":
        # 福利计算模板
        context_parts.append("## 福利计算结果")
        context_parts.append(f"您可获得补贴：{workflow_result.get('subsidy_amount', 0)}元")
        context_parts.append(f"补贴明细：{workflow_result.get('subsidy_breakdown', '无')}")
        if workflow_result.get('constraints'):
            context_parts.append(f"限制条件：{workflow_result['constraints']}")
        if workflow_result.get('required_materials'):
            context_parts.append(f"所需材料：{workflow_result['required_materials']}")
        if workflow_result.get('claiming_platform'):
            context_parts.append(f"申领平台：{workflow_result['claiming_platform']}")
    
    elif intent == "regional_compare":
        # 区域对比模板
        context_parts.append("## 区域政策对比")
        context_parts.append(f"对比地区：{', '.join(workflow_result.get('regions_compared', []))}")
        context_parts.append(f"对比总结：{workflow_result.get('summary', '无')}")
        
        # 对比表格
        comparison_table = workflow_result.get('comparison_table', [])
        if comparison_table:
            context_parts.append("\n详细对比：")
            for item in comparison_table:
                context_parts.append(f"- {item['region']}：{item['benefit_amount']}")
    
    elif intent == "investment_signal":
        # 企业投资信号灯模板
        context_parts.append("## 企业投资分析")
        context_parts.append(f"投资信号：{workflow_result.get('investment_signal', '黄灯')}")
        context_parts.append(f"行业概况：{workflow_result.get('industry_summary', '无')}")
        
        # 推荐企业
        recommended = workflow_result.get('recommended_companies', [])
        if recommended:
            context_parts.append("\n推荐企业Top 5：")
            for comp in recommended[:5]:
                context_parts.append(
                    f"- {comp['company_name']}（{comp['location']}）"
                    f"，评分：{comp['total_score']}，扩展意愿：{comp['expansion_willingness']}"
                )
    
    context = "\n".join(context_parts)
    
    # 构建LLM Prompt
    system_prompt = """你是一个政策咨询智能体的文本生成模块。你需要根据结构化数据，生成友好、专业、易懂的用户回答。

要求：
1. 语言友好，避免生硬的技术术语
2. 重点突出关键信息（补贴金额、申请条件、平台等）
3. 如果有引用来源，务必在末尾注明
4. 不要编造信息，严格基于提供的数据
5. 字数控制在200-300字"""

    user_prompt = f"""用户查询：{raw_text}

结构化数据：
{context}

请生成友好的回答："""
    
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
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            # 提取LLM返回的文本
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 添加引用（如果有）
            if kb_citations:
                content += f"\n\n📚 参考来源：{kb_citations.replace('|', ', ')}"
            
            return content.strip()
            
    except Exception as e:
        print(f"[LLM Writer] 调用失败: {e}")
        # 降级：直接返回结构化数据
        fallback = context
        if kb_citations:
            fallback += f"\n\n参考来源：{kb_citations}"
        return fallback
