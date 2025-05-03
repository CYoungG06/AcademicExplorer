import os
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
import tempfile
import shutil
from openai import OpenAI
from dotenv import load_dotenv

# Import existing modules
from ComparativeReviewer.KeyElementExtractor import KeyElementExtractor, PaperProcessor
from ComparativeReviewer.ReviewSynthesizer import generate_literature_review

# Load environment variables
load_dotenv()

class ReviewService:
    def __init__(self, api_key=None, model="deepseek-chat", base_url=None):
        """
        Initialize the review service
        
        Args:
            api_key: OpenAI API key (if None, will try to read from environment)
            model: Model to use for review generation
            base_url: Base URL for OpenAI API (if None, will use default)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please provide it or set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Initialize KeyElementExtractor
        self.extractor = KeyElementExtractor(self.api_key, self.model)
    
    def extract_key_elements(self, md_files: List[str]) -> List[Dict[str, Any]]:
        """
        Extract key elements from markdown files
        
        Args:
            md_files: List of paths to markdown files
            
        Returns:
            List of dictionaries containing key elements for each paper
        """
        papers_data = []
        
        for md_file in md_files:
            # Read paper content
            with open(md_file, "r", encoding="utf-8") as f:
                paper_content = f.read()
            
            # Extract key elements
            paper_data = self.extractor.process_paper(paper_content)
            paper_data["paper_id"] = os.path.basename(os.path.dirname(md_file))
            papers_data.append(paper_data)
        
        return papers_data
    
    def generate_review(self, papers_data: List[Dict[str, Any]], options: Dict[str, bool] = None) -> str:
        """
        Generate a review from paper data
        
        Args:
            papers_data: List of dictionaries containing key elements for each paper
            options: Dictionary of options for review generation
            
        Returns:
            Generated review text
        """
        # Apply options to papers_data if needed
        if options:
            # Example: If includeMethodology is False, remove methodology from papers_data
            if not options.get("includeMethodology", True):
                for paper in papers_data:
                    paper.pop("methodology", None)
            
            # Example: If includeResults is False, remove results from papers_data
            if not options.get("includeResults", True):
                for paper in papers_data:
                    paper.pop("results", None)
        
        # Generate review
        review = generate_literature_review(
            refs_list=papers_data,
            client=self.client,
            model=self.model,
            n_samples=2,
            n_votes=2
        )
        
        return review
    
    def process_papers_and_generate_review(self, md_files: List[str], options: Dict[str, bool] = None) -> Dict[str, Any]:
        """
        Process papers and generate a review
        
        Args:
            md_files: List of paths to markdown files
            options: Dictionary of options for review generation
            
        Returns:
            Dictionary containing the review and related information
        """
        # Extract key elements
        papers_data = self.extract_key_elements(md_files)
        
        # Generate review
        review = self.generate_review(papers_data, options)
        
        # Return result
        return {
            "review": review,
            "papers_processed": len(papers_data),
            "papers_data": papers_data
        }

class PaperDownloader:
    @staticmethod
    def download_arxiv_paper(arxiv_id: str, output_dir: str) -> Optional[str]:
        """
        Download a paper from arXiv
        
        Args:
            arxiv_id: arXiv ID of the paper
            output_dir: Directory to save the paper
            
        Returns:
            Path to the downloaded PDF file, or None if download failed
        """
        import requests
        from expand_paper import get_paper_metadata_by_id
        
        # Get paper metadata
        metadata = get_paper_metadata_by_id(arxiv_id)
        if not metadata:
            print(f"Failed to get metadata for {arxiv_id}")
            return None
        
        # Download PDF
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_path = os.path.join(output_dir, f"{arxiv_id}.pdf")
        
        try:
            response = requests.get(pdf_url)
            if response.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                return pdf_path
            else:
                print(f"Failed to download {arxiv_id}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Failed to download {arxiv_id}: {e}")
            return None
    
    @staticmethod
    def download_multiple_arxiv_papers(arxiv_ids: List[str], output_dir: str) -> List[Dict[str, Any]]:
        """
        Download multiple papers from arXiv
        
        Args:
            arxiv_ids: List of arXiv IDs
            output_dir: Directory to save the papers
            
        Returns:
            List of dictionaries containing information about downloaded papers
        """
        os.makedirs(output_dir, exist_ok=True)
        
        downloaded_papers = []
        for arxiv_id in arxiv_ids:
            pdf_path = PaperDownloader.download_arxiv_paper(arxiv_id, output_dir)
            if pdf_path:
                # Get paper metadata
                from expand_paper import get_paper_metadata_by_id
                metadata = get_paper_metadata_by_id(arxiv_id)
                
                downloaded_papers.append({
                    "arxiv_id": arxiv_id,
                    "title": metadata["title"] if metadata else arxiv_id,
                    "path": pdf_path
                })
        
        return downloaded_papers

# Example usage
if __name__ == "__main__":
    # Example: Download papers
    output_dir = "temp/downloaded_papers"
    arxiv_ids = ["2101.12345", "2102.12345"]
    downloaded_papers = PaperDownloader.download_multiple_arxiv_papers(arxiv_ids, output_dir)
    
    # Example: Process papers and generate review
    if downloaded_papers:
        # Process PDFs to get markdown files
        from services.pdf_service import PDFProcessor
        
        pdf_folder = output_dir
        md_output_folder = "temp/md_output"
        
        processor = PDFProcessor()
        md_files = processor.process_pdfs(pdf_folder, md_output_folder)
        
        # Generate review
        review_service = ReviewService()
        result = review_service.process_papers_and_generate_review(md_files)
        
        print(f"Generated review for {result['papers_processed']} papers:")
        print(result["review"])
