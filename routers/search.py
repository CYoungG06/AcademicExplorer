from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import json
import uuid
from pathlib import Path

# Import services
from services.search_service import SearchService, DirectSearchService

# Create router
router = APIRouter(
    prefix="/api/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models
class SearchQuery(BaseModel):
    query: str
    search_queries: int = 5
    search_papers: int = 10
    expand_papers: int = 10

class ExpandRequest(BaseModel):
    arxiv_id: str
    depth: int = 1

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# In-memory storage for active tasks
active_tasks = {}

# Helper functions
def generate_task_id():
    return str(uuid.uuid4())

def update_task_status(task_id: str, status: str, progress: float, result=None, message=None):
    if task_id in active_tasks:
        active_tasks[task_id].update({
            "status": status,
            "progress": progress,
            "result": result,
            "message": message
        })

# Dependency to get SearchService
def get_search_service():
    from agent import Agent
    from constants import CRAWLER_MODEL, SELECTOR_MODEL
    
    try:
        crawler = Agent(os.getenv("CRAWLER_MODEL", CRAWLER_MODEL), "crawler")
        selector = Agent(os.getenv("SELECTOR_MODEL", SELECTOR_MODEL), "selector")
        return SearchService(crawler=crawler, selector=selector)
    except Exception as e:
        print(f"Failed to initialize agents: {e}")
        return None

# Dependency to get DirectSearchService
def get_direct_search_service():
    try:
        return DirectSearchService()
    except Exception as e:
        print(f"Failed to initialize direct search service: {e}")
        return None

# Background task functions
def search_papers_task(task_id: str, query: str, search_queries: int, search_papers: int, expand_papers: int, search_service: SearchService):
    try:
        update_task_status(task_id, "processing", 0.1, message="初始化搜索...")
        
        # Search for papers
        results = search_service.search_papers(
            query=query,
            search_queries=search_queries,
            search_papers=search_papers,
            expand_papers=expand_papers
        )
        
        # Save results
        result_path = os.path.join("results", f"search_{task_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Extract relevant papers for the response
        papers = results["papers"]
        
        update_task_status(
            task_id, 
            "completed", 
            1.0, 
            result={
                "papers": papers,
                "total_found": len(papers),
                "relevant_papers": results["relevant_papers"],
                "search_queries": results["search_queries"],
                "result_file": result_path
            }
        )
    except Exception as e:
        update_task_status(task_id, "failed", 0, message=f"搜索失败: {str(e)}")

def expand_citations_task(task_id: str, arxiv_id: str, depth: int, search_service: SearchService):
    try:
        update_task_status(task_id, "processing", 0.1, message="初始化引文扩展...")
        
        # Expand citations
        results = search_service.expand_citations(
            arxiv_id=arxiv_id,
            depth=depth
        )
        
        # Save results
        result_path = os.path.join("results", f"expand_{task_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        update_task_status(
            task_id, 
            "completed", 
            1.0, 
            result={
                "paper": results["paper"],
                "cited_papers": results["cited_papers"],
                "total_cited": results["total_cited"],
                "relevant_cited": results["relevant_cited"],
                "sections": results["sections"],
                "result_file": result_path
            }
        )
    except Exception as e:
        update_task_status(task_id, "failed", 0, message=f"引文扩展失败: {str(e)}")

# API endpoints
@router.post("", response_model=TaskResponse)
async def search_papers(search_query: SearchQuery, background_tasks: BackgroundTasks, search_service: Optional[SearchService] = Depends(get_search_service)):
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not available")
    
    task_id = generate_task_id()
    active_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
        "message": "任务已加入队列"
    }
    
    background_tasks.add_task(
        search_papers_task,
        task_id,
        search_query.query,
        search_query.search_queries,
        search_query.search_papers,
        search_query.expand_papers,
        search_service
    )
    
    return {"task_id": task_id, "status": "queued", "message": "搜索任务已启动"}

@router.post("/expand", response_model=TaskResponse)
async def expand_citations(expand_request: ExpandRequest, background_tasks: BackgroundTasks, search_service: Optional[SearchService] = Depends(get_search_service)):
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not available")
    
    task_id = generate_task_id()
    active_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
        "message": "任务已加入队列"
    }
    
    background_tasks.add_task(
        expand_citations_task,
        task_id,
        expand_request.arxiv_id,
        expand_request.depth,
        search_service
    )
    
    return {"task_id": task_id, "status": "queued", "message": "引文扩展任务已启动"}

@router.get("/direct")
async def direct_search(query: str, limit: int = 10, direct_search_service: Optional[DirectSearchService] = Depends(get_direct_search_service)):
    if not direct_search_service:
        raise HTTPException(status_code=503, detail="Direct search service not available")
    
    try:
        papers = direct_search_service.search_papers(query, num_results=limit)
        return {"papers": papers, "total": len(papers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper/{arxiv_id}")
async def get_paper_info(arxiv_id: str, search_service: Optional[SearchService] = Depends(get_search_service)):
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not available")
    
    try:
        paper_info = search_service.get_paper_info(arxiv_id)
        return paper_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "result": task["result"],
        "message": task["message"]
    }
