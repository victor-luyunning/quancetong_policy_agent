#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业知识库统计分析脚本
分析家电、汽车、数码、零售餐饮四大行业企业数据
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

# 文件路径
DATA_DIR = Path("e:/25-26-2/神思杯/code/data/companies")
FILES = {
    "家电": DATA_DIR / "companies_appliance.jsonl",
    "汽车": DATA_DIR / "companies_auto.jsonl",
    "数码": DATA_DIR / "companies_digital.jsonl",
    "零售餐饮": DATA_DIR / "companies_retail.jsonl"
}

def load_companies(file_path):
    """加载企业数据"""
    companies = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                companies.append(json.loads(line))
    return companies

def analyze_companies():
    """分析企业数据"""
    results = {}
    
    for industry, file_path in FILES.items():
        print(f"正在分析 {industry} 行业...")
        companies = load_companies(file_path)
        
        # 基础统计
        total_count = len(companies)
        
        # 地域分布
        cities = Counter([c.get('city', '未知') for c in companies])
        provinces = Counter([c.get('province', '未知') for c in companies])
        
        # 注册资本统计
        capitals = [c.get('registered_capital_wan', 0) for c in companies if c.get('registered_capital_wan')]
        avg_capital = sum(capitals) / len(capitals) if capitals else 0
        max_capital = max(capitals) if capitals else 0
        min_capital = min(capitals) if capitals else 0
        
        # 评分统计
        scores = [c.get('score', 0) for c in companies if c.get('score')]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        # 创新评分统计
        innovation_scores = [c.get('innovation_score', 0) for c in companies if c.get('innovation_score')]
        avg_innovation = sum(innovation_scores) / len(innovation_scores) if innovation_scores else 0
        
        # 招聘意向评分统计
        recruitment_scores = [c.get('recruitment_intent_score', 0) for c in companies if c.get('recruitment_intent_score')]
        avg_recruitment = sum(recruitment_scores) / len(recruitment_scores) if recruitment_scores else 0
        
        # 新闻情绪评分统计
        sentiment_scores = [c.get('news_sentiment_score', 0) for c in companies if c.get('news_sentiment_score')]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # 扩张意愿统计
        expansion = Counter([c.get('expansion_willingness', '未知') for c in companies])
        
        # 渠道类型统计
        all_channels = []
        for c in companies:
            channels = c.get('existing_channels', [])
            all_channels.extend(channels)
        channel_stats = Counter(all_channels)
        
        # 企业年龄统计
        ages = [c.get('age_years', 0) for c in companies if c.get('age_years')]
        avg_age = sum(ages) / len(ages) if ages else 0
        
        # 成立时间分布
        years = []
        for c in companies:
            date_str = c.get('established_date', '')
            if date_str:
                try:
                    year = int(date_str.split('-')[0])
                    years.append(year)
                except:
                    pass
        year_dist = Counter(years)
        
        results[industry] = {
            'total_count': total_count,
            'cities': cities,
            'provinces': provinces,
            'avg_capital': avg_capital,
            'max_capital': max_capital,
            'min_capital': min_capital,
            'avg_score': avg_score,
            'max_score': max_score,
            'min_score': min_score,
            'avg_innovation': avg_innovation,
            'avg_recruitment': avg_recruitment,
            'avg_sentiment': avg_sentiment,
            'expansion': expansion,
            'channels': channel_stats,
            'avg_age': avg_age,
            'year_dist': year_dist
        }
    
    return results

