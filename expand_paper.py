import requests
from bs4 import BeautifulSoup
import re
import arxiv
import time
import difflib

def get_paper_structure(url):
    # 获取网页内容
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取章节目录
    sections = []
    for section in soup.find_all('section', class_='ltx_section'):
        title_element = section.find('h2', class_='ltx_title_section')
        if title_element:
            section_number = title_element.find('span', class_='ltx_tag_section')
            section_title = title_element.text.strip()
            sections.append(section_title)
    
    return {
        'sections': sections,
        'soup': soup  # 返回解析后的soup对象，以便后续使用
    }

def get_section_citations(soup, section_name):
    # 找到指定章节
    sections = soup.find_all('section', class_='ltx_section')
    target_section = None
    
    for section in sections:
        title_element = section.find('h2', class_='ltx_title_section')
        if title_element and title_element.text.strip() == section_name:
            target_section = section
            break
    
    if not target_section:
        return []
    
    # 提取章节中的引用
    citation_refs = []
    for cite in target_section.find_all('cite', class_='ltx_cite'):
        for a_tag in cite.find_all('a', class_='ltx_ref'):
            href = a_tag.get('href', '')
            bib_match = re.search(r'#(bib\.\w+)', href)
            if bib_match:
                citation_refs.append(bib_match.group(1))
    
    # 去除重复的引用ID
    unique_citation_refs = list(dict.fromkeys(citation_refs))
    
    # 获取引用文献的详细信息
    citations = []
    bibliography = soup.find('section', class_='ltx_bibliography')
    
    if bibliography:
        for ref_id in unique_citation_refs:
            bib_item = bibliography.find('li', id=ref_id)
            if bib_item:
                # 获取完整的引用文本
                full_citation = bib_item.text.strip()
                
                # 尝试从引用文本中提取arXiv ID
                arxiv_id = None
                arxiv_patterns = [
                    r'arXiv:(\d+\.\d+)',  # 匹配 arXiv:1234.56789
                    r'arxiv\.org/abs/(\d+\.\d+)',  # 匹配 arxiv.org/abs/1234.56789
                    r'arxiv\.org/pdf/(\d+\.\d+)'   # 匹配 arxiv.org/pdf/1234.56789
                ]
                
                for pattern in arxiv_patterns:
                    match = re.search(pattern, full_citation, re.IGNORECASE)
                    if match:
                        arxiv_id = match.group(1)
                        break
                
                # 通常标题在第二个bibblock中
                bib_blocks = bib_item.find_all('span', class_='ltx_bibblock')
                title = ""
                if len(bib_blocks) >= 2:
                    title = bib_blocks[1].text.strip()
                
                citations.append({
                    'ref_id': ref_id,
                    'title': title,
                    'full_citation': full_citation,
                    'arxiv_id': arxiv_id
                })
    
    return citations

def get_paper_metadata_by_id(arxiv_id):
    """
    使用arXiv ID直接获取论文元数据
    
    Args:
        arxiv_id: arXiv ID，例如 '2101.12345'
    
    Returns:
        包含元数据的字典，如果未找到则返回None
    """
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    
    try:
        results = list(client.results(search))
        if results:
            paper = results[0]
            metadata = {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'published': paper.published.strftime('%Y-%m-%d'),
                'updated': paper.updated.strftime('%Y-%m-%d') if hasattr(paper, 'updated') else None,
                'abstract': paper.summary,
                'arxiv_id': arxiv_id
            }
            return metadata
    except Exception as e:
        print(f"  通过ID检索时出错: {e}")
    
    return None

