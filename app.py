import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv

# Import routers
from routers import search, review, utils

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="智能文献处理系统",
    description="基于大语言模型的智能文献处理平台，集检索与综述分析于一体",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Copy index.html to static directory if it exists
if os.path.exists("index.html") and not os.path.exists("static/index.html"):
    import shutil
    os.makedirs("static", exist_ok=True)
    shutil.copy("index.html", "static/index.html")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(search.router)
app.include_router(review.router)
app.include_router(utils.router)

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head>
                <title>智能文献处理系统</title>
            </head>
            <body>
                <h1>智能文献处理系统</h1>
                <p>API 文档: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
