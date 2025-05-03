import os
import json
from typing import List, Dict, Optional, Generator
from pathlib import Path
import re
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from constants import DEFAULT_MODEL, OPENAI_BASE_URL

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

class PaperProcessor:
    def __init__(self, root_dir: str = "./mds"):
        self.root_dir = Path(root_dir)
        
    def _find_md_files(self) -> Generator[Path, None, None]:
        """递归查找所有符合条件的Markdown文件"""
        for dir_path in self.root_dir.glob("*"):
            if dir_path.is_dir() and not dir_path.name.startswith("."):
                md_file = dir_path / f"{dir_path.name}.md"
                if md_file.exists():
                    yield md_file

    def read_paper_content(self, md_path: Path) -> str:
        """读取并预处理Markdown内容"""
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 预处理：移除图片标记和特殊字符
            content = re.sub(r"!\[.*?\]\(.*?\)", "", content)  # 移除图片
            content = re.sub(r"{#.*?}", "", content)  # 移除Markdown锚点
            return content.strip()
        except Exception as e:
            print(f"读取文件失败 {md_path}: {str(e)}")
            return ""



class KeyElementExtractor:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
            )
        self.model = model
        self.questions = [
            {
                "en": "What research questions does the paper attempt to address?",
                "key": "research_questions"
            },
            {
                "en": "What method does the paper employ to address this issue?",
                "key": "methodology"
            },
            {
                "en": "What were the obtained experimental results in the paper?",
                "key": "results"
            },
            {
                "en": "What conclusions were drawn from the experiments?",
                "key": "conclusions"
            },
            {
                "en": "What contributions does this paper make?",
                "key": "contributions"
            },
            {
                "en": "What are the innovations introduced in the paper?",
                "key": "innovations"
            },
            {
                "en": "What limitations are identified in the paper?",
                "key": "limitations"
            }
        ]

    
    def _build_prompt(self, content: str) -> str:
        """提示词模板"""
        system_prompt = """您是一位经验丰富的学术研究员，需要从科研论文中提取结构化信息。请仔细阅读以下内容并按顺序回答每个问题：

要求：
1. 确保每个答案包含具体的技术细节
2. 保持专业术语的准确性
3. 如果某项信息不存在，明确标注"未提及"
4. 使用规范的学术表达方式"""

        question_items = "\n".join(
            [f"{idx+1}. [{q['en']}]" for idx, q in enumerate(self.questions)]
        )

        prompt = f"""{system_prompt}

需要回答的问题列表：
{question_items}

论文全文内容：
{content}

请严格按照以下JSON格式输出：
{json.dumps({q['key']: "..." for q in self.questions}, indent=2, ensure_ascii=False)}"""
        
        return prompt

    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_llm(self, prompt: str) -> Optional[Dict]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "你是一个专业的学术研究助理，擅长从论文中提取结构化信息"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1024
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            return None

    def process_paper(self, paper_content: str) -> Dict:
        """处理单篇论文"""
        prompt = self._build_prompt(paper_content)
        result = self._call_llm(prompt)
        
        # 结果后处理
        if result:
            for key in [q['key'] for q in self.questions]:
                if key not in result:
                    result[key] = "未找到相关信息"
            return result
        return {q['key']: "提取失败" for q in self.questions}

    def batch_process(self, papers: List[str]) -> List[Dict]:
        """批量处理论文集"""
        return [self.process_paper(paper) for paper in papers]



class Pipeline:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, root_dir: str = "./mds"):
        self.processor = PaperProcessor(root_dir)
        self.extractor = KeyElementExtractor(api_key, model)
        
    def run(self, output_path: str = "results1.json"):
        """完整处理流水线"""
        md_files = list(self.processor._find_md_files())
        print(f"找到 {len(md_files)} 篇待处理论文")
        
        all_results = []
        for md_path in md_files:
            print(f"正在处理：{md_path.parent.name}")
            content = self.processor.read_paper_content(md_path)
            if not content:
                continue
                
            result = self.extractor.process_paper(content)
            result["paper_id"] = md_path.parent.name  # 添加论文标识
            all_results.append(result)
            
        # 保存结果
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        print(f"处理完成，结果已保存至 {output_path}")



if __name__ == "__main__":
    api_key = os.environ["OPENAI_API_KEY"]
    
    root_dir = "./mdss"
    pipeline = Pipeline(api_key, DEFAULT_MODEL, root_dir)
    pipeline.run()
