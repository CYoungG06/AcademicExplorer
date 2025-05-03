from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import platform
import psutil
import json
from pathlib import Path

# Create router
router = APIRouter(
    prefix="/api/utils",
    tags=["utils"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models
class SystemInfo(BaseModel):
    os: str
    python_version: str
    cpu_count: int
    memory_total: float  # GB
    memory_available: float  # GB
    disk_total: float  # GB
    disk_free: float  # GB

class ConfigInfo(BaseModel):
    crawler_model: str
    selector_model: str
    review_model: str
    google_key_available: bool
    openai_api_available: bool
    mineru_api_available: bool

# API endpoints
@router.get("/health")
async def health_check():
    """
    Check if the API is running
    """
    return {"status": "ok", "version": "1.0.0"}

@router.get("/system", response_model=SystemInfo)
async def get_system_info():
    """
    Get system information
    """
    import sys
    
    # Get memory information
    memory = psutil.virtual_memory()
    memory_total = memory.total / (1024 ** 3)  # Convert to GB
    memory_available = memory.available / (1024 ** 3)  # Convert to GB
    
    # Get disk information
    disk = psutil.disk_usage('/')
    disk_total = disk.total / (1024 ** 3)  # Convert to GB
    disk_free = disk.free / (1024 ** 3)  # Convert to GB
    
    return {
        "os": platform.system(),
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "memory_total": memory_total,
        "memory_available": memory_available,
        "disk_total": disk_total,
        "disk_free": disk_free
    }

@router.get("/config", response_model=ConfigInfo)
async def get_config_info():
    """
    Get configuration information
    """
    return {
        "crawler_model": os.getenv("CRAWLER_MODEL", "deepseek-chat"),
        "selector_model": os.getenv("SELECTOR_MODEL", "deepseek-chat"),
        "review_model": os.getenv("REVIEW_MODEL", "qwen-max-2025-01-25"),
        "google_key_available": bool(os.getenv("GOOGLE_KEY")),
        "openai_api_available": bool(os.getenv("OPENAI_API_KEY")),
        "mineru_api_available": bool(os.getenv("MINERU_API_KEY") or os.path.exists("api.txt"))
    }

@router.get("/tasks")
async def get_active_tasks():
    """
    Get all active tasks
    """
    # Import active_tasks from both routers
    from routers.search import active_tasks as search_tasks
    from routers.review import active_tasks as review_tasks
    
    # Combine tasks
    all_tasks = {}
    
    for task_id, task in search_tasks.items():
        all_tasks[task_id] = {
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "message": task["message"],
            "type": "search"
        }
    
    for task_id, task in review_tasks.items():
        all_tasks[task_id] = {
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "message": task["message"],
            "type": "review"
        }
    
    return {"tasks": list(all_tasks.values())}

@router.get("/results")
async def get_results():
    """
    Get all results
    """
    results_dir = Path("results")
    if not results_dir.exists():
        return {"results": []}
    
    results = []
    for file_path in results_dir.glob("*"):
        if file_path.is_file():
            file_info = {
                "name": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_ctime,
                "modified": file_path.stat().st_mtime,
                "type": file_path.suffix[1:] if file_path.suffix else "unknown"
            }
            results.append(file_info)
    
    # Sort by modified time (newest first)
    results.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"results": results}

@router.delete("/results/{file_name}")
async def delete_result(file_name: str):
    """
    Delete a result file
    """
    file_path = Path("results") / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {"status": "ok", "message": f"File {file_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/temp")
async def get_temp_files():
    """
    Get all temporary files
    """
    temp_dir = Path("temp")
    if not temp_dir.exists():
        return {"temp_files": []}
    
    temp_files = []
    for file_path in temp_dir.glob("**/*"):
        if file_path.is_file():
            file_info = {
                "name": file_path.name,
                "path": str(file_path.relative_to(temp_dir)),
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_ctime,
                "modified": file_path.stat().st_mtime,
                "type": file_path.suffix[1:] if file_path.suffix else "unknown"
            }
            temp_files.append(file_info)
    
    # Sort by modified time (newest first)
    temp_files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"temp_files": temp_files}

@router.delete("/temp/{task_id}")
async def delete_temp_files(task_id: str):
    """
    Delete temporary files for a task
    """
    temp_dir = Path("temp") / task_id
    if not temp_dir.exists():
        raise HTTPException(status_code=404, detail="Task directory not found")
    
    try:
        import shutil
        shutil.rmtree(temp_dir)
        return {"status": "ok", "message": f"Temporary files for task {task_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/temp")
async def clean_temp_files():
    """
    Clean all temporary files
    """
    temp_dir = Path("temp")
    if not temp_dir.exists():
        return {"status": "ok", "message": "No temporary files to clean"}
    
    try:
        import shutil
        for path in temp_dir.glob("*"):
            if path.is_dir():
                shutil.rmtree(path)
        return {"status": "ok", "message": "All temporary files cleaned"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
