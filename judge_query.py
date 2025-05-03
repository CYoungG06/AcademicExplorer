import os
import json
import openai
from typing import List, Dict, Tuple
import time
import re

# 假设API密钥和Base URL已在环境变量中设置
# 如果没有设置，您可以取消下面两行的注释并设置这些值
# os.environ["OPENAI_API_KEY"] = "your-api-key"
# os.environ["OPENAI_API_BASE"] = "your-base-url"

# 评价者提示词
EVALUATOR_PROMPT = """# 高质量学术查询改写评估者

作为一名专业的学术查询评估专家，你的任务是评估AI系统改写的学术查询语句质量。你将收到原始用户查询和AI改写后的查询，需要基于以下标准进行全面评估，以确保改写查询能够在学术搜索引擎中获取最相关、最有价值的论文资源。

## 评估流程

1. 首先呈现原始查询和改写查询
2. 分析查询改写的核心变化
3. 在各个维度进行详细评估
4. 给出总体评分和改进建议

## 评估维度

### 1. 学术相关性 (0-10分)
- 改写查询是否保持或增强了原始查询的学术性
- 是否使用了适当的学术术语和概念
- 是否避免了非学术性、过于口语化的表达

### 2. 语义保真度 (0-10分)
- 改写查询是否准确保留了原始查询的核心意图
- 是否有误解或偏离原始查询的核心主题
- 改写是否导致了任何语义偏移或失真

### 3. 专业术语优化 (0-10分)
- 是否恰当地引入或修正了学术领域专业术语
- 术语使用是否准确、规范
- 是否考虑了跨学科术语的适用性

### 4. 检索效率 (0-10分)
- 改写查询是否更有利于搜索引擎检索相关论文
- 是否添加了有助于缩小搜索范围的限定词
- 是否移除了可能导致结果偏离的干扰词

### 5. 查询完整性 (0-10分)
- 改写查询是否涵盖了原始查询的所有关键要素
- 是否有重要概念被遗漏或弱化
- 改写查询的结构是否完整、逻辑清晰

## 总体评分

根据以上维度的评分，计算总分(0-50分)并转换为以下等级：
- 优秀 (40-50分): 显著提升查询质量，极大改善检索效果
- 良好 (30-39分): 有效改善查询质量，提升检索效果
- 一般 (20-29分): 维持查询质量，轻微改善检索效果
- 欠佳 (10-19分): 降低查询质量，可能影响检索效果
- 不合格 (0-9分): 严重损害查询意图，显著降低检索效果

## 输出格式

```
## 评估报告

**原始查询**: [用户原始查询]
**改写查询**: [AI改写查询]

### 核心变化分析
[详细分析改写带来的主要变化]

### 维度评估

1. **学术相关性**: [评分]/10
   [详细评论]

2. **语义保真度**: [评分]/10  
   [详细评论]

3. **专业术语优化**: [评分]/10
   [详细评论]

4. **检索效率**: [评分]/10
   [详细评论]

5. **查询完整性**: [评分]/10
   [详细评论]

### 总体评分
**总分**: [总分]/50
**等级**: [等级]

### 改进建议
[具体、可操作的改进建议]
```

在进行评估时，请注意以下事项：
- 考虑学科特性，不同领域可能有不同的查询习惯和术语
- 保持客观中立，避免偏见
- 提供具体、可行的改进建议
- 解释你的评分理由，使评估透明
- 考虑查询在不同学术搜索引擎(Google Scholar、PubMed、Web of Science等)中的适用性

请评估以下查询改写:
原始查询: {original_query}
改写查询: {rewritten_query}
"""

