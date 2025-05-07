import json
import pandas as pd
import numpy as np

def parse_score(score_str):
    """Parses score string like '42.3/50' or '44' to a float."""
    if isinstance(score_str, (int, float)):
        return float(score_str)
    if isinstance(score_str, str):
        if '/' in score_str:
            try:
                return float(score_str.split('/')[0])
            except ValueError:
                return None
        else:
            try:
                return float(score_str)
            except ValueError:
                return None
    return None

def analyze_relevance_data_corrected(relevance_list):
    """
    根据新的理解分析单个论文的相关性列表。
    'probability' 字段是 P(Relevant)。'token' 是一个分类。
    返回 (classified_as_true, p_relevant_float)。
    - classified_as_true: 如果 token == "True" 则为 True，否则为 False。
    - p_relevant_float: 来自 JSON 的 'probability' 值。如果未找到或无效，则返回 0.0。
    """
    if not relevance_list or not isinstance(relevance_list, list) or not relevance_list[0]: # 确保列表不为空且至少有一个元素
        return False, 0.0

    item = relevance_list[0] # 假设每个列表只有一个项目
    if not isinstance(item, dict):
        return False, 0.0

    classified_as_true = (item.get('token') == 'True')
    p_relevant_val = item.get('probability') # probability 字段代表 P(Relevant)

    p_relevant_float = 0.0
    if p_relevant_val is not None:
        try:
            p_relevant_float = float(p_relevant_val)
        except (ValueError, TypeError):
            # 如果转换失败，p_relevant_float 保持 0.0
            pass
            
    return classified_as_true, p_relevant_float

