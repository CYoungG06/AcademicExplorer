import re
import json
import os
from paper_node import PaperNode
from agent import Agent
from datetime import datetime

from search_from_google import parse_rewrites, google_search_arxiv_id
from expand_paper import (
    get_paper_metadata_by_id, 
    get_paper_metadata_by_title,
    get_paper_structure, 
    get_section_citations
)

class PaperAgent:
    def __init__(
        self,
        user_query:     str,
        crawler:        Agent, # prompt(s) -> response(s)
        selector:       Agent, # prompt(s) -> score(s)
        end_date:       str = datetime.now().strftime("%Y%m%d"),
        prompts_path:   str = "prompts.json",
        expand_layers:  int = 2,
        search_queries: int = 5,
        search_papers:  int = 10, # per query
        expand_papers:  int = 20, # per layer
        google_key:     str = None
    ) -> None:
        self.user_query = user_query
        self.crawler    = crawler
        self.selector   = selector
        self.end_date   = end_date
        self.prompts    = json.load(open(prompts_path))
        self.google_key = google_key or os.getenv("GOOGLE_KEY")
        self.root       = PaperNode({
            "title": user_query,
            "extra": {
                "touch_ids": [],
                "crawler_recall_papers": [],
                "recall_papers": [],
            }
        })

        self.expand_layers   = expand_layers
        self.search_queries  = search_queries
        self.search_papers   = search_papers
        self.expand_papers   = expand_papers
        self.papers_queue    = []
        self.expand_start    = 0
        self.templates       = {
            "search_template": r"Search\](.*?)\[",
            "expand_template": r"Expand\](.*?)\["
        }
    
    def search_paper(self, queries):
        """搜索相关论文"""
        processed_queries = []
        for query in queries:
            if not query in self.root.child:
                self.root.child[query] = []
                processed_queries.append(query)
        
        for query in processed_queries:
            print(f"搜索查询: {query}")
            
            # 使用Google搜索获取arXiv ID
            arxiv_ids = google_search_arxiv_id(
                query, 
                num=self.search_papers, 
                end_date=self.end_date,
                google_key=self.google_key
            )
            
            print(f"找到 {len(arxiv_ids)} 个arXiv ID")
            
            searched_papers = []
            for arxiv_id in arxiv_ids:
                arxiv_id = arxiv_id.split('v')[0]  # 移除版本号
                
                if arxiv_id not in self.root.extra["touch_ids"]:
                    self.root.extra["touch_ids"].append(arxiv_id)
                    
                    # 使用您的函数获取论文元数据
                    paper_data = get_paper_metadata_by_id(arxiv_id)
                    if paper_data:
                        searched_papers.append({
                            "title": paper_data["title"],
                            "arxiv_id": arxiv_id,
                            "abstract": paper_data["abstract"],
                            "sections": "",  # 初始为空，按需获取
                            "source": "arxiv"
                        })
            
            # 评估论文相关性
            select_prompts = []
            for paper in searched_papers:
                prompt = self.prompts["get_selected"].format(
                    title=paper["title"], 
                    abstract=paper["abstract"], 
                    user_query=self.user_query
                )
                select_prompts.append(prompt)
            
            if select_prompts:
                scores = self.selector.infer_score(select_prompts)
                
                for i, (paper, score) in enumerate(zip(searched_papers, scores)):
                    score = score['probability']
                    print(f"评估论文 [{i+1}/{len(searched_papers)}]: {paper['title']} (分数: {score})")
                    
                    self.root.extra["crawler_recall_papers"].append(paper["title"])
                    if score > 0.5:
                        self.root.extra["recall_papers"].append(paper["title"])
                    
                    # 创建论文节点
                    paper_node = PaperNode({
                        "title":        paper["title"],
                        "arxiv_id":     paper["arxiv_id"],
                        "depth":        0,
                        "abstract":     paper["abstract"],
                        "sections":     paper["sections"],
                        "source":       "Search " + paper["source"],
                        "select_score": score,
                        "extra":        {}
                    })
                    
                    self.root.child[query].append(paper_node)
                    self.papers_queue.append(paper_node)

    def search(self):
        """执行搜索过程"""
        print(f"为查询生成搜索关键词: '{self.user_query}'")
        
        # 使用LLM生成搜索查询
        prompt = self.prompts["generate_query"].format(user_query=self.user_query).strip()
        queries_text = self.crawler.infer(prompt)
        print("生成的搜索查询:", queries_text)

        # 解析生成的查询
        queries = [q.strip() for q in re.findall(self.templates["search_template"], queries_text, flags=re.DOTALL)]
        queries = queries[:self.search_queries]
        
        if not queries:
            # 如果未能通过模板提取查询，尝试直接解析
            queries = parse_rewrites(queries_text)[:self.search_queries]
        
        print(f"生成的搜索关键词: {queries}")
        
        # 搜索每个查询
        self.search_paper(queries)

    def get_paper_content(self, paper):
        """获取论文的完整内容和章节"""
        if not paper.sections:
            print(f"获取论文章节: {paper.title} (arXiv ID: {paper.arxiv_id})")
            
            try:
                # 使用您的函数获取论文结构
                paper_url = f"https://arxiv.org/html/{paper.arxiv_id}"
                paper_data = get_paper_structure(paper_url)
                
                if paper_data and 'sections' in paper_data:
                    # 将章节列表转换为字典格式，与原代码保持一致
                    sections_dict = {}
                    for section in paper_data['sections']:
                        sections_dict[section] = []  # 初始为空列表，稍后再填充引用
                    
                    paper.sections = sections_dict
                    paper.extra["structure"] = paper_data
                else:
                    paper.extra["expand"] = "get full paper error"
                    return None
                    
            except Exception as e:
                print(f"获取论文章节失败: {e}")
                paper.extra["expand"] = "get full paper error"
                return None
                
            if not paper.sections:
                paper.extra["expand"] = "get full paper error"
                return None
        
        paper.extra["expand"] = "not expand"
        
        # 选择相关章节
        prompt = self.prompts["select_section"].format(
            user_query=self.user_query, 
            title=paper.title, 
            abstract=paper.abstract, 
            sections=list(paper.sections.keys())
        ).strip()
        
        return prompt

    def do_expand(self, depth, paper, crawl_result):
        """扩展论文引用"""
        # 解析选定的章节
        selected_sections = re.findall(self.templates["expand_template"], crawl_result, flags=re.DOTALL)
        
        if not selected_sections:
            print(f"未找到要扩展的章节: {paper.title}")
            return
            
        print(f"找到 {len(selected_sections)} 个要扩展的章节")
        
        # 存储所有引用
        all_citations = []
        
        # 遍历选定的章节，获取引用
        for section_name in selected_sections:
            section_name = section_name.strip()
            
            if section_name not in paper.sections:
                print(f"章节不存在: {section_name}")
                continue
                
            print(f"处理章节: {section_name}")
            
            # 使用您的函数获取章节的引用
            if "structure" in paper.extra and "soup" in paper.extra["structure"]:
                citations = get_section_citations(paper.extra["structure"]["soup"], section_name)
                
                if citations:
                    # 更新章节下的引用列表
                    paper.sections[section_name] = [citation["title"] for citation in citations]
                    
                    # 添加到要处理的引用列表
                    for citation in citations:
                        all_citations.append((section_name, citation))
        
        if not all_citations:
            print(f"未找到引用文献: {paper.title}")
            return
            
        print(f"找到 {len(all_citations)} 篇引用文献")
        
        # 处理引用
        for section_name, citation in all_citations:
            # 获取论文元数据
            metadata = None
            
            # 如果有arXiv ID，优先使用
            if citation.get('arxiv_id'):
                print(f"使用arXiv ID: {citation['arxiv_id']}检索...")
                metadata = get_paper_metadata_by_id(citation['arxiv_id'])
                
            # 否则使用标题搜索
            if not metadata:
                print(f"使用标题搜索...")
                metadata = get_paper_metadata_by_title(citation['title'])
            
            if not metadata:
                print(f"未找到论文元数据: {citation['title']}")
                continue
                
            arxiv_id = metadata['arxiv_id']
            
            # 检查是否已处理过
            if arxiv_id in self.root.extra["touch_ids"]:
                print(f"论文已处理过: {metadata['title']}")
                continue
                
            self.root.extra["touch_ids"].append(arxiv_id)
            
            # 评估论文相关性
            prompt = self.prompts["get_selected"].format(
                title=metadata['title'], 
                abstract=metadata['abstract'], 
                user_query=self.user_query
            )
            
            score = self.selector.infer_score([prompt])[0]['probability']
            
            print(f"评估论文: {metadata['title']} (分数: {score})")
            
            self.root.extra["crawler_recall_papers"].append(metadata['title'])
            if score > 0.5:
                self.root.extra["recall_papers"].append(metadata['title'])
                
            # 创建论文节点
            paper_node = PaperNode({
                "title":        metadata['title'],
                "depth":        depth + 1,
                "arxiv_id":     arxiv_id,
                "abstract":     metadata['abstract'],
                "sections":     "",  # 初始为空
                "source":       "Expand arxiv",
                "select_score": score,
                "extra":        {}
            })
            
            # 添加到父节点的子节点列表
            if section_name not in paper.child:
                paper.child[section_name] = []
                
            paper.child[section_name].append(paper_node)
            paper.extra["expand"] = "success"
            
            # 添加到待处理队列
            self.papers_queue.append(paper_node)

    def expand(self, depth):
        """扩展指定深度的论文"""
        print(f"扩展第 {depth+1} 层引用...")
        
        # 排序找到最相关的论文
        expand_papers = sorted(self.papers_queue[self.expand_start:], key=PaperNode.sort_paper, reverse=True)
        self.papers_queue = self.papers_queue[:self.expand_start] + expand_papers
        
        if depth > 0:
            expand_papers = expand_papers[:self.expand_papers]
            
        self.expand_start = len(self.papers_queue)
        
        print(f"本层需要扩展的论文数: {len(expand_papers)}")
        
        # 对每篇论文获取内容并扩展
        for i, paper in enumerate(expand_papers):
            print(f"处理论文 [{i+1}/{len(expand_papers)}]: {paper.title}")
            
            # 获取论文内容
            crawl_prompt = self.get_paper_content(paper)
            if crawl_prompt:
                # 使用LLM选择要扩展的章节
                crawl_result = self.crawler.infer(crawl_prompt)
                
                # 扩展引用
                self.do_expand(depth, paper, crawl_result)

    def run(self):
        """运行完整的检索流程"""
        print(f"开始论文检索，用户查询: '{self.user_query}'")
        
        # 论文搜索
        self.search()
        print(f"初始搜索完成，找到 {len(self.papers_queue)} 篇论文")
        
        # 逐层扩展引用
        for depth in range(self.expand_layers):
            self.expand(depth)
            
        print(f"检索完成! 共找到 {len(self.root.extra['recall_papers'])} 篇相关论文。")

if __name__ == "__main__":
    agent = PaperAgent(
        user_query="Show me papers of reinforcement learning with LLM.",
        crawler=Agent("qwen3-32B-FP8", "crawler"),
        selector=Agent("selector", "selector"),
        expand_layers=1,
        search_queries=5,
        search_papers=10,
        expand_papers=10
    )
    agent.run()