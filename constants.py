"""
Constants for the intelligent literature processing system.
This file centralizes configuration values to make them easier to change.
"""

# Model names
DEFAULT_MODEL = "deepseek-chat"  # Default model for all operations
CRAWLER_MODEL = "deepseek-chat"  # Model for search crawling
SELECTOR_MODEL = "deepseek-chat"  # Model for paper selection
REVIEW_MODEL = "deepseek-chat"   # Model for review generation

# API configuration
OPENAI_BASE_URL = "https://api.deepseek.com/v1"  # Base URL for API calls

# Search configuration
MAX_SEARCH_QUERIES = 5  # Maximum number of search queries to generate
MAX_SEARCH_PAPERS = 10  # Maximum number of papers to search per query
MAX_EXPAND_PAPERS = 10  # Maximum number of papers to expand per layer

# Review configuration
MAX_REVIEW_PAPERS = 5  # Maximum number of papers for review

# File paths
TEMP_DIR = "temp"       # Directory for temporary files
UPLOAD_DIR = "uploads"  # Directory for uploaded files
RESULTS_DIR = "results" # Directory for results
