# 智能文献处理系统 - 文档

欢迎阅读智能文献处理系统的文档。本文档提供了系统的详细信息，包括安装、使用、开发和API参考。

## 文档目录

- [API文档](api.md) - API端点和使用方法
- [架构文档](architecture.md) - 系统架构和设计
- [用户指南](user_guide.md) - 系统使用指南
- [安装指南](installation.md) - 安装和配置指南
- [开发指南](development.md) - 开发和贡献指南

## 系统概述

智能文献处理系统是一个基于大语言模型(LLM)的智能文献处理平台，集检索与综述分析于一体，旨在提升学术阅读与研究效率。系统由两个核心模块组成：

1. **文献检索模块**：根据用户查询搜索相关论文，并支持引文网络扩展。
2. **多文献对比综述模块**：分析多篇论文，生成对比综述。

## 快速入门

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/my_search.git
cd my_search

# 安装依赖
python setup.py
pip install -r requirements.txt

# 配置环境变量
# 编辑.env文件，添加API密钥
```

### 运行

```bash
# 运行系统
python run.py
```

### 访问

打开浏览器，访问：

```
http://localhost:8000
```

## 文档更新

本文档会随着系统的更新而更新。如果您发现文档中的错误或有改进建议，请提交Issue或Pull Request。

## 贡献

欢迎贡献代码和文档。请参阅[开发指南](development.md)了解如何贡献。

## 许可证

本项目采用MIT许可证。详情请参阅LICENSE文件。
