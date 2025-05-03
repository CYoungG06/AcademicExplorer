import re
import json
import os
from typing import List, Dict, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from constants import DEFAULT_MODEL, REVIEW_MODEL, OPENAI_BASE_URL

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

class PaperDescriptionGenerator:
    def __init__(self, client: OpenAI, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model
    
    def _build_prompt(self, paper_info: Dict) -> str:
        """构建单篇论文描述的提示词"""
        system_prompt = """您是一位专业的学术写作助手，需要将论文的关键要点转化为规范的学术描述。请注意：
1. 使用专业、准确的学术语言
2. 突出论文的研究问题、方法创新和主要发现
3. 保持简明扼要，控制在200字左右
4. 使用客观的描述语言"""
        
        prompt = f"""请基于以下论文要点生成一段学术性描述：
{json.dumps(paper_info, indent=2, ensure_ascii=False)}

要求：
1. 用1-2句话说明研究问题和背景
2. 用1-2句话描述方法创新
3. 用1句话总结主要发现
4. 如果有明显的局限性，用1句话点明
5. 使用学术性表达，避免口语化
6. 严格控制在200字以内"""
        
        return system_prompt, prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, paper_info: Dict, n_samples: int) -> List[str]:
        """为单篇论文生成多个候选描述"""
        system_prompt, prompt = self._build_prompt(paper_info)
        descriptions = []
        
        for _ in range(n_samples):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=512
                )
                descriptions.append(response.choices[0].message.content)
            except Exception as e:
                print(f"生成失败: {str(e)}")
                descriptions.append("")
                
        return [d for d in descriptions if d]

class DescriptionEvaluator:
    def __init__(self, client: OpenAI, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model
    
    def _build_eval_prompt(self, description: str) -> str:
        """构建评估提示词"""
        return f"""请评估以下论文描述的质量，考虑以下方面：
1. 完整性（25分）：是否涵盖了研究问题、方法、发现等关键要素
2. 简明性（25分）：是否简洁清晰，避免冗余
3. 学术性（25分）：是否使用了规范的学术语言
4. 客观性（25分）：是否保持客观描述，避免过度评价

描述内容：
{description}

请给出总分（0-100），并以JSON格式返回包含score和reasoning两个字段的评估结果。"""
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def evaluate(self, descriptions: List[str], n_votes: int) -> List[float]:
        """评估多个候选描述"""
        all_scores = []
        
        for description in descriptions:
            scores = []
            for _ in range(n_votes):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": "你是一个严格的学术写作评估专家"},
                            {"role": "user", "content": self._build_eval_prompt(description)}
                        ],
                        temperature=0.3
                    )
                    result = json.loads(extract_json(response.choices[0].message.content))
                    scores.append(float(result["score"]))
                except Exception as e:
                    print(f"评估失败: {str(e)}")
                    scores.append(0)
                    
            all_scores.append(sum(scores) / len(scores))
            
        return all_scores

class ReviewSynthesizer:
    def __init__(self, client: OpenAI, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model
    
    def _build_synthesis_prompt(self, descriptions: List[str]) -> str:
        """构建综述合成的提示词"""
        system_prompt = """您是一位专业的学术写作专家，需要基于多篇论文的描述撰写一个连贯的文献综述。请注意：
1. 根据主题相关性组织内容结构
2. 突出不同研究之间的联系与区别
3. 使用恰当的过渡词衔接各部分
4. 保持对每篇文献的均衡关注"""
        
        descriptions_text = "\n\n".join([f"论文{i+1}描述：\n{desc}" for i, desc in enumerate(descriptions)])
        
        prompt = f"""请基于以下论文描述撰写一个完整的文献综述：

{descriptions_text}

要求：
1. 合理规划段落结构，可以是一段或多段
2. 建立论文之间的关联，突出共同点和差异
3. 使用恰当的过渡词确保行文流畅
4. 对每篇论文给予均衡的关注
5. 使用规范的学术语言
6. 适当概括总结，不要逐字重复原描述"""
        
        return system_prompt, prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def synthesize(self, descriptions: List[str], n_samples: int) -> List[str]:
        """生成多个候选综述"""
        system_prompt, prompt = self._build_synthesis_prompt(descriptions)
        reviews = []
        
        for _ in range(n_samples):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
                reviews.append(response.choices[0].message.content)
            except Exception as e:
                print(f"生成失败: {str(e)}")
                reviews.append("")
                
        return [r for r in reviews if r]

def generate_literature_review_simple(refs_list: List[Dict],
                                    client: OpenAI,
                                    model: str = DEFAULT_MODEL) -> str:
    """简化版文献综述生成函数 - 直接生成单一结果"""
    # 初始化组件
    desc_generator = PaperDescriptionGenerator(client, model)
    synthesizer = ReviewSynthesizer(client, model)
    
    # 第一阶段：为每篇论文生成描述
    descriptions = []
    
    for i, paper_info in enumerate(refs_list):
        print(f"正在处理第 {i+1}/{len(refs_list)} 篇论文：{paper_info['paper_id']}")
        
        # 生成描述
        system_prompt, prompt = desc_generator._build_prompt(paper_info)
        
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
            description = response.choices[0].message.content
            descriptions.append(description)
            print(f"已生成第 {i+1} 篇论文的描述")
        except Exception as e:
            print(f"生成失败: {str(e)}")
    
    print("所有论文的描述生成完成，开始合成综述...")
    
    # 第二阶段：合成综述
    system_prompt, prompt = synthesizer._build_synthesis_prompt(descriptions)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        review = response.choices[0].message.content
        return review
    except Exception as e:
        print(f"综述生成失败: {str(e)}")
        return "综述生成失败"

# 保留原函数以兼容旧代码
def generate_literature_review(refs_list: List[Dict],
                             client: OpenAI,
                             model: str = DEFAULT_MODEL,
                             n_samples: int = 2,
                             n_votes: int = 2) -> str:
    """使用简化版函数替代原多候选版本"""
    return generate_literature_review_simple(refs_list, client, model)

if __name__ == "__main__":
    # 读取API密钥
    with open("model_api.txt", "r", encoding="utf-8") as f:
        api_key = f.read().strip()
    
    # 初始化客户端
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
    )
    
    # 从JSON文件读取论文信息
    with open("results1.json", "r", encoding="utf-8") as f:
        refs_list = json.load(f)
    
    # 生成文献综述
    final_review = generate_literature_review_simple(refs_list, client)
    
    # 保存结果
    with open("literature_review_1.txt", "w", encoding="utf-8") as f:
        f.write(final_review)
    
    print("文献综述生成完成，已保存到 literature_review.txt")
