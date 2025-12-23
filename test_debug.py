#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backend Debug Test Tool - Interactive Mode"""

import requests
import json
import sys

# API Configuration
API_URL = "http://146.56.198.222:8001/query"


def print_line(char="=", length=70):
    print(char * length)


def display_response(data):
    """Display all response data with detailed debugging info"""
    print_line()
    print("SUCCESS:", data.get('success', False))
    print("INTENT:", data.get('intent', 'unknown'))
    print("RAW_TEXT:", data.get('raw_text', ''))
    
    print_line("-")
    print("ENTITIES:")
    if data.get('entities'):
        for k, v in data['entities'].items():
            if v is not None:
                print(f"  {k}: {v}")
    
    print_line("-")
    print("RESULT:")
    if data.get('result'):
        result = data['result']
        if result.get('subsidy_amount') is not None:
            print(f"  Subsidy: {result['subsidy_amount']} yuan")
        if result.get('calculation_method'):
            print(f"  Method: {result['calculation_method']}")
        if result.get('procedures'):
            print(f"  Procedures: {result['procedures']}")
        if result.get('constraints'):
            print(f"  Constraints: {result['constraints']}")
        if result.get('required_materials'):
            print(f"  Materials: {result['required_materials']}")
        if result.get('claiming_platform'):
            print(f"  Platform: {result['claiming_platform']}")
        if result.get('comparison_table'):
            print(f"  Comparison: {len(result['comparison_table'])} items")
        if result.get('recommended_companies'):
            print(f"  Companies: {len(result['recommended_companies'])} found")
    
    print_line("-")
    print("FINAL ANSWER:")
    print(data.get('final_answer', 'No answer'))
    
    if data.get('citations'):
        print_line("-")
        print("CITATIONS:")
        print(data['citations'])
    
    if data.get('mcp_enhancements'):
        print_line("-")
        print("MCP ENHANCEMENTS:")
        mcp = data['mcp_enhancements']
        if mcp.get('quickchart'):
            print("  QuickChart:", list(mcp['quickchart'].keys()))
        if mcp.get('amap'):
            amap = mcp['amap']
            if amap.get('success'):
                print(f"  Amap: {amap.get('map_source', 'N/A')}")
        if mcp.get('time'):
            time_res = mcp['time']
            if time_res.get('success'):
                print("  Time:")
                print(f"    now: {time_res.get('now')}")
                print(f"    active_hits: {time_res.get('active_hits', [])}")
                print(f"    inactive_hits: {time_res.get('inactive_hits', [])}")
            else:
                print(f"  Time: failed - {time_res.get('error')}")
    
    if data.get('error'):
        print_line("!")
        print("ERROR:", data['error'])
    
    print_line()


def query_api(question):
    """Send query to backend API"""
    try:
        print(f"\nQuerying: {question}")
        print("Please wait...")
        
        response = requests.post(
            API_URL,
            json={"query": question},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            display_response(result)
            return True
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False


def main():
    """Main interactive loop"""
    print_line("*")
    print("Backend Debug Test Tool")
    print(f"API: {API_URL}")
    print("Commands: 'q' to quit, 'h' for help")
    print_line("*")
    
    examples = [
        "What subsidy policy for buying computers in Jinan?",
        "How much subsidy for 10000 yuan air conditioner in Jinan?",
        "Compare car subsidy policies between Qingdao and Jinan",
        "Recommend some quality catering companies in Jinan",
    ]
    
    while True:
        print_line("-")
        try:
            # Use simple ASCII prompt to avoid encoding issues
            question = input("\n>>> Question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['q', 'quit', 'exit']:
                print("Bye!")
                break
            
            if question.lower() in ['h', 'help']:
                print("\nExamples:")
                for i, ex in enumerate(examples, 1):
                    print(f"  {i}. {ex}")
                continue
            
            query_api(question)
            
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
