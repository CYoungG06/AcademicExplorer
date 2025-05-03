# 智能文献处理系统 - 安装指南

本文档提供了智能文献处理系统的安装和配置指南。

## 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置](#配置)
4. [启动系统](#启动系统)
5. [验证安装](#验证安装)
6. [常见问题](#常见问题)

## 系统要求

### 硬件要求

- CPU: 双核处理器或更高
- 内存: 至少4GB RAM（推荐8GB或更高）
- 硬盘空间: 至少1GB可用空间

### 软件要求

- 操作系统: Windows 10/11, macOS 10.15+, 或 Linux (Ubuntu 20.04+, CentOS 8+)
- Python: 3.8或更高版本
- pip: 最新版本
- 网络连接: 用于下载依赖和访问外部API

### API密钥要求

以下API密钥是可选的，但强烈推荐配置以获得完整功能：

- OpenAI API密钥: 用于生成对比综述
- Google Search API密钥: 用于搜索论文
- MinerU API密钥: 用于处理PDF文件

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/my_search.git
cd my_search
```

### 2. 创建虚拟环境（推荐）

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 运行安装脚本

系统提供了一个简便的安装脚本，可以自动设置项目结构和安装依赖：

```bash
python setup.py
```

或者使用Makefile（仅适用于macOS/Linux）：

```bash
make setup
make install
```

### 4. 手动安装依赖

如果您选择不使用安装脚本，可以手动安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

### 1. 环境变量

系统使用`.env`文件存储配置和API密钥。安装脚本会创建一个模板文件，您需要编辑它：

```bash
# 使用您喜欢的文本编辑器打开.env文件
nano .env  # 或者 vim .env, code .env 等
```

填写以下信息：

```
# API Keys
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，如果使用其他API端点
GOOGLE_KEY=your_google_search_api_key
MINERU_API_KEY=your_mineru_api_key

# Model Settings
CRAWLER_MODEL=deepseek-chat  # 可选，默认为deepseek-chat
SELECTOR_MODEL=deepseek-chat  # 可选，默认为deepseek-chat
REVIEW_MODEL=qwen-max-2025-01-25  # 可选，默认为qwen-max-2025-01-25
```

### 2. MinerU配置

如果您有MinerU API密钥，请将其添加到`api.txt`文件中：

```bash
echo "your_mineru_api_key" > api.txt
```

### 3. 创建必要的目录

安装脚本会自动创建以下目录，但如果您需要手动创建：

```bash
mkdir -p static uploads results temp services routers
```

### 4. 复制前端文件

确保`index.html`文件被复制到`static`目录：

```bash
cp index.html static/
```

## 启动系统

### 使用run.py脚本

最简单的方法是使用提供的`run.py`脚本：

```bash
python run.py
```

这将启动系统并自动打开浏览器。

### 使用Makefile

如果您使用的是macOS或Linux，可以使用Makefile：

```bash
make run
```

### 手动启动

您也可以手动启动系统：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 开发模式

如果您想在开发模式下运行系统（启用自动重载）：

```bash
python run.py --no-browser
```

或者：

```bash
make dev
```

## 验证安装

### 1. 访问系统

打开浏览器，访问：

```
http://localhost:8000
```

您应该能看到系统的主页。

### 2. 运行测试

系统提供了测试脚本，可以验证API是否正常工作：

```bash
python test_all.py
```

或者使用Makefile：

```bash
make test
```

### 3. 检查API健康状态

您可以通过访问以下URL检查API的健康状态：

```
http://localhost:8000/api/health
```

应该返回类似以下的JSON响应：

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## 常见问题

### 1. 依赖安装失败

如果依赖安装失败，请尝试：

```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

对于某些依赖，可能需要安装系统级别的库：

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev
```

#### CentOS/RHEL

```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel
```

#### macOS

```bash
xcode-select --install
```

### 2. 端口已被占用

如果8000端口已被占用，您可以使用不同的端口：

```bash
python run.py --port 8080
```

或者：

```bash
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### 3. API密钥问题

如果您看到关于API密钥的警告，请确保您已正确配置`.env`文件。系统将在启动时检查API密钥，并在Web界面上显示警告。

### 4. PDF处理问题

如果PDF处理失败，请确保：

1. MinerU API密钥已正确配置
2. PDF文件格式正确
3. PDF文件不是加密的

### 5. 系统无法启动

如果系统无法启动，请检查日志输出。常见原因包括：

1. Python版本不兼容
2. 依赖缺失
3. 端口冲突
4. 权限问题

如果问题仍然存在，请尝试重新安装系统或联系支持团队。