class QueryEvaluator:
    def __init__(self, model_name="deepseek-chat"):
        """初始化查询评估器"""
        self.client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_API_BASE")
        )
        self.model = model_name
    
    def evaluate_query_rewrite(self, original_query: str, rewritten_query: str) -> str:
        """评估查询改写质量
        
        Args:
            original_query: 用户原始查询
            rewritten_query: AI改写后的查询
        
        Returns:
            str: 完整的评估报告
        """
        try:
            # 准备评估提示
            prompt = EVALUATOR_PROMPT.format(
                original_query=original_query,
                rewritten_query=rewritten_query
            )
            
            # 调用大模型进行评估
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of academic search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 设置较低温度，保持评估一致性
                max_tokens=2000
            )
            
            # 提取评估报告
            evaluation_report = response.choices[0].message.content
            return evaluation_report
        
        except Exception as e:
            print(f"评估过程中出错: {str(e)}")
            return f"评估失败: {str(e)}"
    
    def evaluate_multiple_rewrites(self, original_query: str, rewritten_queries: List[str]) -> List[Dict]:
        """评估原始查询的多个改写版本
        
        Args:
            original_query: 用户原始查询
            rewritten_queries: 多个改写查询的列表
        
        Returns:
            List[Dict]: 各改写查询的评估结果
        """
        results = []
        
        for i, rewritten in enumerate(rewritten_queries):
            print(f"评估改写查询 {i+1}/{len(rewritten_queries)}...")
            
            # 移除可能的[Search]前缀
            clean_rewritten = rewritten.replace("[Search]", "").strip()
            
            evaluation = self.evaluate_query_rewrite(original_query, clean_rewritten)
            
            result = {
                "original_query": original_query,
                "rewritten_query": clean_rewritten,
                "raw_rewritten_query": rewritten,  # 保留原始格式
                "evaluation": evaluation
            }
            
            results.append(result)
            print(f"完成改写查询 {i+1} 的评估")
            
            # 避免API调用过于频繁
            if i < len(rewritten_queries) - 1:
                time.sleep(1)
        
        return results

def parse_input_format(input_text: str) -> Tuple[str, List[str]]:
    """解析指定格式的输入文本
    
    Args:
        input_text: 包含用户查询和改写查询的文本
    
    Returns:
        Tuple[str, List[str]]: 用户查询和改写查询列表
    """
    lines = input_text.strip().split('\n')
    
    user_query = ""
    rewrite_queries = []
    
    # 解析用户查询
    for line in lines:
        if line.startswith("user_query:"):
            user_query = line.replace("user_query:", "").strip()
            break
    
    # 解析改写查询
    rewrite_section_started = False
    for line in lines:
        if line.startswith("rewrite_query:"):
            rewrite_section_started = True
            continue
        
        if rewrite_section_started and line.strip():
            rewrite_queries.append(line.strip())
    
    return user_query, rewrite_queries

def main():
    # 示例输入
    sample_input = """
user_query: Find papers of how to build good reward model in LLM post-training with Reinforcement learning.
rewrite_query:
[search]Survey papers on reward model design for reinforcement learning in post-training of large language models  
[search]Best practices for constructing reward functions in RLHF (Reinforcement Learning from Human Feedback) for LLMs  
[search]Comparative analysis of reward modeling techniques in reinforcement learning for language model alignment  
[search]Challenges and solutions in developing robust reward models for post-training LLMs with reinforcement learning  
[search]Empirical studies on reward model optimization in reinforcement learning for fine-tuning large language models
"""
    
    # 解析输入
    original_query, rewritten_queries = parse_input_format(sample_input)
    
    print(f"原始查询: {original_query}")
    print(f"找到 {len(rewritten_queries)} 个改写查询")
    
    # 初始化评估器
    evaluator = QueryEvaluator()
    
    # 评估多个改写查询
    results = evaluator.evaluate_multiple_rewrites(original_query, rewritten_queries)
    
    # 保存评估结果
    with open("query_evaluation_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"评估结果已保存到 query_evaluation_results.json")
    
    # 打印评估结果
    for i, result in enumerate(results):
        print(f"\n\n===== 改写查询 {i+1} 评估结果 =====")
        print(f"改写查询: {result['raw_rewritten_query']}")
        print(result["evaluation"])

if __name__ == "__main__":
    main()
