#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比测试 DeepSeek-V3 和 Qwen-Max 使用MCP联网搜索增强的表现
"""

import os
import json
import csv
import time
from datetime import datetime
import requests
from openai import OpenAI

# 从环境变量获取配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_BASE_URL = os.getenv("DASHSCOPE_API_BASE_URL")

# 政策知识库文件路径
KNOWLEDGE_BASE_PATH = "data/policies/总知识库.md"

def load_local_knowledge():
    """加载本地政策知识库"""
    try:
        with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"  ⚠️ 加载知识库失败: {e}")
        return ""

def extract_relevant_knowledge(question, knowledge_base, max_length=2000):
    """从知识库中提取相关内容（简单关键词匹配）"""
    import re
    
    # 提取问题中的关键词
    keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', question)
    
    # 分段知识库
    sections = knowledge_base.split('\n\n')
    
    # 找出包含关键词的段落
    relevant_sections = []
    for section in sections:
        score = sum(1 for keyword in keywords if keyword in section)
        if score > 0:
            relevant_sections.append((score, section))
    
    # 按相关度排序
    relevant_sections.sort(reverse=True, key=lambda x: x[0])
    
    # 拼接最相关的内容
    result = ""
    for score, section in relevant_sections[:5]:  # 取前5个最相关的段落
        if len(result) + len(section) > max_length:
            break
        result += section + "\n\n"
    
    return result.strip()

def load_test_questions(json_file="test_questions_dataset.json"):
    """加载测试问题"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_with_knowledge_base(question, model_name, api_key=DASHSCOPE_API_KEY):
    """使用本地知识库增强测试模型"""
    try:
        # 1. 直接加载整份知识库（不做任何文本处理）
        print(f"    📚 从本地知识库加载全文...")
        
        # 首次调用时加载知识库
        if not hasattr(test_with_knowledge_base, 'knowledge_base'):
            test_with_knowledge_base.knowledge_base = load_local_knowledge()
        
        knowledge_base = test_with_knowledge_base.knowledge_base
        
        if knowledge_base:
            print(f"    ✅ 知识库已加载，长度 {len(knowledge_base)} 字符")
            # 不做任何截断、切分、关键词抽取，直接作为上下文传给模型
            context = "\n\n以下是政策知识库全文：\n" + knowledge_base
        else:
            print(f"    ⚠️ 知识库为空")
            context = ""
        
        enhanced_question = f"""{context}

基于以上政策信息，请回答以下问题：
{question}

请给出准确简洁的答案，重点关注具体的金额、时间、档位等关键信息。"""
        
        # 3. 调用LLM
        client = OpenAI(
            api_key=api_key,
            base_url=DASHSCOPE_API_BASE_URL
        )
        
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的政策咨询助手，帮助用户查询山东省和济南市的消费补贴政策。请基于提供的信息给出准确的答案。"
                },
                {
                    "role": "user",
                    "content": enhanced_question
                }
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        response_time = time.time() - start_time
        
        return {
            "status": "success",
            "answer": response.choices[0].message.content,
            "response_time": response_time,
            "model": model_name,
            "knowledge_used": len(context) > 0,
            "error": ""
        }
    
    except Exception as e:
        return {
            "status": "error",
            "answer": "",
            "response_time": 0,
            "model": model_name,
            "knowledge_used": False,
            "error": str(e)
        }

def evaluate_answer(expected, actual):
    """简单评估答案（关键词匹配）"""
    if not actual:
        return "错误", "答案为空"
    
    # 提取关键数字和关键词
    import re
    expected_nums = set(re.findall(r'\d+', expected))
    actual_nums = set(re.findall(r'\d+', actual))
    
    expected_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', expected))
    actual_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', actual))
    
    # 数字匹配度
    num_match = len(expected_nums & actual_nums) / len(expected_nums) if expected_nums else 0
    
    # 关键词匹配度
    keyword_match = len(expected_keywords & actual_keywords) / len(expected_keywords) if expected_keywords else 0
    
    overall_score = (num_match + keyword_match) / 2
    
    if overall_score >= 0.7:
        return "正确", f"匹配度{overall_score*100:.0f}%"
    elif overall_score >= 0.4:
        return "部分正确", f"匹配度{overall_score*100:.0f}%"
    else:
        return "错误", f"匹配度低({overall_score*100:.0f}%)"

