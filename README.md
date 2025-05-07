# AcademicExplorer

LLM 驱动的文献智能体平台，集**检索与综述分析**于一体，提升学术阅读与研究效率。

## 系统功能

本系统主要包含两个核心功能模块：

1. **文献检索与引文网络扩展模块**（部分参考并修改自 PaSa：[https://github.com/bytedance/pasa](https://github.com/bytedance/pasa)）：
   - 根据用户查询生成多个智能改写查询
   - 通过谷歌检索 API 获取论文，由 ArXiv API 获取论文元信息
   - 支持对每篇论文的动态引文网络扩展，深入挖掘相关文献

2. **多文献对比综述模块**（部分参考自论文 ChatCite：[https://arxiv.org/abs/2403.02574](https://arxiv.org/abs/2403.02574)）：
   - 支持对多篇论文进行对比综述
   - 可以处理搜索到的论文或用户上传的 PDF 文件
   - 使用 MinerU API 提取 PDF 内容，转换为结构化数据

## 技术架构

- **前端**：HTML, CSS, JavaScript, Bootstrap
- **后端**：FastAPI, Python
- **核心技术**：LLM)，PDF处理，文本分析

## 系统架构图

```
前端 (HTML/CSS/JS) <--> FastAPI后端
                         |
                         ├── 文献检索模块
                         |   ├── 搜索论文 (PaperAgent)
                         |   └── 扩展引文 (ExpandPaper)
                         |
                         └── 对比综述模块
                             ├── 处理PDF (MinerU)
                             ├── 提取要素 (KeyElementExtractor)
                             └── 生成综述 (ReviewGenerator/ReviewSynthesizer)
```

## 安装与运行

### 环境要求

- Python 3.10+
- 相关 API 密钥:
  - OpenAI-like API 密钥
  - Google Search API 密钥（Serper）
  - MinerU API 密钥

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/CYoungG06/AcademicExplorer.git
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
cd AcademicExplorer
python run.py
```

## API文档

启动应用后，可以通过以下URL访问API文档：

- Swagger UI: http://localhost:your_port/docs
- ReDoc: http://localhost:your_port/redoc

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

## 许可证

[MIT](LICENSE)
