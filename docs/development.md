# 智能文献处理系统 - 开发指南

本文档提供了智能文献处理系统的开发指南，帮助开发者了解系统架构、代码组织和如何进行开发。

## 目录

1. [开发环境设置](#开发环境设置)
2. [项目结构](#项目结构)
3. [核心模块](#核心模块)
4. [API开发](#api开发)
5. [前端开发](#前端开发)
6. [测试](#测试)
7. [部署](#部署)
8. [贡献指南](#贡献指南)

## 开发环境设置

### 基本设置

1. 克隆仓库并安装依赖（参见[安装指南](installation.md)）
2. 设置开发环境变量（参见[配置](#配置)）
3. 安装开发工具（可选）：
   ```bash
   pip install black flake8 pytest pytest-cov
   ```

### 推荐的IDE和工具

- **IDE**: Visual Studio Code, PyCharm
- **代码格式化**: Black
- **代码检查**: Flake8
- **测试**: Pytest
- **API测试**: Postman, curl, httpie

### 配置

开发环境应该使用单独的`.env.dev`文件：

```bash
cp .env .env.dev
```

然后编辑`.env.dev`文件，添加开发环境特定的配置：

```
# API Keys
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
GOOGLE_KEY=your_google_search_api_key
MINERU_API_KEY=your_mineru_api_key

# Model Settings
CRAWLER_MODEL=deepseek-chat
SELECTOR_MODEL=deepseek-chat
REVIEW_MODEL=qwen-max-2025-01-25

# Development Settings
DEBUG=true
LOG_LEVEL=debug
```

启动开发服务器时，使用以下命令：

```bash
DOTENV_FILE=.env.dev python run.py
```

或者：

```bash
DOTENV_FILE=.env.dev uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

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
│   ├── index.html              # 前端页面
│   └── js/                     # JavaScript文件
│       ├── api.js              # API客户端
│       └── main.js             # 主要JavaScript代码
├── docs/                       # 文档
├── tests/                      # 测试
├── expand_paper.py             # 引文扩展模块
├── paper_agent.py              # 论文代理模块
├── paper_node.py               # 论文节点模块
├── agent.py                    # 代理模块
├── search_from_google.py       # Google搜索模块
├── prompts.json                # 提示词模板
├── setup.py                    # 安装脚本
├── run.py                      # 运行脚本
├── test_api.py                 # API测试脚本
├── test_all.py                 # 全面测试脚本
├── requirements.txt            # 项目依赖
├── Makefile                    # Makefile
└── .env                        # 环境变量
```

## 核心模块

### 1. 文献检索模块

#### 主要文件

- `agent.py`: 实现基于LLM的代理
- `paper_agent.py`: 实现论文搜索代理
- `paper_node.py`: 实现论文节点数据结构
- `expand_paper.py`: 实现引文扩展功能
- `search_from_google.py`: 实现Google搜索功能
- `services/search_service.py`: 搜索服务
- `routers/search.py`: 搜索API路由

#### 开发指南

1. **添加新的搜索源**:
   
   在`services/search_service.py`中添加新的搜索源：

   ```python
   def search_from_new_source(self, query, num_results=10):
       # 实现新的搜索源
       pass
   ```

   然后在`search_papers`方法中调用它：

   ```python
   def search_papers(self, query, ...):
       # 现有代码
       results_from_new_source = self.search_from_new_source(query, num_results)
       all_results.extend(results_from_new_source)
       # 继续处理
   ```

2. **修改搜索算法**:

   搜索算法主要在`paper_agent.py`中实现，可以修改`run`方法来改进搜索算法。

3. **调整提示词**:

   提示词模板存储在`prompts.json`文件中，可以根据需要调整提示词。

### 2. 多文献对比综述模块

#### 主要文件

- `ComparativeReviewer/MinerU.py`: PDF处理
- `ComparativeReviewer/KeyElementExtractor.py`: 关键要素提取
- `ComparativeReviewer/ReviewGenerator.py`: 综述生成
- `ComparativeReviewer/ReviewSynthesizer.py`: 综述合成
- `services/review_service.py`: 综述服务
- `services/pdf_service.py`: PDF处理服务
- `routers/review.py`: 综述API路由

#### 开发指南

1. **改进PDF处理**:

   PDF处理主要在`MinerU.py`中实现，可以修改`process_pdfs`方法来改进PDF处理。

2. **改进关键要素提取**:

   关键要素提取主要在`KeyElementExtractor.py`中实现，可以修改`process_paper`方法来改进关键要素提取。

3. **改进综述生成**:

   综述生成主要在`ReviewGenerator.py`和`ReviewSynthesizer.py`中实现，可以修改`generate_literature_review`方法来改进综述生成。

## API开发

### API架构

系统使用FastAPI框架，API路由分为三个模块：

- `routers/search.py`: 文献检索相关API
- `routers/review.py`: 对比综述相关API
- `routers/utils.py`: 工具类API

### 添加新的API端点

1. 在相应的路由文件中添加新的端点：

   ```python
   @router.get("/new-endpoint")
   async def new_endpoint():
       # 实现新的端点
       return {"message": "New endpoint"}
   ```

2. 如果需要添加新的路由模块，创建新的路由文件，然后在`app.py`中注册：

   ```python
   from routers import new_router
   app.include_router(new_router.router)
   ```

### API文档

系统使用FastAPI的自动文档生成功能，可以通过以下URL访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 前端开发

### 前端架构

前端使用HTML, CSS和JavaScript构建，采用Bootstrap框架实现响应式设计。主要文件：

- `static/index.html`: 主页面
- `static/js/api.js`: API客户端
- `static/js/main.js`: 主要JavaScript代码

### 修改前端

1. 修改HTML：编辑`index.html`文件
2. 修改JavaScript：编辑`static/js/main.js`文件
3. 修改API客户端：编辑`static/js/api.js`文件

### 添加新的前端功能

1. 在`index.html`中添加新的HTML元素
2. 在`static/js/main.js`中添加新的JavaScript代码
3. 如果需要调用新的API端点，在`static/js/api.js`中添加新的方法

## 测试

### 单元测试

系统使用Pytest进行单元测试，测试文件存放在`tests`目录中。

运行单元测试：

```bash
pytest
```

### API测试

系统提供了API测试脚本`test_api.py`，可以测试API端点是否正常工作。

运行API测试：

```bash
python test_api.py
```

或者使用Makefile：

```bash
make test-api
```

### 全面测试

系统提供了全面测试脚本`test_all.py`，可以测试整个系统是否正常工作。

运行全面测试：

```bash
python test_all.py
```

或者使用Makefile：

```bash
make test
```

## 部署

### 开发环境

开发环境使用`uvicorn`启动服务器：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 生产环境

生产环境推荐使用`gunicorn`和`uvicorn`：

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

### Docker部署

系统提供了Dockerfile，可以使用Docker部署：

```bash
docker build -t my_search .
docker run -p 8000:8000 my_search
```

## 贡献指南

### 代码风格

系统使用Black进行代码格式化，使用Flake8进行代码检查。

格式化代码：

```bash
black .
```

检查代码：

```bash
flake8
```

### 提交代码

1. 创建分支：`git checkout -b feature/your-feature`
2. 提交代码：`git commit -m "Add your feature"`
3. 推送分支：`git push origin feature/your-feature`
4. 创建Pull Request

### 报告问题

如果您发现问题，请在GitHub上创建Issue，包括以下信息：

1. 问题描述
2. 复现步骤
3. 期望行为
4. 实际行为
5. 系统信息（操作系统、Python版本等）