def process_file_data(file_path):
    """
    处理单个 JSON 文件并提取关键指标。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件未找到 {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"错误: 无法解码 JSON 文件 {file_path}")
        return None

    results = {
        "file_path": file_path,
        "original_queries_assessments": [],
        "all_rewritten_queries_scores": [],
        "rewritten_queries_details": [],
        "all_paper_relevance_probabilities": [] # 存储所有论文的 P(Relevant) 值
    }

    total_papers_retrieved = 0
    total_papers_classified_true = 0 # 被分类为 "True" 的论文总数
    sum_relevance_prob_for_classified_true_papers = 0.0 # 被分类为 "True" 的论文的相关概率总和
    # all_paper_relevance_probabilities 将用于计算所有论文的平均相关概率

    num_rewritten_queries_with_any_classified_true_papers = 0
    sum_avg_relevance_prob_for_queries_with_classified_true_papers = 0.0


    if not isinstance(data, list):
        print(f"错误: {file_path} 中期望的是列表，但得到的是 {type(data)}")
        return None

    for item_idx, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"警告: {file_path} 中的项目 {item_idx} 不是字典，已跳过。")
            continue

        original_query = item.get("original_query")
        overall_assessment = item.get("overall_assessment", {})
        
        avg_score_val = None
        if "average_score" in overall_assessment:
            avg_score_val = parse_score(overall_assessment.get("average_score"))

        results["original_queries_assessments"].append({
            "original_query": original_query,
            "average_score": avg_score_val,
            "grade": overall_assessment.get("overall_grade"),
            "commentary": overall_assessment.get("overall_commentary"),
            "suggestions": overall_assessment.get("suggestions_for_improvement")
        })

        query_papers_data = item.get("query_papers", {})
        if not isinstance(query_papers_data, dict):
            print(f"警告: 原始查询 '{original_query}' 的 'query_papers' 不是字典，已跳过。")
            continue
            
        for rewritten_query, details in query_papers_data.items():
            if not isinstance(details, dict):
                print(f"警告:改写查询 '{rewritten_query}' 的详细信息不是字典，已跳过。")
                continue
                
            query_eval = details.get("query_evaluation", {})
            rewritten_query_score_str = query_eval.get("score")
            rewritten_query_score = parse_score(rewritten_query_score_str)

            if rewritten_query_score is not None:
                results["all_rewritten_queries_scores"].append(rewritten_query_score)

            papers = details.get("papers", [])
            if not isinstance(papers, list):
                print(f"警告: 改写查询 '{rewritten_query}' 的 'papers' 不是列表，已跳过。")
                papers = []
                
            num_papers_for_this_rewritten_query = len(papers)
            total_papers_retrieved += num_papers_for_this_rewritten_query
            
            classified_true_count_for_query = 0
            sum_prob_relevant_for_query_if_classified_true = 0.0
            sum_prob_relevant_for_query_all_papers = 0.0
            current_query_paper_relevance_probabilities = []

            for paper_idx, paper in enumerate(papers):
                if not isinstance(paper, dict):
                    print(f"警告: 查询 '{rewritten_query}' 的论文 {paper_idx} 不是字典，已跳过。")
                    continue
                
                classified_as_true, p_relevant = analyze_relevance_data_corrected(paper.get("relevance"))
                
                results["all_paper_relevance_probabilities"].append(p_relevant)
                current_query_paper_relevance_probabilities.append(p_relevant)
                sum_prob_relevant_for_query_all_papers += p_relevant

                if classified_as_true:
                    total_papers_classified_true += 1
                    sum_relevance_prob_for_classified_true_papers += p_relevant
                    classified_true_count_for_query += 1
                    sum_prob_relevant_for_query_if_classified_true += p_relevant
            
            avg_prob_classified_true_for_query = (sum_prob_relevant_for_query_if_classified_true / classified_true_count_for_query) \
                if classified_true_count_for_query > 0 else 0.0
            avg_prob_all_papers_for_query = (sum_prob_relevant_for_query_all_papers / num_papers_for_this_rewritten_query) \
                if num_papers_for_this_rewritten_query > 0 else 0.0
            
            if classified_true_count_for_query > 0:
                num_rewritten_queries_with_any_classified_true_papers += 1
                sum_avg_relevance_prob_for_queries_with_classified_true_papers += avg_prob_classified_true_for_query

            results["rewritten_queries_details"].append({
                "rewritten_query": rewritten_query,
                "rewritten_query_score": rewritten_query_score,
                "num_papers_retrieved": num_papers_for_this_rewritten_query,
                "num_papers_classified_true": classified_true_count_for_query,
                "avg_relevance_probability_classified_true_in_query": avg_prob_classified_true_for_query,
                "avg_relevance_probability_all_papers_in_query": avg_prob_all_papers_for_query,
                "all_paper_relevance_probabilities_for_query": current_query_paper_relevance_probabilities
            })

    overall_assessment_scores = [
        item['average_score'] for item in results["original_queries_assessments"] 
        if item['average_score'] is not None
    ]
    results["average_overall_assessment_score"] = np.mean(overall_assessment_scores) \
        if overall_assessment_scores else 0.0
    results["num_original_queries_processed"] = len(results["original_queries_assessments"])

    results["total_rewritten_queries"] = len(results["all_rewritten_queries_scores"])
    results["avg_rewritten_query_score"] = np.mean(results["all_rewritten_queries_scores"]) \
        if results["all_rewritten_queries_scores"] else 0.0
    
    results["total_papers_retrieved"] = total_papers_retrieved
    results["total_papers_classified_true"] = total_papers_classified_true
    results["percentage_papers_classified_true"] = (total_papers_classified_true / total_papers_retrieved) * 100 \
        if total_papers_retrieved > 0 else 0.0
    
    results["avg_relevance_probability_all_retrieved_papers"] = np.mean(results["all_paper_relevance_probabilities"]) \
        if results["all_paper_relevance_probabilities"] else 0.0
        
    results["avg_relevance_probability_for_classified_true_papers"] = \
        (sum_relevance_prob_for_classified_true_papers / total_papers_classified_true) \
        if total_papers_classified_true > 0 else 0.0
        
    results["avg_classified_true_papers_per_rewritten_query"] = \
        (total_papers_classified_true / results["total_rewritten_queries"]) \
        if results["total_rewritten_queries"] > 0 else 0.0

    results["avg_relevance_prob_for_queries_with_classified_true_papers"] = \
        (sum_avg_relevance_prob_for_queries_with_classified_true_papers / num_rewritten_queries_with_any_classified_true_papers) \
        if num_rewritten_queries_with_any_classified_true_papers > 0 else 0.0

    df_rewritten_queries = pd.DataFrame(results["rewritten_queries_details"])
    correlation_results = {
        "correlation_score_vs_num_classified_true": np.nan,
        "correlation_score_vs_avg_relevance_prob_classified_true_for_query": np.nan,
        "correlation_score_vs_avg_relevance_prob_all_papers_for_query": np.nan
    }

    if not df_rewritten_queries.empty and 'rewritten_query_score' in df_rewritten_queries.columns and len(df_rewritten_queries) > 1:
        df_rewritten_queries['rewritten_query_score'] = pd.to_numeric(df_rewritten_queries['rewritten_query_score'], errors='coerce')
        df_corr = df_rewritten_queries.dropna(subset=['rewritten_query_score']) 

        if len(df_corr) > 1:
            correlation_results["correlation_score_vs_num_classified_true"] = df_corr['rewritten_query_score'].corr(
                df_corr['num_papers_classified_true']
            )
            correlation_results["correlation_score_vs_avg_relevance_prob_classified_true_for_query"] = df_corr['rewritten_query_score'].corr(
                df_corr['avg_relevance_probability_classified_true_in_query']
            )
            correlation_results["correlation_score_vs_avg_relevance_prob_all_papers_for_query"] = df_corr['rewritten_query_score'].corr(
                df_corr['avg_relevance_probability_all_papers_in_query']
            )
    
    results.update(correlation_results)
    return results

# --- 主脚本执行 ---
if __name__ == "__main__":
    # 替换为您的 JSON 文件的实际路径
    file_path_sft = 'search_evaluation_results_sft.json'
    file_path_base = 'search_evaluation_results.json'

    print(f"正在处理 SFT 文件: {file_path_sft}")
    data_sft = process_file_data(file_path_sft)
    
    print(f"\n正在处理 Base 文件: {file_path_base}")
    data_base = process_file_data(file_path_base)

    print("\n\n--- 分析结果 ---")

    if data_sft:
        print("\n--- SFT 文件结果 ---")
        for key, value in data_sft.items():
            if key not in ["original_queries_assessments", "rewritten_queries_details", "all_rewritten_queries_scores", "all_paper_relevance_probabilities"]:
                print(f"{key}: {value}")
    
    if data_base:
        print("\n--- Base 文件结果 ---")
        for key, value in data_base.items():
            if key not in ["original_queries_assessments", "rewritten_queries_details", "all_rewritten_queries_scores", "all_paper_relevance_probabilities"]:
                 print(f"{key}: {value}")

    if data_sft and data_base:
        print("\n\n--- 直接对比亮点 ---")
        print(f"平均总体评估分数 (SFT): {data_sft.get('average_overall_assessment_score', 'N/A')}")
        print(f"平均总体评估分数 (Base): {data_base.get('average_overall_assessment_score', 'N/A')}")
        
        print(f"平均改写查询分数 (SFT): {data_sft.get('avg_rewritten_query_score', 'N/A')}")
        print(f"平均改写查询分数 (Base): {data_base.get('avg_rewritten_query_score', 'N/A')}")

        print(f"被分类为 True 的论文百分比 (SFT): {data_sft.get('percentage_papers_classified_true', 'N/A')}%")
        print(f"被分类为 True 的论文百分比 (Base): {data_base.get('percentage_papers_classified_true', 'N/A')}%")
        
        print(f"所有检索论文的平均相关概率 (SFT): {data_sft.get('avg_relevance_probability_all_retrieved_papers', 'N/A')}")
        print(f"所有检索论文的平均相关概率 (Base): {data_base.get('avg_relevance_probability_all_retrieved_papers', 'N/A')}")

        print(f"查询分数 vs. 被分类为True论文数的相关性 (SFT): {data_sft.get('correlation_score_vs_num_classified_true', 'N/A')}")
        print(f"查询分数 vs. 被分类为True论文数的相关性 (Base): {data_base.get('correlation_score_vs_num_classified_true', 'N/A')}")
        
        print(f"查询分数 vs. 所有论文平均相关概率的相关性 (SFT): {data_sft.get('correlation_score_vs_avg_relevance_prob_all_papers_for_query', 'N/A')}")
        print(f"查询分数 vs. 所有论文平均相关概率的相关性 (Base): {data_base.get('correlation_score_vs_avg_relevance_prob_all_papers_for_query', 'N/A')}")