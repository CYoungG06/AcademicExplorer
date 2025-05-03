import re
import json
from typing import List, Dict, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from dotenv import load_dotenv
from constants import DEFAULT_MODEL, REVIEW_MODEL, OPENAI_BASE_URL

load_dotenv(override=True)


def extract_json(content: str):
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass

    json_block_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_block_match:
        try:
            json.loads(json_block_match.group(1))
            return json_block_match.group(1)
        except json.JSONDecodeError:
            pass

    possible_json = re.findall(r'\{.*?}', content, re.DOTALL)
    for json_str in possible_json:
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            continue
    return ""

class ComparativeSummarizer:
    def __init__(self, client: OpenAI, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model

    def _build_prompt(self, ref_i: Dict, prev_summary: str = "") -> str:
        """构建比较性总结的提示词"""
        system_prompt = """您是一位专业的学术研究助理，需要帮助撰写学术论文的相关工作(Related Work)部分。请注意：
    1. 每篇论文的介绍都应该简明扼要，突出其独特贡献
    2. 应该与其他论文建立明确的联系，展示文献间的关联性
    3. 遵循"先总体后细节"的组织原则
    4. 使用恰当的过渡词连接不同文献
    5. 避免过分详细描述单篇文献的细节"""

        context = f"""正在撰写相关工作部分，目前处理的论文要素如下：
    {json.dumps(ref_i, indent=2, ensure_ascii=False)}

    已有的综述内容：
    {prev_summary if prev_summary else '尚无已生成的综述内容。'}"""

        prompt = f"""{context}

    请生成一个新的段落，将这篇论文整合到现有的综述中，要求：
    1. 用1-2句话简要介绍该论文的主要研究问题
    2. 用1-2句话概括其方法创新
    3. 用1句话说明其主要结果
    4. 如果可能，用1句话指出与前文提到的其他工作的关系
    5. 段落长度控制在150-200字左右
    6. 使用学术性的连接词，如"此外"、"相比之下"、"与...类似"等
    7. 确保与前文的自然衔接
    8. 为每篇论文分配均衡的篇幅，避免过分详细描述单篇文献的细节
    """

        return system_prompt, prompt

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, ref_i: Dict, prev_summary: str, n_samples: int) -> List[str]:
        """生成多个候选综述段落"""
        system_prompt, prompt = self._build_prompt(ref_i, prev_summary)
        summaries = []
        
        for _ in range(n_samples):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=512  # 减小token数以控制生成长度
                )
                summaries.append(response.choices[0].message.content)
            except Exception as e:
                print(f"生成失败: {str(e)}")
                summaries.append("")
                
        print(f"生成的候选综述：{summaries}")
        return [s for s in summaries if s]  # 过滤空结果


class ReflectiveEvaluator:
    def __init__(self, client: OpenAI, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model

    def _build_eval_prompt(self, summary: str) -> str:
        """构建评估提示词"""
        return f"""请评估以下文献综述段落的质量，考虑以下方面：
    1. 篇幅均衡性（20分）：是否对每篇文献都给予了适当篇幅的介绍
    2. 重点突出（20分）：是否准确提炼了各篇文献的核心贡献
    3. 连贯性（20分）：段落之间是否有合适的过渡和逻辑联系
    4. 简明性（20分）：是否避免了过度详细的描述
    5. 学术性（20分）：是否使用了恰当的学术用语和表达方式

    综述内容：
    {summary}

    请给出总分（0-100），并以JSON格式返回包含score和reasoning两个字段的评估结果。"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def evaluate(self, summaries: List[str], n_votes: int) -> List[float]:
        """对每个候选综述进行多次评估"""
        all_scores = []
        
        for summary in summaries:
            scores = []
            for _ in range(n_votes):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": "你是一个严格的学术写作评估专家"},
                            {"role": "user", "content": self._build_eval_prompt(summary)}
                        ],
                        temperature=0.3
                    )
                    result = json.loads(extract_json(response.choices[0].message.content))
                    scores.append(float(result["score"]))
                except Exception as e:
                    print(f"评估失败: {str(e)}")
                    scores.append(0)
                    
            all_scores.append(sum(scores) / len(scores))  # 取平均分
            
        return all_scores

def generate_literature_review(refs_list: List[Dict], 
                             client: OpenAI,
                             model: str = DEFAULT_MODEL) -> str:
    """生成完整的文献综述 - 简化版本，直接生成单一结果"""
    summarizer = ComparativeSummarizer(client, model)
    
    # 初始化为空字符串
    current_summary = ""
    
    # 逐篇处理论文
    for i, ref_i in enumerate(refs_list):
        print(f"处理第 {i+1}/{len(refs_list)} 篇参考文献：{ref_i['paper_id']}")
        
        # 生成综述段落
        system_prompt, prompt = summarizer._build_prompt(ref_i, current_summary)
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=512
            )
            
            # 获取生成的段落并添加到当前综述
            new_paragraph = response.choices[0].message.content
            if current_summary:
                current_summary += "\n\n" + new_paragraph
            else:
                current_summary = new_paragraph
                
            print(f"已添加第 {i+1} 篇论文的综述段落")
            
        except Exception as e:
            print(f"生成失败: {str(e)}")
    
    return current_summary

# 使用示例
if __name__ == "__main__":
    api_key = os.environ["OPENAI_API_KEY"]
    
    # 初始化客户端
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
    )
    
    # 从JSON文件读取关键要素列表
    with open("results.json", "r", encoding="utf-8") as f:
        refs_list = json.load(f)
    
    # 生成文献综述
    final_summary = generate_literature_review(refs_list, client)
    
    # 保存生成的综述
    with open("literature_review.txt", "w", encoding="utf-8") as f:
        f.write(final_summary)
    
    print("文献综述生成完成，已保存到 literature_review.txt")
