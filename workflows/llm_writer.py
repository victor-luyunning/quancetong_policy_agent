# workflows/llm_writer.py - LLM润色生成最终回答
import os
import json
import httpx
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

API_BASE = os.getenv("DASHSCOPE_API_BASE_URL", "")
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
CHAT_MODEL = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen3-235b-a22b-instruct-2507")


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
        if workflow_result.get('time_now'):
            context_parts.append(f"当前时间：{workflow_result['time_now']}")
        if workflow_result.get('conditions'):
            context_parts.append(f"申请条件：{workflow_result['conditions']}")
        if workflow_result.get('procedures'):
            context_parts.append(f"办理流程：{workflow_result['procedures']}")
        if workflow_result.get('required_materials'):
            context_parts.append(f"所需材料：{workflow_result['required_materials']}")
        if workflow_result.get('claiming_platform'):
            context_parts.append(f"申领平台：{workflow_result['claiming_platform']}")
        
        # 命中政策总览（为LLM融合提供完整上下文）
        all_hits = workflow_result.get('all_hits', [])
        if all_hits:
            context_parts.append("\n## 命中政策总览（整合输出）")
            for h in all_hits:
                title = h.get('title') or '未知'
                start = h.get('effective_start') or ''
                end = h.get('effective_end') or ''
                period = f"{start} 至 {end}".strip() if (start or end) else '未知'
                context_parts.append(
                    f"- {title}（时间：{period}，补贴：{h.get('benefit_amount') or '未知'}，渠道：{h.get('claiming_platform') or '未知'}）"
                )
        
        # 主政策状态（结合时间MCP）
        all_hits_for_status = workflow_result.get('all_hits', [])
        if all_hits_for_status and (workflow_result.get('active_hits') or workflow_result.get('inactive_hits')):
            active_ids_s = set(workflow_result.get('active_hits', []))
            inactive_ids_s = set(workflow_result.get('inactive_hits', []))
            primary = all_hits_for_status[0]
            pid = primary.get('doc_id') or primary.get('title') or ''
            status = '有效' if pid in active_ids_s else ('已失效' if pid in inactive_ids_s else '未知')
            context_parts.append(f"主政策状态：{status}")
        
        # 合并所有命中政策（用于LLM综合分析）
        all_hits = workflow_result.get('all_hits', [])
        if all_hits:
            context_parts.append("\n## 相关命中政策（供综合参考）")
            # 时间校验信息
            if workflow_result.get('time_now'):
                context_parts.append(f"当前时间：{workflow_result['time_now']}")
            active_ids = set(workflow_result.get('active_hits', []))
            inactive_ids = set(workflow_result.get('inactive_hits', []))
            for h in all_hits:
                period = ""
                if h.get('effective_start') or h.get('effective_end'):
                    start = h.get('effective_start') or ''
                    end = h.get('effective_end') or ''
                    period = f"{start} 至 {end}".strip()
                hid = h.get('doc_id') or h.get('title') or ''
                status = "有效" if hid in active_ids else ("已失效" if hid in inactive_ids else "未知")
                context_parts.append(
                    f"- 标题：{h.get('title') or '未知'}；时间：{period or '未知'}；状态：{status}；补贴：{h.get('benefit_amount') or '未知'}；渠道：{h.get('claiming_platform') or '未知'}；流程：{h.get('procedures') or '未知'}；地区：{(h.get('region_city') or '')} {h.get('region_province') or ''}".strip()
                )
    
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
    system_prompt = """你是一个政策咨询智能体的文本生成模块。你需要根据结构化数据，生成友好、专业、易懂且“人性化”的中文回答。

输出风格要求：
1. 用自然段落表达，先给结论再解释，不要输出标题、列表符号或表格；不要复述上下文中的提示语（如“政策解析结果/命中政策总览/相关命中政策”等）。
2. 融合多条或多轮政策时，按时间顺序简洁归纳（例如：上半年…；5-6月首保…；7-9月三轮…），避免逐条硬列出。
3. 重点突出关键信息：当前状态（结合当前时间与有效/失效）、申领渠道、所需材料、办理流程、金额或档位（如未明确请说明“尚未明确”）。
4. 严禁编造：仅基于结构化数据内容；如信息缺失请以“尚未明确”或“以官方公告为准”表述。
5. 字数控制在200-350字，语言友好、简洁，不使用技术化措辞。
6. 若结构化数据提示“主政策状态：已失效或未知”，不得使用“仍在有效期内/正在实施”等措辞，需明确提醒政策已截止或无法确认。
7. 若存在多轮次或多条命中，必须整合输出，禁止仅选取第一条。
8. 当当前时间晚于政策有效期结束时间时，需明确标注“已截止/历史活动”，避免使用“正在实施/仍在有效期内”的表述。
9. 禁止输出QuickChart或其他第三方图表服务的URL链接，图表将由系统自动处理并展示。"""

    user_prompt = f"""用户查询：{raw_text}

结构化数据（仅供参考，不要原样复制）：
{context}

生成要求：
- 请输出1-3段自然语言说明，不要出现“政策解析结果/命中政策总览/相关命中政策”等上下文标题，也不要用项目符号或表格。
- 若存在多轮次或多条政策命中，请整合并按时间顺序简洁归纳，禁止仅取第一条。
- 严格依据提供的“当前时间”和“状态（有效/已失效/未知）”进行表述；若失效或未知，禁止使用“正在实施/仍在有效期内”。
- 明确申请渠道、所需材料和流程，金额或档位如未明确请说明“尚未明确”。
- 不要编造超出结构化数据的信息。

请生成友好的回答："""
    
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30) as client:
            content = ""
            ok = False
            # 优先尝试 OpenAI 兼容模式
            if API_BASE and ("compatible-mode" in API_BASE):
                url1 = f"{API_BASE}/chat/completions"
                payload1 = {
                    "model": CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                try:
                    r1 = await client.post(url1, headers=headers, json=payload1)
                    if r1.status_code == 200:
                        data = r1.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        ok = True
                except Exception:
                    ok = False
            # 兼容模式不可用或失败时，回退到 DashScope 原生接口
            if not ok:
                base2 = API_BASE or "https://dashscope.aliyuncs.com"
                url2 = f"{base2}/v1/services/aigc/text-generation/generation"
                payload2 = {
                    "model": CHAT_MODEL,
                    "input": {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    },
                    "parameters": {
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                }
                r2 = await client.post(url2, headers=headers, json=payload2)
                r2.raise_for_status()
                data = r2.json()
                # 兼容多种返回结构
                content = (
                    data.get("output", {}).get("text") or
                    data.get("choices", [{}])[0].get("message", {}).get("content", "") or
                    json.dumps(data, ensure_ascii=False)
                )
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