def generate_summary_table(results):
    """生成汇总表格"""
    summary_data = []
    
    for industry, stats in results.items():
        row = {
            '行业': industry,
            '企业数量': stats['total_count'],
            '平均注册资本(万元)': f"{stats['avg_capital']:.2f}",
            '最高注册资本(万元)': f"{stats['max_capital']:.2f}",
            '平均综合评分': f"{stats['avg_score']:.2f}",
            '最高综合评分': f"{stats['max_score']:.2f}",
            '平均创新评分': f"{stats['avg_innovation']:.2f}",
            '平均招聘意向分': f"{stats['avg_recruitment']:.2f}",
            '平均新闻情绪分': f"{stats['avg_sentiment']:.2f}",
            '平均企业年龄(年)': f"{stats['avg_age']:.2f}",
            '高扩张意愿企业数': stats['expansion'].get('high', 0),
            '主要省份': ', '.join([f"{k}({v})" for k, v in stats['provinces'].most_common(3)]),
            '主要城市': ', '.join([f"{k}({v})" for k, v in stats['cities'].most_common(3)]),
            '主要渠道类型': ', '.join([f"{k}({v})" for k, v in stats['channels'].most_common(3)])
        }
        summary_data.append(row)
    
    # 添加总计行
    total_row = {
        '行业': '总计',
        '企业数量': sum([s['total_count'] for s in results.values()]),
        '平均注册资本(万元)': f"{sum([s['avg_capital'] for s in results.values()]) / len(results):.2f}",
        '最高注册资本(万元)': f"{max([s['max_capital'] for s in results.values()]):.2f}",
        '平均综合评分': f"{sum([s['avg_score'] for s in results.values()]) / len(results):.2f}",
        '最高综合评分': f"{max([s['max_score'] for s in results.values()]):.2f}",
        '平均创新评分': f"{sum([s['avg_innovation'] for s in results.values()]) / len(results):.2f}",
        '平均招聘意向分': f"{sum([s['avg_recruitment'] for s in results.values()]) / len(results):.2f}",
        '平均新闻情绪分': f"{sum([s['avg_sentiment'] for s in results.values()]) / len(results):.2f}",
        '平均企业年龄(年)': f"{sum([s['avg_age'] for s in results.values()]) / len(results):.2f}",
        '高扩张意愿企业数': sum([s['expansion'].get('high', 0) for s in results.values()]),
        '主要省份': '山东省为主',
        '主要城市': '济南、青岛、淄博等',
        '主要渠道类型': '线下门店、电商平台'
    }
    summary_data.append(total_row)
    
    df = pd.DataFrame(summary_data)
    return df

def generate_detailed_report(results):
    """生成详细报告"""
    report = []
    report.append("=" * 80)
    report.append("企业知识库统计分析报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    
    for industry, stats in results.items():
        report.append(f"\n## {industry}行业企业分析")
        report.append("-" * 60)
        report.append(f"企业总数: {stats['total_count']} 家")
        report.append(f"平均注册资本: {stats['avg_capital']:.2f} 万元")
        report.append(f"注册资本范围: {stats['min_capital']:.2f} - {stats['max_capital']:.2f} 万元")
        report.append(f"平均综合评分: {stats['avg_score']:.2f} 分")
        report.append(f"评分范围: {stats['min_score']:.2f} - {stats['max_score']:.2f} 分")
        report.append(f"平均创新评分: {stats['avg_innovation']:.2f} 分")
        report.append(f"平均招聘意向分: {stats['avg_recruitment']:.2f} 分")
        report.append(f"平均新闻情绪分: {stats['avg_sentiment']:.2f} 分")
        report.append(f"平均企业年龄: {stats['avg_age']:.2f} 年")
        
        report.append(f"\n扩张意愿分布:")
        for level, count in stats['expansion'].most_common():
            report.append(f"  - {level}: {count} 家")
        
        report.append(f"\n前5大城市分布:")
        for city, count in stats['cities'].most_common(5):
            report.append(f"  - {city}: {count} 家")
        
        report.append(f"\n渠道类型统计:")
        for channel, count in stats['channels'].most_common():
            report.append(f"  - {channel}: {count} 次")
        
        report.append(f"\n成立年份分布(前5年):")
        for year, count in sorted(stats['year_dist'].items(), reverse=True)[:5]:
            report.append(f"  - {year}年: {count} 家")
        
        report.append("")
    
    # 总体统计
    total_companies = sum([s['total_count'] for s in results.values()])
    report.append("\n## 总体统计")
    report.append("-" * 60)
    report.append(f"四大行业企业总数: {total_companies} 家")
    report.append(f"行业分布:")
    for industry, stats in results.items():
        percentage = (stats['total_count'] / total_companies) * 100
        report.append(f"  - {industry}: {stats['total_count']} 家 ({percentage:.2f}%)")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("开始分析企业知识库...")
    
    # 分析数据
    results = analyze_companies()
    
    # 生成汇总表格
    print("\n生成汇总表格...")
    summary_df = generate_summary_table(results)
    
    # 保存为CSV
    output_csv = DATA_DIR / "企业知识库汇总表.csv"
    summary_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"汇总表格已保存到: {output_csv}")
    
    # 打印表格
    print("\n" + "=" * 100)
    print("企业知识库汇总表")
    print("=" * 100)
    print(summary_df.to_string(index=False))
    
    # 生成详细报告
    print("\n生成详细报告...")
    report = generate_detailed_report(results)
    
    # 保存报告
    output_report = DATA_DIR / "企业知识库分析报告.txt"
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"详细报告已保存到: {output_report}")
    
    # 打印报告
    print("\n" + report)
    
    print("\n分析完成！")

if __name__ == "__main__":
    main()
