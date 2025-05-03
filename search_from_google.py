import re
import json
import requests
import warnings
from datetime import datetime
from openai import OpenAI
import os
from expand_paper import get_paper_metadata_by_id
from dotenv import load_dotenv

load_dotenv()

# 配置OpenAI客户端
def get_openai_client(base_url, api_key):
    return OpenAI(
        base_url=base_url,
        api_key=api_key
    )

# 从OpenAI获取查询改写
def get_query_rewrites(client, user_query):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a query rewriting assistant. Users will provide an academic query, and you need to generate at least 5 different rewritten versions to better retrieve relevant papers. Please return in the following format: [search]rewritten query 1\n[search]rewritten query 2\n[search]rewritten query 3\n[search]rewritten query 4\n[search]rewritten query 5\n[stopsearch]"},
                {"role": "user", "content": f"Please generate 5 rewritten versions for the following academic query: {user_query}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"获取查询改写时出错: {e}")
        return None

# 解析改写后的查询
def parse_rewrites(rewrites_text):
    if not rewrites_text:
        return []
    
    queries = []
    for line in rewrites_text.strip().split('\n'):
        if line.startswith('[search]'):
            query = line.replace('[search]', '').strip()
            if query:
                queries.append(query)
        elif line.startswith('[stopsearch]'):
            break
    
    return queries[:5]  # 确保最多返回5个查询

# Google搜索获取arXiv ID
def google_search_arxiv_id(query, num=10, end_date=None, google_key=None):
    url = "https://google.serper.dev/search"

    search_query = f"{query} site:arxiv.org"
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')
            search_query = f"{query} before:{end_date} site:arxiv.org"
        except:
            search_query = f"{query} site:arxiv.org"
    
    payload = json.dumps({
        "q": search_query, 
        "num": num, 
        "page": 1, 
    })

    headers = {
        'X-API-KEY': google_key,
        'Content-Type': 'application/json'
    }
    assert headers['X-API-KEY'] is not None, "请提供Google搜索API密钥!"

    for _ in range(3):
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:
                results = json.loads(response.text)
                arxiv_id_list = []
                for paper in results.get('organic', []):
                    if re.search(r'arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d+)', paper["link"]):
                        arxiv_id = re.search(r'arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d+)', paper["link"]).group(1)
                        arxiv_id_list.append(arxiv_id)
                return list(set(arxiv_id_list))
        except Exception as e:
            warnings.warn(f"Google搜索失败，查询: {query}, 错误: {e}")
            continue
    return []

# 主函数
def search_arxiv_papers(user_query, openai_base_url, openai_api_key, google_key, num_results=10, end_date=None):
    # 初始化OpenAI客户端
    client = get_openai_client(openai_base_url, openai_api_key)
    
    # 获取查询改写
    rewrites_text = get_query_rewrites(client, user_query)
    
    # 解析改写后的查询
    queries = parse_rewrites(rewrites_text)
    
    if not queries:
        print("无法获取有效的查询改写")
        return []
    
    # 打印改写后的查询
    print("改写后的查询:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    # 对每个改写后的查询进行搜索
    all_arxiv_ids = []
    for query in queries[:2]:
        arxiv_ids = google_search_arxiv_id(query, num=num_results, end_date=end_date, google_key=google_key)
        all_arxiv_ids.extend(arxiv_ids)
    
    # 去重
    unique_arxiv_ids = list(set(all_arxiv_ids))
    
    return unique_arxiv_ids

# 示例使用
if __name__ == "__main__":
    # 从环境变量或配置文件中获取密钥
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    google_key = os.getenv("GOOGLE_KEY", "your-google-api-key")
    
    # 用户查询示例
    user_query = input("请输入您的学术查询: ")
    
    # 搜索论文
    arxiv_ids = search_arxiv_papers(user_query, openai_base_url, openai_api_key, google_key)
    
    # 打印结果
    print("\n找到的arXiv论文ID:")
    for i, arxiv_id in enumerate(arxiv_ids, 1):
        md = get_paper_metadata_by_id(arxiv_id)

        print(f"{i}. {arxiv_id} - {md['title']}")
    
    print(f"\n总共找到 {len(arxiv_ids)} 篇相关论文")