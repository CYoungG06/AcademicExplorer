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
    Analyzes the relevance list for a single paper.
    'probability' field is P(Relevant). 'token' is a classification.
    Returns (classified_as_true, p_relevant_float).
    """
    if not relevance_list or not isinstance(relevance_list, list) or not relevance_list[0]:
        return False, 0.0

    item = relevance_list[0]
    if not isinstance(item, dict):
        return False, 0.0

    classified_as_true = (item.get('token') == 'True')
    p_relevant_val = item.get('probability')

    p_relevant_float = 0.0
    if p_relevant_val is not None:
        try:
            p_relevant_float = float(p_relevant_val)
        except (ValueError, TypeError):
            pass
            
    return classified_as_true, p_relevant_float

def process_file_data(file_path):
    """
    Processes a single JSON file and extracts key metrics.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None

    results = {
        "file_path": file_path,
        "original_queries_assessments": [],
        "all_rewritten_queries_scores": [],
        "rewritten_queries_details": [],
        "all_paper_relevance_probabilities": []
    }

    total_papers_retrieved = 0
    total_papers_classified_true = 0
    sum_relevance_prob_for_classified_true_papers = 0.0
    num_rewritten_queries_with_any_classified_true_papers = 0
    sum_avg_relevance_prob_for_queries_with_classified_true_papers = 0.0

    if not isinstance(data, list):
        print(f"Error: Expected a list of items in {file_path}, but got {type(data)}")
        return None

    for item_idx, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"Warning: Item {item_idx} in {file_path} is not a dictionary, skipping.")
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
            print(f"Warning: 'query_papers' for original query '{original_query}' is not a dict, skipping.")
            continue
            
        for rewritten_query, details in query_papers_data.items():
            if not isinstance(details, dict):
                print(f"Warning: Details for rewritten query '{rewritten_query}' is not a dict, skipping.")
                continue
                
            query_eval = details.get("query_evaluation", {})
            rewritten_query_score_str = query_eval.get("score")
            rewritten_query_score = parse_score(rewritten_query_score_str)

            if rewritten_query_score is not None:
                results["all_rewritten_queries_scores"].append(rewritten_query_score)

            papers = details.get("papers", [])
            if not isinstance(papers, list):
                print(f"Warning: 'papers' for rewritten query '{rewritten_query}' is not a list, skipping.")
                papers = []
                
            num_papers_for_this_rewritten_query = len(papers)
            total_papers_retrieved += num_papers_for_this_rewritten_query
            
            classified_true_count_for_query = 0
            sum_prob_relevant_for_query_if_classified_true = 0.0
            sum_prob_relevant_for_query_all_papers = 0.0
            current_query_paper_relevance_probabilities = []

            for paper_idx, paper in enumerate(papers):
                if not isinstance(paper, dict):
                    print(f"Warning: Paper {paper_idx} for query '{rewritten_query}' is not a dict, skipping.")
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
        # Ensure 'rewritten_query_score' is numeric and drop NaNs for correlation calculation
        df_rewritten_queries['rewritten_query_score'] = pd.to_numeric(df_rewritten_queries['rewritten_query_score'], errors='coerce')
        df_corr = df_rewritten_queries.dropna(subset=['rewritten_query_score'])

        if len(df_corr) > 1: # Need at least 2 valid data points for correlation
            # Ensure target columns for correlation are also numeric and handle potential NaNs if necessary
            # For these specific metrics, 0 is a valid value if no papers were classified true, etc.
            df_corr.loc[:, 'num_papers_classified_true'] = pd.to_numeric(df_corr['num_papers_classified_true'], errors='coerce').fillna(0)
            df_corr.loc[:, 'avg_relevance_probability_classified_true_in_query'] = pd.to_numeric(df_corr['avg_relevance_probability_classified_true_in_query'], errors='coerce').fillna(0)
            df_corr.loc[:, 'avg_relevance_probability_all_papers_in_query'] = pd.to_numeric(df_corr['avg_relevance_probability_all_papers_in_query'], errors='coerce').fillna(0)
            
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

# --- Main script execution ---
if __name__ == "__main__":
    files_to_analyze = [
        {"name": "SFT", "path": "search_evaluation_results_sft.json"},
        {"name": "Base", "path": "search_evaluation_results.json"},
        {"name": "DS", "path": "ds_search_evaluation_results.json"},
        {"name": "P", "path": "p_search_evaluation_results.json"}
    ]

    all_results_data = {}

    for file_info in files_to_analyze:
        print(f"Processing {file_info['name']} file: {file_info['path']}")
        data = process_file_data(file_info['path'])
        if data:
            all_results_data[file_info['name']] = data
        print("-" * 30)

    print("\n\n--- Aggregated Analysis Results ---")

    for name, results_data in all_results_data.items():
        print(f"\n--- {name} File Results ---")
        if results_data:
            for key, value in results_data.items():
                # Exclude printing very long list fields for brevity in summary
                if key not in ["original_queries_assessments", 
                               "rewritten_queries_details", 
                               "all_rewritten_queries_scores", 
                               "all_paper_relevance_probabilities"]:
                    print(f"{key}: {value}")
        else:
            print(f"No data processed for {name}.")

    # --- Direct Comparison Highlights ---
    if all_results_data:
        print("\n\n--- Direct Comparison Highlights ---")
        
        metrics_to_compare = [
            "average_overall_assessment_score",
            "avg_rewritten_query_score",
            "percentage_papers_classified_true",
            "avg_relevance_probability_all_retrieved_papers",
            "correlation_score_vs_num_classified_true",
            "correlation_score_vs_avg_relevance_prob_all_papers_for_query"
        ]

        # Header for the comparison table
        header = "| Metric                                                      | " + " | ".join(all_results_data.keys()) + " |"
        print(header)
        separator = "|:------------------------------------------------------|:" + ":|:".join(["-"*len(name) for name in all_results_data.keys()]) + ":|"
        print(separator)

        for metric_key in metrics_to_compare:
            row_values = [f"{results.get(metric_key, 'N/A'):.3f}" if isinstance(results.get(metric_key), float) else str(results.get(metric_key, 'N/A')) for name, results in all_results_data.items()]
            # Adjust metric name display for readability
            metric_display_name = metric_key.replace("_", " ").title()
            if "Percentage" in metric_display_name:
                 row_values = [f"{results.get(metric_key, 'N/A'):.2f}%" if isinstance(results.get(metric_key), float) else str(results.get(metric_key, 'N/A')) for name, results in all_results_data.items()]


            print(f"| {metric_display_name:<53} | " + " | ".join(f"{val:<{len(name)}}" for val, name in zip(row_values, all_results_data.keys())) + " |")
            
    else:
        print("No data was processed successfully to show comparison highlights.")