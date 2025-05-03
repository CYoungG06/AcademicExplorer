from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import json
import uuid
import shutil
from pathlib import Path

# Import services
from services.review_service import ReviewService, PaperDownloader
from services.pdf_service import PDFProcessor

# Create router
router = APIRouter(
    prefix="/api/review",
    tags=["review"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models
class ReviewRequest(BaseModel):
    arxiv_ids: List[str]
    options: Dict[str, bool] = {"includeMethodology": True, "includeResults": True, "includeGaps": False}

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

# Dependency to get ReviewService
def get_review_service():
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("REVIEW_MODEL", "deepseek-chat")
        base_url = os.getenv("OPENAI_BASE_URL")
        return ReviewService(api_key=api_key, model=model, base_url=base_url)
    except Exception as e:
        print(f"Failed to initialize review service: {e}")
        return None

# Dependency to get PDFProcessor
def get_pdf_processor():
    try:
        api_key = os.getenv("MINERU_API_KEY")
        return PDFProcessor(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize PDF processor: {e}")
        return None

# Background task functions
def process_pdfs_task(task_id: str, file_paths: List[str], options: Dict[str, bool], pdf_processor: PDFProcessor, review_service: ReviewService):
    try:
        update_task_status(task_id, "processing", 0.1, message="处理PDF文件中...")
        
        # Create a temporary directory for PDF processing
        temp_dir = os.path.join("temp", task_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create PDF_FOLDER and OUTPUT_FOLDER for processing
        pdf_folder = os.path.join(temp_dir, "pdfs")
        output_folder = os.path.join(temp_dir, "mdss")
        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        # Copy PDFs to the temporary directory
        for file_path in file_paths:
            shutil.copy(file_path, os.path.join(pdf_folder, os.path.basename(file_path)))
        
        update_task_status(task_id, "processing", 0.2, message="提取PDF内容...")
        
        # Process PDFs to get markdown files
        md_files = pdf_processor.process_pdfs(pdf_folder, output_folder)
        
        if not md_files:
            update_task_status(task_id, "failed", 0, message="PDF处理失败，未能提取内容")
            return
        
        update_task_status(task_id, "processing", 0.5, message=f"提取了 {len(md_files)} 个文件的内容，开始生成综述...")
        
        # Generate review
        result = review_service.process_papers_and_generate_review(md_files, options)
        
        # Save the review
        review_path = os.path.join("results", f"review_{task_id}.txt")
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(result["review"])
        
        # Save paper data
        papers_data_path = os.path.join("results", f"papers_data_{task_id}.json")
        with open(papers_data_path, "w", encoding="utf-8") as f:
            json.dump(result["papers_data"], f, indent=2, ensure_ascii=False)
        
        update_task_status(
            task_id, 
            "completed", 
            1.0, 
            result={
                "review": result["review"],
                "review_file": review_path,
                "papers_processed": result["papers_processed"],
                "papers_data_file": papers_data_path
            }
        )
    except Exception as e:
        update_task_status(task_id, "failed", 0, message=f"综述生成失败: {str(e)}")

def download_arxiv_papers_task(task_id: str, arxiv_ids: List[str], options: Dict[str, bool], pdf_processor: PDFProcessor, review_service: ReviewService):
    try:
        update_task_status(task_id, "processing", 0.1, message="下载arXiv论文...")
        
        # Create a temporary directory for downloaded papers
        temp_dir = os.path.join("temp", task_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download papers
        downloaded_papers = PaperDownloader.download_multiple_arxiv_papers(arxiv_ids, temp_dir)
        
        if not downloaded_papers:
            update_task_status(task_id, "failed", 0, message="论文下载失败，未能获取任何论文")
            return
        
        update_task_status(
            task_id, 
            "processing", 
            0.3, 
            message=f"下载了 {len(downloaded_papers)} 篇论文，开始处理PDF..."
        )
        
        # Process the downloaded PDFs
        pdf_paths = [paper["path"] for paper in downloaded_papers]
        
        # Create PDF_FOLDER and OUTPUT_FOLDER for processing
        pdf_folder = os.path.join(temp_dir, "pdfs")
        output_folder = os.path.join(temp_dir, "mdss")
        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        # Copy PDFs to the processing directory
        for pdf_path in pdf_paths:
            shutil.copy(pdf_path, os.path.join(pdf_folder, os.path.basename(pdf_path)))
        
        # Process PDFs to get markdown files
        md_files = pdf_processor.process_pdfs(pdf_folder, output_folder)
        
        if not md_files:
            update_task_status(task_id, "failed", 0, message="PDF处理失败，未能提取内容")
            return
        
        update_task_status(task_id, "processing", 0.6, message=f"提取了 {len(md_files)} 个文件的内容，开始生成综述...")
        
        # Generate review
        result = review_service.process_papers_and_generate_review(md_files, options)
        
        # Save the review
        review_path = os.path.join("results", f"review_{task_id}.txt")
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(result["review"])
        
        # Save paper data
        papers_data_path = os.path.join("results", f"papers_data_{task_id}.json")
        with open(papers_data_path, "w", encoding="utf-8") as f:
            json.dump(result["papers_data"], f, indent=2, ensure_ascii=False)
        
        update_task_status(
            task_id, 
            "completed", 
            1.0, 
            result={
                "review": result["review"],
                "review_file": review_path,
                "papers_processed": result["papers_processed"],
                "papers_data_file": papers_data_path,
                "downloaded_papers": [{"arxiv_id": p["arxiv_id"], "title": p["title"]} for p in downloaded_papers]
            }
        )
    except Exception as e:
        update_task_status(task_id, "failed", 0, message=f"综述生成失败: {str(e)}")

# API endpoints
@router.post("/arxiv", response_model=TaskResponse)
async def generate_review_from_arxiv(
    review_request: ReviewRequest, 
    background_tasks: BackgroundTasks, 
    pdf_processor: Optional[PDFProcessor] = Depends(get_pdf_processor),
    review_service: Optional[ReviewService] = Depends(get_review_service)
):
    if not pdf_processor:
        raise HTTPException(status_code=503, detail="PDF processor not available")
    
    if not review_service:
        raise HTTPException(status_code=503, detail="Review service not available")
    
    task_id = generate_task_id()
    active_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
        "message": "任务已加入队列"
    }
    
    background_tasks.add_task(
        download_arxiv_papers_task,
        task_id,
        review_request.arxiv_ids,
        review_request.options,
        pdf_processor,
        review_service
    )
    
    return {"task_id": task_id, "status": "queued", "message": "综述生成任务已启动"}

@router.post("/files", response_model=TaskResponse)
async def generate_review_from_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    options: str = Form("{}"),
    pdf_processor: Optional[PDFProcessor] = Depends(get_pdf_processor),
    review_service: Optional[ReviewService] = Depends(get_review_service)
):
    if not pdf_processor:
        raise HTTPException(status_code=503, detail="PDF processor not available")
    
    if not review_service:
        raise HTTPException(status_code=503, detail="Review service not available")
    
    # Parse options
    try:
        options_dict = json.loads(options)
    except:
        options_dict = {}
    
    task_id = generate_task_id()
    active_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
        "message": "任务已加入队列"
    }
    
    # Create upload directory
    upload_dir = os.path.join("uploads", task_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded files
    file_paths = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_paths.append(file_path)
    
    if not file_paths:
        return HTTPException(status_code=400, detail="No valid PDF files uploaded")
    
    background_tasks.add_task(
        process_pdfs_task,
        task_id,
        file_paths,
        options_dict,
        pdf_processor,
        review_service
    )
    
    return {"task_id": task_id, "status": "queued", "message": "文件上传成功，开始处理"}

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

@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    full_path = os.path.join("results", file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(full_path)