def get_paper_metadata_by_title(title):
    """
    使用标题搜索论文元数据，返回最匹配的结果
    
    Args:
        title: 论文标题
    
    Returns:
        包含元数据的字典，如果未找到则返回None
    """
    # 清理标题，移除特殊字符
    clean_title = re.sub(r'[^\w\s]', '', title)
    
    # 创建arXiv客户端
    client = arxiv.Client()
    
    # 搜索arXiv，获取前3个结果
    search = arxiv.Search(
        query=f'"{clean_title}"',  # 使用引号进行精确匹配
        max_results=3,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    try:
        results = list(client.results(search))
    except Exception as e:
        print(f"  搜索时出错: {e}")
        return None
    
    # 如果没有找到结果，尝试不使用引号的更宽松搜索
    if not results:
        search = arxiv.Search(
            query=clean_title,
            max_results=3,
            sort_by=arxiv.SortCriterion.Relevance
        )
        try:
            results = list(client.results(search))
        except Exception as e:
            print(f"  第二次搜索时出错: {e}")
            return None
    
    if not results:
        return None
    
    # 如果有多个结果，选择标题最匹配的一个
    if len(results) > 1:
        # 计算每个结果标题与搜索标题的相似度
        similarities = []
        for paper in results:
            # 使用difflib计算字符串相似度
            similarity = difflib.SequenceMatcher(None, 
                                               clean_title.lower(), 
                                               re.sub(r'[^\w\s]', '', paper.title.lower())).ratio()
            similarities.append((paper, similarity))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 打印所有候选项及其相似度，以便调试
        print("  候选论文:")
        for i, (paper, similarity) in enumerate(similarities):
            print(f"  {i+1}. 相似度: {similarity:.4f}, 标题: {paper.title}")
        
        # 选择相似度最高的论文
        paper = similarities[0][0]
        print(f"  选择相似度最高的论文: {paper.title}")
    else:
        paper = results[0]
    
    # 提取元数据
    metadata = {
        'title': paper.title,
        'authors': [author.name for author in paper.authors],
        'published': paper.published.strftime('%Y-%m-%d'),
        'updated': paper.updated.strftime('%Y-%m-%d') if hasattr(paper, 'updated') else None,
        'abstract': paper.summary,
        'arxiv_id': paper.entry_id.split('/')[-1]
    }
    
    return metadata

def get_paper_metadata(citation):
    """
    获取论文元数据，首先尝试使用arXiv ID，然后回退到标题搜索
    
    Args:
        citation: 包含引用信息的字典
    
    Returns:
        包含元数据的字典，如果未找到则返回None
    """
    # 如果有arXiv ID，优先使用ID获取
    if citation.get('arxiv_id'):
        print(f"  使用arXiv ID: {citation['arxiv_id']}检索...")
        metadata = get_paper_metadata_by_id(citation['arxiv_id'])
        if metadata:
            return metadata
    
    # 回退到标题搜索
    print(f"  使用标题搜索...")
    return get_paper_metadata_by_title(citation['title'])

def fetch_all_citations_metadata(citations):
    """获取所有引用文献的元数据"""
    results = []
    
    for i, citation in enumerate(citations):
        print(f"正在获取 [{i+1}/{len(citations)}] {citation['title']} 的元数据...")
        metadata = get_paper_metadata(citation)
        
        if metadata:
            results.append({
                'ref_id': citation['ref_id'],
                'original_title': citation['title'],
                'metadata': metadata
            })
        else:
            results.append({
                'ref_id': citation['ref_id'],
                'original_title': citation['title'],
                'metadata': None
            })
        
        # 添加延迟以避免API限制
        time.sleep(1)
    
    return results

def main(paper_url):
    # 获取论文结构
    paper_data = get_paper_structure(paper_url)
    
    print("论文章节目录:")
    for i, section in enumerate(paper_data['sections']):
        print(f"{i+1}. {section}")
    
    # 获取用户选择的章节
    section_name = input("\n请输入要查询引用文献的章节名称(例如 '1 Introduction'): ")
    citations = get_section_citations(paper_data['soup'], section_name)
    
    if not citations:
        print("未找到引用文献或指定章节不存在")
        return
    
    print(f"\n章节 '{section_name}' 中的引用文献 (共{len(citations)}篇):")
    for i, citation in enumerate(citations):
        arxiv_info = f" [arXiv:{citation['arxiv_id']}]" if citation.get('arxiv_id') else ""
        print(f"{i+1}. [{citation['ref_id']}]{arxiv_info} {citation['title']}")
    
    # 获取引用文献的元数据
    print("\n正在获取引用文献的元数据...")
    metadata_results = fetch_all_citations_metadata(citations)
    
    # 显示元数据结果
    print("\n引用文献的详细元数据:")
    for i, result in enumerate(metadata_results):
        print(f"\n{i+1}. [{result['ref_id']}] {result['original_title']}")
        
        if result['metadata']:
            meta = result['metadata']
            print(f"   arXiv ID: {meta['arxiv_id']}")
            print(f"   标题: {meta['title']}")
            print(f"   作者: {', '.join(meta['authors'])}")
            print(f"   发布日期: {meta['published']}")
            if meta['updated']:
                print(f"   最后更新: {meta['updated']}")
            print(f"   摘要: {meta['abstract'][:200]}..." if len(meta['abstract']) > 200 else f"   摘要: {meta['abstract']}")
        else:
            print("   未找到元数据")

if __name__ == "__main__":
    paper_url = "https://arxiv.org/html/2503.04697v1"
    main(paper_url)