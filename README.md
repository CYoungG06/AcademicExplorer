# 智能文献处理系统

基于大语言模型的智能文献处理平台，集检索与综述分析于一体，提升学术阅读与研究效率。

## 系统功能

本系统主要包含两个核心功能模块：

1. **文献检索与引文网络扩展模块**：
   - 根据用户查询生成多个搜索关键词
   - 通过搜索API获取论文
   - 支持引文网络扩展，深入挖掘相关文献

2. **多文献对比综述模块**：
   - 支持对多篇论文（最多5篇）进行对比综述
   - 可以处理搜索到的论文或用户上传的PDF文件
   - 使用MinerU提取PDF内容，转换为结构化数据

## 技术架构

- **前端**：HTML, CSS, JavaScript, Bootstrap
- **后端**：FastAPI, Python
- **核心技术**：大语言模型 (LLM)，PDF处理，文本分析

## 系统架构图

```
前端 (HTML/CSS/JS) <--> FastAPI后端
                         |
                         ├── 文献检索模块
                         |   ├── 搜索论文 (PaperAgent)
                         |   └── 扩展引文 (引文扩展)
                         |
                         └── 对比综述模块
                             ├── 处理PDF (MinerU)
                             ├── 提取要素 (KeyElementExtractor)
                             └── 生成综述 (ReviewGenerator/ReviewSynthesizer)
```

## 安装与运行

### 环境要求

- Python 3.8+
- 相关API密钥:
  - OpenAI API密钥
  - Google Search API密钥
  - MinerU API密钥

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/my_search.git
cd my_search
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

创建`.env`文件并添加以下内容：

```
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，如果使用其他API端点
GOOGLE_KEY=your_google_search_api_key
MINERU_API_KEY=your_mineru_api_key
CRAWLER_MODEL=deepseek-chat  # 可选，默认为deepseek-chat
SELECTOR_MODEL=deepseek-chat  # 可选，默认为deepseek-chat
REVIEW_MODEL=qwen-max-2025-01-25  # 可选，默认为qwen-max-2025-01-25
```

4. 运行应用

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

5. 访问应用

打开浏览器，访问 http://localhost:8000

## API文档

启动应用后，可以通过以下URL访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要API端点

### 文献检索

- `POST /api/search`: 搜索论文
- `POST /api/search/expand`: 扩展论文引文
- `GET /api/search/paper/{arxiv_id}`: 获取论文信息
- `GET /api/search/direct`: 直接搜索论文（不使用代理）

### 对比综述

- `POST /api/review/arxiv`: 从arXiv ID生成对比综述
- `POST /api/review/files`: 从上传的PDF文件生成对比综述
- `GET /api/review/task/{task_id}`: 获取任务状态
- `GET /api/review/download/{file_path}`: 下载生成的综述

### 工具

- `GET /api/utils/health`: 健康检查
- `GET /api/utils/system`: 获取系统信息
- `GET /api/utils/config`: 获取配置信息
- `GET /api/utils/tasks`: 获取所有活动任务
- `GET /api/utils/results`: 获取所有结果
- `DELETE /api/utils/results/{file_name}`: 删除结果文件
- `GET /api/utils/temp`: 获取所有临时文件
- `DELETE /api/utils/temp/{task_id}`: 删除任务的临时文件
- `DELETE /api/utils/temp`: 清理所有临时文件

## 项目结构

```
my_search/
├── app.py                      # FastAPI主应用
├── routers/                    # API路由
│   ├── search.py               # 文献检索相关路由
│   ├── review.py               # 对比综述相关路由
│   └── utils.py                # 工具类路由
├── services/                   # 业务逻辑
│   ├── search_service.py       # 文献检索服务
│   ├── review_service.py       # 对比综述服务
│   └── pdf_service.py          # PDF处理服务
├── ComparativeReviewer/        # 对比综述模块
│   ├── KeyElementExtractor.py  # 关键要素提取
│   ├── MinerU.py               # PDF处理
│   ├── ReviewGenerator.py      # 综述生成
│   └── ReviewSynthesizer.py    # 综述合成
├── static/                     # 静态文件
│   └── index.html              # 前端页面
├── expand_paper.py             # 引文扩展模块
├── paper_agent.py              # 论文代理模块
├── paper_node.py               # 论文节点模块
├── agent.py                    # 代理模块
├── search_from_google.py       # Google搜索模块
├── prompts.json                # 提示词模板
├── requirements.txt            # 项目依赖
└── .env                        # 环境变量
```

## 贡献

欢迎提交问题和拉取请求。

## 许可证

[MIT](LICENSE)
