import os
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
import tempfile
import shutil
from dotenv import load_dotenv

# Import existing modules
from agent import Agent
from paper_agent import PaperAgent
from expand_paper import get_paper_metadata_by_id
from search_from_google import google_search_arxiv_id, parse_rewrites
from constants import CRAWLER_MODEL, SELECTOR_MODEL, MAX_SEARCH_QUERIES, MAX_SEARCH_PAPERS, MAX_EXPAND_PAPERS

# Load environment variables
load_dotenv()

class SearchService:
    def __init__(self, crawler=None, selector=None, google_key=None):
        """
        Initialize the search service
        
        Args:
            crawler: Agent for generating queries and selecting sections
            selector: Agent for evaluating paper relevance
            google_key: Google Search API key
        """
        self.crawler = crawler
        self.selector = selector
        self.google_key = google_key or os.getenv("GOOGLE_KEY")
        
        # Initialize agents if not provided
        if not self.crawler:
            try:
                # self.crawler = Agent(os.getenv("CRAWLER_MODEL", CRAWLER_MODEL))
                self.crawler = Agent("qwen3-32B-FP8", "crawler")
            except Exception as e:
                print(f"Failed to initialize crawler agent: {e}")
                self.crawler = None
        
        if not self.selector:
            try:
                # self.selector = Agent(os.getenv("SELECTOR_MODEL", SELECTOR_MODEL))
                self.selector = Agent("selector", "selector")
            except Exception as e:
                print(f"Failed to initialize selector agent: {e}")
                self.selector = None
        
        if not self.google_key:
            print("Warning: Google Search API key not found. Paper search functionality will be limited.")
    
    def search_papers(self, query: str, search_queries: int = MAX_SEARCH_QUERIES, 
                     search_papers: int = MAX_SEARCH_PAPERS, expand_papers: int = MAX_EXPAND_PAPERS) -> Dict[str, Any]:
        """
        Search for papers related to the query without citation expansion
        
        Args:
            query: User query
            search_queries: Number of search queries to generate
            search_papers: Number of papers to search per query
            expand_papers: Number of papers to expand per layer
            
        Returns:
            Dictionary containing search results
        """
        # Check if agents are initialized
        if not self.crawler or not self.selector:
            raise ValueError("Agents not initialized. Cannot search for papers.")
        
        # Create PaperAgent
        paper_agent = PaperAgent(
            user_query=query,
            crawler=self.crawler,
            selector=self.selector,
            expand_layers=0,  # No citation expansion by default
            search_queries=search_queries,
            search_papers=search_papers,
            expand_papers=expand_papers,
            google_key=self.google_key
        )
        
        # Run the search only (no expansion)
        paper_agent.search()
        
        # Extract relevant papers for the response
        papers = []
        for query, papers_list in paper_agent.root.child.items():
            for paper in papers_list:
                papers.append({
                    "title": paper.title,
                    "arxiv_id": paper.arxiv_id,
                    "abstract": paper.abstract,
                    "score": paper.select_score,
                    "source": paper.source,
                    "depth": paper.depth
                })
        
        # Sort papers by relevance score
        papers.sort(key=lambda x: x["score"], reverse=True)
        
        # Return results
        return {
            "papers": papers,
            "total_found": len(papers),
            "relevant_papers": len([p for p in papers if p["score"] > 0.5]),
            "search_queries": list(paper_agent.root.child.keys()),
            "root": paper_agent.root.todic()
        }
    
    def expand_citations(self, arxiv_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Expand citations for a specific paper
        
        Args:
            arxiv_id: arXiv ID of the paper
            depth: Depth of citation expansion
            
        Returns:
            Dictionary containing expansion results
        """
        # Check if agents are initialized
        if not self.crawler or not self.selector:
            raise ValueError("Agents not initialized. Cannot expand citations.")
        
        # Get paper metadata
        metadata = get_paper_metadata_by_id(arxiv_id)
        if not metadata:
            raise ValueError(f"Paper with arXiv ID {arxiv_id} not found.")
        
        # Create a PaperNode for the paper
        from paper_node import PaperNode
        paper = PaperNode({
            "title": metadata["title"],
            "arxiv_id": arxiv_id,
            "depth": 0,
            "abstract": metadata["abstract"],
            "sections": "",
            "source": "User selected",
            "select_score": 1.0,
            "extra": {}
        })
        
        # Create a PaperAgent with the paper as the starting point
        paper_agent = PaperAgent(
            user_query=f"Expand citations for {metadata['title']}",
            crawler=self.crawler,
            selector=self.selector,
            expand_layers=depth,
            search_queries=0,  # No search queries, only expansion
            search_papers=0,
            expand_papers=MAX_EXPAND_PAPERS,
            google_key=self.google_key
        )
        
        # Add the paper to the queue
        paper_agent.papers_queue = [paper]
        
        # Run expansion
        for d in range(depth):
            paper_agent.expand(d)
        
        # Extract cited papers
        cited_papers = []
        for section_name, papers_list in paper.child.items():
            for cited_paper in papers_list:
                cited_papers.append({
                    "title": cited_paper.title,
                    "arxiv_id": cited_paper.arxiv_id,
                    "abstract": cited_paper.abstract,
                    "score": cited_paper.select_score,
                    "source": cited_paper.source,
                    "section": section_name,
                    "depth": cited_paper.depth
                })
        
        # Sort papers by relevance score
        cited_papers.sort(key=lambda x: x["score"], reverse=True)
        
        # Return results
        return {
            "paper": {
                "title": metadata["title"],
                "arxiv_id": arxiv_id,
                "abstract": metadata["abstract"]
            },
            "cited_papers": cited_papers,
            "total_cited": len(cited_papers),
            "relevant_cited": len([p for p in cited_papers if p["score"] > 0.5]),
            "sections": list(paper.child.keys())
        }
    
    def get_paper_info(self, arxiv_id: str) -> Dict[str, Any]:
        """
        Get information about a specific paper
        
        Args:
            arxiv_id: arXiv ID of the paper
            
        Returns:
            Dictionary containing paper information
        """
        # Get paper metadata
        metadata = get_paper_metadata_by_id(arxiv_id)
        if not metadata:
            raise ValueError(f"Paper with arXiv ID {arxiv_id} not found.")
        
        return metadata

class DirectSearchService:
    """
    A simpler search service that directly uses Google Search API without agents
    """
    def __init__(self, google_key=None):
        """
        Initialize the direct search service
        
        Args:
            google_key: Google Search API key
        """
        self.google_key = google_key or os.getenv("GOOGLE_KEY")
        
        if not self.google_key:
            raise ValueError("Google Search API key not found. Please provide it or set GOOGLE_KEY environment variable.")
    
    def search_papers(self, query: str, num_results: int = MAX_SEARCH_PAPERS) -> List[Dict[str, Any]]:
        """
        Search for papers related to the query
        
        Args:
            query: User query
            num_results: Number of results to return
            
        Returns:
            List of dictionaries containing paper information
        """
        # Search for arXiv IDs
        arxiv_ids = google_search_arxiv_id(query, num=num_results, google_key=self.google_key)
        
        # Get paper metadata
        papers = []
        for arxiv_id in arxiv_ids:
            metadata = get_paper_metadata_by_id(arxiv_id)
            if metadata:
                papers.append({
                    "title": metadata["title"],
                    "arxiv_id": arxiv_id,
                    "abstract": metadata["abstract"],
                    "authors": metadata["authors"],
                    "published": metadata["published"],
                    "source": "Google Search"
                })
        
        return papers

# Example usage
if __name__ == "__main__":
    # Example: Search for papers
    search_service = SearchService()
    results = search_service.search_papers("Large language models for scientific literature")
    
    print(f"Found {results['total_found']} papers, {results['relevant_papers']} relevant")
    for i, paper in enumerate(results["papers"][:5]):
        print(f"{i+1}. {paper['title']} (Score: {paper['score']:.2f})")
