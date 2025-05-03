# 智能文献处理系统 API 文档

本文档描述了智能文献处理系统的API端点。

## 基础信息

- 基础URL: `http://localhost:8000`
- API版本: v1.0.0
- 内容类型: `application/json`

## 健康检查

### 检查API健康状态

```
GET /api/health
```

**响应**

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## 文献检索模块

### 搜索论文

```
POST /api/search
```

**请求体**

```json
{
  "query": "large language models for scientific literature",
  "expand_layers": 1,
  "search_queries": 5,
  "search_papers": 10,
  "expand_papers": 10
}
```

**参数说明**

- `query`: 搜索查询
- `expand_layers`: 引文扩展层数
- `search_queries`: 生成的搜索查询数量
- `search_papers`: 每个查询搜索的论文数量
- `expand_papers`: 每层扩展的论文数量

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "搜索任务已启动"
}
```

### 扩展论文引文

```
POST /api/search/expand
```

**请求体**

```json
{
  "arxiv_id": "2101.12345",
  "depth": 1
}
```

**参数说明**

- `arxiv_id`: arXiv ID
- `depth`: 引文扩展深度

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "引文扩展任务已启动"
}
```

### 直接搜索论文

```
GET /api/search/direct?query=large+language+models&limit=10
```

**查询参数**

- `query`: 搜索查询
- `limit`: 返回结果数量限制

**响应**

```json
{
  "papers": [
    {
      "title": "Large Language Model Agents: State-of-the-Art, Applications, and Challenges",
      "arxiv_id": "2303.08774",
      "abstract": "This paper presents a comprehensive survey...",
      "authors": ["Zhang, Wei", "Wang, Jing", "Chen, Xi"],
      "published": "2023-03-15",
      "source": "Google Search"
    },
    ...
  ],
  "total": 10
}
```

### 获取论文信息

```
GET /api/search/paper/{arxiv_id}
```

**路径参数**

- `arxiv_id`: arXiv ID

**响应**

```json
{
  "title": "Large Language Model Agents: State-of-the-Art, Applications, and Challenges",
  "authors": ["Zhang, Wei", "Wang, Jing", "Chen, Xi"],
  "published": "2023-03-15",
  "updated": "2023-04-10",
  "abstract": "This paper presents a comprehensive survey...",
  "arxiv_id": "2303.08774"
}
```

### 获取任务状态

```
GET /api/search/task/{task_id}
```

**路径参数**

- `task_id`: 任务ID

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "result": {
    "papers": [...],
    "total_found": 10,
    "result_file": "results/550e8400-e29b-41d4-a716-446655440000.json"
  },
  "message": null
}
```

## 对比综述模块

### 从arXiv ID生成对比综述

```
POST /api/review/arxiv
```

**请求体**

```json
{
  "arxiv_ids": ["2101.12345", "2102.12345", "2103.12345"],
  "options": {
    "includeMethodology": true,
    "includeResults": true,
    "includeGaps": false
  }
}
```

**参数说明**

- `arxiv_ids`: arXiv ID列表
- `options`: 综述选项

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "综述生成任务已启动"
}
```

### 从上传的PDF文件生成对比综述

```
POST /api/review/files
```

**表单数据**

- `files`: PDF文件列表
- `options`: 综述选项（JSON字符串）

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "文件上传成功，开始处理"
}
```

### 获取任务状态

```
GET /api/review/task/{task_id}
```

**路径参数**

- `task_id`: 任务ID

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "result": {
    "review": "本综述对比分析了3篇关于...",
    "review_file": "results/review_550e8400-e29b-41d4-a716-446655440000.txt",
    "papers_processed": 3
  },
  "message": null
}
```

### 下载文件

```
GET /api/review/download/{file_path}
```

**路径参数**

- `file_path`: 文件路径

**响应**

文件内容

## 工具模块

### 获取系统信息

```
GET /api/utils/system
```

**响应**

```json
{
  "os": "Linux",
  "python_version": "3.9.7",
  "cpu_count": 8,
  "memory_total": 16.0,
  "memory_available": 8.5,
  "disk_total": 512.0,
  "disk_free": 256.0
}
```

### 获取配置信息

```
GET /api/utils/config
```

**响应**

```json
{
  "crawler_model": "deepseek-chat",
  "selector_model": "deepseek-chat",
  "review_model": "qwen-max-2025-01-25",
  "google_key_available": true,
  "openai_api_available": true,
  "mineru_api_available": true
}
```

### 获取所有活动任务

```
GET /api/utils/tasks
```

**响应**

```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "processing",
      "progress": 0.5,
      "message": "搜索论文中...",
      "type": "search"
    },
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440001",
      "status": "completed",
      "progress": 1.0,
      "message": null,
      "type": "review"
    }
  ]
}
```

### 获取所有结果

```
GET /api/utils/results
```

**响应**

```json
{
  "results": [
    {
      "name": "550e8400-e29b-41d4-a716-446655440000.json",
      "path": "results/550e8400-e29b-41d4-a716-446655440000.json",
      "size": 1024,
      "created": 1620000000,
      "modified": 1620000000,
      "type": "json"
    },
    {
      "name": "review_550e8400-e29b-41d4-a716-446655440001.txt",
      "path": "results/review_550e8400-e29b-41d4-a716-446655440001.txt",
      "size": 2048,
      "created": 1620000000,
      "modified": 1620000000,
      "type": "txt"
    }
  ]
}
```

### 删除结果文件

```
DELETE /api/utils/results/{file_name}
```

**路径参数**

- `file_name`: 文件名

**响应**

```json
{
  "status": "ok",
  "message": "File 550e8400-e29b-41d4-a716-446655440000.json deleted"
}
```

### 获取所有临时文件

```
GET /api/utils/temp
```

**响应**

```json
{
  "temp_files": [
    {
      "name": "2101.12345.pdf",
      "path": "550e8400-e29b-41d4-a716-446655440000/2101.12345.pdf",
      "size": 1024,
      "created": 1620000000,
      "modified": 1620000000,
      "type": "pdf"
    }
  ]
}
```

### 删除任务的临时文件

```
DELETE /api/utils/temp/{task_id}
```

**路径参数**

- `task_id`: 任务ID

**响应**

```json
{
  "status": "ok",
  "message": "Temporary files for task 550e8400-e29b-41d4-a716-446655440000 deleted"
}
```

### 清理所有临时文件

```
DELETE /api/utils/temp
```

**响应**

```json
{
  "status": "ok",
  "message": "All temporary files cleaned"
}