def main():
    print("="*80)
    print("🔬 Moonshot-Kimi-K2-Instruct + 本地知识库测试")
    print("="*80)
    print(f"模型: Moonshot-Kimi-K2-Instruct")
    print(f"增强方式: 本地政策知识库")
    print(f"知识库路径: {KNOWLEDGE_BASE_PATH}")
    print(f"API Key: {'已配置' if DASHSCOPE_API_KEY else '未配置'}")
    print("="*80 + "\n")
    
    # 加载测试问题
    questions = load_test_questions()
    print(f"📝 加载了 {len(questions)} 个测试问题\n")
    
    # 准备结果存储
    results = []
    
    # 对每个问题进行测试
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] 测试问题 #{q['id']}")
        print(f"问题: {q['question']}")
        print(f"预期: {q['expected_answer'][:50]}...")
        
        # 测试 GPT-4 Turbo（单次）
        print(f"\n  🔵 GPT-4 Turbo + 知识库...")
        gpt4_result = test_with_knowledge_base(q['question'], "Moonshot-Kimi-K2-Instruct")
        if gpt4_result['status'] == 'success':
            kb_status = "使用知识库" if gpt4_result['knowledge_used'] else "无知识库"
            print(f"  ✅ 完成 ({gpt4_result['response_time']:.2f}秒, {kb_status})")
            gpt4_eval, gpt4_reason = evaluate_answer(q['expected_answer'], gpt4_result['answer'])
            print(f"  评估: {gpt4_eval} - {gpt4_reason}")
        else:
            print(f"  ❌ 失败: {gpt4_result['error']}")
            gpt4_eval, gpt4_reason = "错误", gpt4_result['error']
        
        # 保存结果
        results.append({
            'id': q['id'],
            'question': q['question'],
            'expected_answer': q['expected_answer'],
            'category': q['category'],
            'campaign_id': q['campaign_id'],
            
            'gpt4_answer': gpt4_result['answer'],
            'gpt4_time': gpt4_result['response_time'],
            'gpt4_status': gpt4_result['status'],
            'gpt4_knowledge_used': gpt4_result['knowledge_used'],
            'gpt4_evaluation': gpt4_eval,
            'gpt4_reason': gpt4_reason,
            'gpt4_error': gpt4_result['error']
        })
        
        # 短暂延迟避免频率限制
        time.sleep(2)
    
    # 保存结果到CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = "model_evaluate"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, f"mcp_comparison_results_{timestamp}.csv")
    
    fieldnames = [
        'id', 'question', 'expected_answer', 'category', 'campaign_id',
        'gpt4_answer', 'gpt4_time', 'gpt4_status', 'gpt4_knowledge_used',
        'gpt4_evaluation', 'gpt4_reason', 'gpt4_error'
    ]
    
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n\n✅ 测试完成！结果已保存到: {output_csv}")
    
    # 统计
    gpt4_correct = sum(1 for r in results if r['gpt4_evaluation'] in ['正确', '部分正确'])
    gpt4_success = [r for r in results if r['gpt4_status'] == 'success']
    gpt4_avg_time = sum(r['gpt4_time'] for r in gpt4_success) / len(gpt4_success) if gpt4_success else 0
    
    print(f"\n📊 统计:")
    print(f"  准确率: {gpt4_correct}/{len(results)} ({gpt4_correct/len(results)*100:.1f}%)")
    print(f"  平均响应时间: {gpt4_avg_time:.2f}秒")
    print(f"  成功率: {len(gpt4_success)}/{len(results)}")

if __name__ == "__main__":
    main()
