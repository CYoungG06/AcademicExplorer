import requests
import json
import argparse
import time
import os
from pprint import pprint

def test_health(base_url):
    """Test the health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{base_url}/api/health")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    return response.status_code == 200

def test_system_info(base_url):
    """Test the system info endpoint"""
    print("\n=== Testing System Info Endpoint ===")
    response = requests.get(f"{base_url}/api/utils/system")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        pprint(response.json())
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_config_info(base_url):
    """Test the config info endpoint"""
    print("\n=== Testing Config Info Endpoint ===")
    response = requests.get(f"{base_url}/api/utils/config")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        pprint(response.json())
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_direct_search(base_url, query="large language models"):
    """Test the direct search endpoint"""
    print(f"\n=== Testing Direct Search Endpoint with query: '{query}' ===")
    response = requests.get(f"{base_url}/api/search/direct", params={"query": query, "limit": 3})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result.get('papers', []))} papers")
        for i, paper in enumerate(result.get('papers', [])[:3], 1):
            print(f"\n{i}. {paper.get('title')}")
            print(f"   Authors: {', '.join(paper.get('authors', []))}")
            print(f"   arXiv ID: {paper.get('arxiv_id')}")
            print(f"   Published: {paper.get('published')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_paper_info(base_url, arxiv_id="2303.08774"):
    """Test the paper info endpoint"""
    print(f"\n=== Testing Paper Info Endpoint with arXiv ID: {arxiv_id} ===")
    response = requests.get(f"{base_url}/api/search/paper/{arxiv_id}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        paper = response.json()
        print(f"Title: {paper.get('title')}")
        print(f"Authors: {', '.join(paper.get('authors', []))}")
        print(f"Published: {paper.get('published')}")
        print(f"Abstract: {paper.get('abstract')[:200]}...")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_search(base_url, query="large language models for scientific literature"):
    """Test the search endpoint"""
    print(f"\n=== Testing Search Endpoint with query: '{query}' ===")
    data = {
        "query": query,
        "expand_layers": 1,
        "search_queries": 2,
        "search_papers": 3,
        "expand_papers": 3
    }
    response = requests.post(f"{base_url}/api/search", json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        task_id = result.get("task_id")
        print(f"Task ID: {task_id}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        # Poll for task completion
        print("\nPolling for task completion...")
        max_polls = 30
        poll_interval = 5
        for i in range(max_polls):
            time.sleep(poll_interval)
            task_response = requests.get(f"{base_url}/api/search/task/{task_id}")
            if task_response.status_code == 200:
                task_result = task_response.json()
                print(f"Status: {task_result.get('status')}")
                print(f"Progress: {task_result.get('progress')}")
                print(f"Message: {task_result.get('message')}")
                
                if task_result.get("status") == "completed":
                    print("\nTask completed!")
                    papers = task_result.get("result", {}).get("papers", [])
                    print(f"Found {len(papers)} papers")
                    for i, paper in enumerate(papers[:3], 1):
                        print(f"\n{i}. {paper.get('title')}")
                        print(f"   arXiv ID: {paper.get('arxiv_id')}")
                        print(f"   Score: {paper.get('score')}")
                    return True
                elif task_result.get("status") == "failed":
                    print(f"Task failed: {task_result.get('message')}")
                    return False
            else:
                print(f"Error checking task status: {task_response.text}")
            
            print(f"Polling... ({i+1}/{max_polls})")
        
        print("Polling timed out")
        return False
    else:
        print(f"Error: {response.text}")
        return False

def test_upload_pdf(base_url, pdf_path):
    """Test the PDF upload endpoint"""
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False
    
    print(f"\n=== Testing PDF Upload Endpoint with file: {pdf_path} ===")
    files = [("files", (os.path.basename(pdf_path), open(pdf_path, "rb"), "application/pdf"))]
    response = requests.post(f"{base_url}/api/review/files", files=files)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        task_id = result.get("task_id")
        print(f"Task ID: {task_id}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test the API endpoints")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--query", default="large language models", help="Query for search tests")
    parser.add_argument("--arxiv-id", default="2303.08774", help="arXiv ID for paper info test")
    parser.add_argument("--pdf", help="Path to a PDF file for upload test")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--health", action="store_true", help="Test health endpoint")
    parser.add_argument("--system", action="store_true", help="Test system info endpoint")
    parser.add_argument("--config", action="store_true", help="Test config info endpoint")
    parser.add_argument("--direct-search", action="store_true", help="Test direct search endpoint")
    parser.add_argument("--paper-info", action="store_true", help="Test paper info endpoint")
    parser.add_argument("--search", action="store_true", help="Test search endpoint")
    parser.add_argument("--upload", action="store_true", help="Test PDF upload endpoint")
    
    args = parser.parse_args()
    
    # If no specific tests are selected, run health check
    if not (args.all or args.health or args.system or args.config or args.direct_search or 
            args.paper_info or args.search or args.upload):
        args.health = True
    
    # Run selected tests
    results = {}
    
    if args.all or args.health:
        results["health"] = test_health(args.url)
    
    if args.all or args.system:
        results["system"] = test_system_info(args.url)
    
    if args.all or args.config:
        results["config"] = test_config_info(args.url)
    
    if args.all or args.direct_search:
        results["direct_search"] = test_direct_search(args.url, args.query)
    
    if args.all or args.paper_info:
        results["paper_info"] = test_paper_info(args.url, args.arxiv_id)
    
    if args.all or args.search:
        results["search"] = test_search(args.url, args.query)
    
    if (args.all or args.upload) and args.pdf:
        results["upload"] = test_upload_pdf(args.url, args.pdf)
    
    # Print summary
    print("\n=== Test Results Summary ===")
    for test, result in results.items():
        print(f"{test}: {'PASS' if result else 'FAIL'}")

if __name__ == "__main__":
    main()
