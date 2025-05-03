import json

def extract_relevant_papers(input_file, output_file, threshold=0.5):
    # 读取原始JSON数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取搜索到的论文和扩展的论文
    all_papers = data['search_papers'] + data['expanded_papers']
    
    # 筛选相关性分数大于阈值的论文
    relevant_papers = []
    for paper in all_papers:
        # 检查论文是否有相关性分数且大于阈值
        if 'relevance_score' in paper and paper['relevance_score'] > threshold:
            # 创建一个新的论文对象，不包含嵌套的引文关系
            relevant_paper = {
                'title': paper['title'],
                'arxiv_id': paper['arxiv_id'],
                'abstract': paper['abstract'],
                'relevance_score': paper['relevance_score'],
                'source': paper.get('source', 'Not specified')
            }
            
            # 如果有部分内容，也包括它们
            if 'sections' in paper and paper['sections']:
                relevant_paper['sections'] = paper['sections']
            
            relevant_papers.append(relevant_paper)
    
    # 按相关性分数从高到低排序
    relevant_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # 创建输出数据结构
    output_data = {
        'user_query': data['user_query'],
        'relevant_papers': relevant_papers,
        'metadata': {
            'total_relevant_papers': len(relevant_papers),
            'relevance_threshold': threshold,
            'original_total_papers': len(all_papers)
        }
    }
    
    # 保存到新的JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"已提取 {len(relevant_papers)} 篇相关性分数大于 {threshold} 的论文，并保存到 {output_file}")
    return output_data

# 执行提取操作
extract_relevant_papers('single_query_result.json', 'relevant_papers.json')