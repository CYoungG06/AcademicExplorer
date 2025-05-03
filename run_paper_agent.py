import os
import json
import argparse
from agent import Agent
from paper_agent import PaperAgent
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument('--input_file',     type=str, default="data/RealScholarQuery/test_copy.jsonl")
parser.add_argument('--crawler_path',   type=str, default="deepseek-chat")
parser.add_argument('--selector_path',  type=str, default="deepseek-chat")
parser.add_argument('--output_folder',  type=str, default="results")
parser.add_argument('--expand_layers',  type=int, default=1)
parser.add_argument('--search_queries', type=int, default=5)
parser.add_argument('--search_papers',  type=int, default=10)
parser.add_argument('--expand_papers',  type=int, default=10)
parser.add_argument('--google_key',     type=str, default=os.getenv("GOOGLE_KEY"))

args = parser.parse_args()

def main():
    crawler = Agent(args.crawler_path)
    selector = Agent(args.selector_path)

    if args.output_folder:
        os.makedirs(args.output_folder, exist_ok=True)

    print(f"从 {args.input_file} 读取查询...")
    with open(args.input_file) as f:
        lines = f.readlines()
        total = len(lines)
        
        for idx, line in enumerate(lines):
            print(f"\n处理查询 [{idx+1}/{total}]")
            data = json.loads(line)
            
            end_date = data['source_meta']['published_time']
            end_date = datetime.strptime(end_date, "%Y%m%d") - timedelta(days=7)
            end_date = end_date.strftime("%Y%m%d")
            
            paper_agent = PaperAgent(
                user_query     = data['question'], 
                crawler        = crawler,
                selector       = selector,
                end_date       = end_date,
                expand_layers  = args.expand_layers,
                search_queries = args.search_queries,
                search_papers  = args.search_papers,
                expand_papers  = args.expand_papers,
                google_key     = args.google_key
            )
            
            if "answer" in data:
                paper_agent.root.extra["answer"] = data["answer"]
            
            try:
                paper_agent.run()
            except Exception as e:
                print(f"处理查询时出错: {e}")
                continue
            
            if args.output_folder:
                output_path = os.path.join(args.output_folder, f"{idx}.json")
                with open(output_path, "w") as f:
                    json.dump(paper_agent.root.todic(), f, indent=2)
                print(f"结果已保存至 {output_path}")

if __name__ == "__main__":
    main()