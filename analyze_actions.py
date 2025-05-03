import json
from collections import Counter
from typing import List, Dict
import re

def analyze_jsonl_file(file_path: str) -> Dict:
    """分析JSONL文件中的动作统计信息"""
    
    # 初始化计数器
    stats = {
        'total_entries': 0,
        'expand_count': 0,
        'search_count': 0,
        'action_sequences': [],
        'expand_patterns': Counter(),
        'search_patterns': Counter(),
        'messages_per_conversation': [],
        'sections_selected_count': Counter()
    }
    
    # 读取并分析文件
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stats['total_entries'] += 1
            data = json.loads(line)
            
            # 获取messages
            messages = data.get('messages', [])
            stats['messages_per_conversation'].append(len(messages))
            
            # 分析每条消息
            for message in messages:
                content = message.get('content', '')
                
                # 提取sections信息（在user消息中）
                if message.get('role') == 'user' and 'Sections:' in content:
                    sections = re.findall(r'"([^"]+)"', content)
                    for section in sections:
                        stats['sections_selected_count'][section] += 1
                
                # 提取动作序列（在assistant消息中）
                if message.get('role') == 'assistant':
                    actions = []
                    
                    # 统计[Expand]动作
                    expand_matches = re.findall(r'\[Expand\][^\[]*', content)
                    stats['expand_count'] += len(expand_matches)
                    for match in expand_matches:
                        stats['expand_patterns'][match.strip()] += 1
                        actions.append('Expand')
                    
                    # 统计[Search]动作
                    search_matches = re.findall(r'\[Search\][^\[]*', content)
                    stats['search_count'] += len(search_matches)
                    for match in search_matches:
                        stats['search_patterns'][match.strip()] += 1
                        actions.append('Search')
                    
                    if actions:
                        stats['action_sequences'].append('->'.join(actions))
    
    return stats

def print_statistics(stats: Dict) -> None:
    """打印统计结果"""
    print("=== 基础统计 ===")
    print(f"总对话数: {stats['total_entries']}")
    print(f"[Expand]动作总数: {stats['expand_count']}")
    print(f"[Search]动作总数: {stats['search_count']}")
    
    print("\n=== 章节选择统计 ===")
    print("最常被选择的章节 (top 10):")
    for section, count in stats['sections_selected_count'].most_common(10):
        print(f"{section}: {count}次")

def main():
    file_path = "sft_crawler/train.jsonl"
    try:
        stats = analyze_jsonl_file(file_path)
        print_statistics(stats)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
    except json.JSONDecodeError:
        print("错误: JSON解析失败")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
