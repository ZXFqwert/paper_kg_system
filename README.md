# 论文知识图谱系统

一个基于Web的论文知识图谱系统，实现从论文搜索到智能问答的完整工作流。

## 设计思想与标准

### 核心设计理念
- **零数据库依赖**: 完全基于文件系统存储，避免复杂的数据库配置
- **单一LLM标准**: 仅支持OpenAI API，确保接口统一性和兼容性
- **直接代码集成**: nano-graphrag核心代码直接集成，避免pip依赖冲突
- **本地化部署**: 设计为个人本地应用，单机运行
- **模块化架构**: 功能解耦，易于维护和扩展

### 技术标准
- **前端**: 原生HTML/CSS/JS + Bootstrap，无框架依赖
- **后端**: Python Flask，轻量级RESTful API
- **存储**: JSON文件 + 文本文件，人类可读
- **异步**: 长任务异步执行，实时进度反馈
- **配置**: 统一配置管理，环境变量传递

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Flask Backend  │    │  File Storage   │
│                 │    │                 │    │                 │
│ ├─ Search UI    │    │ ├─ ArXiv Client │    │ ├─ papers/      │
│ ├─ Graph UI     │◄──►│ ├─ GraphRAG Mgr │◄──►│ ├─ graph/       │
│ └─ Settings UI  │    │ └─ Config Mgr   │    │ └─ config.json  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │                 │
                       │ ├─ Chat Models  │
                       │ └─ Embeddings   │
                       └─────────────────┘
```

### 核心模块

#### 1. 前端层 (Static Files)
```
static/
├── js/app.js          # 单页面应用逻辑
├── css/style.css      # 响应式样式设计
└── templates/         # HTML模板
    └── index.html     # 主界面模板
```

#### 2. 后端层 (Core Modules)
```
core/
├── arxiv_client.py    # ArXiv API封装
├── paper_manager.py   # 论文数据管理
├── graphrag_manager.py # 知识图谱核心
├── config_manager.py  # 配置统一管理
├── llm_client.py      # OpenAI API封装
└── nano_graphrag/     # GraphRAG核心集成
```

#### 3. 存储层 (File System)
```
data/
├── papers/
│   ├── metadata.json  # 论文元数据索引
│   └── contents/      # 论文全文内容
├── graph/             # GraphRAG数据存储
│   ├── chunks/        # 文本块存储
│   ├── entities/      # 实体向量存储
│   └── communities/   # 社区报告存储
└── config.json        # 系统配置文件
```

## 数据流设计

### 完整数据流
```
用户关键词 → ArXiv API → 论文检索结果 → 前端展示
     ↓
论文收录决策 → 元数据保存 → 本地文件存储
     ↓
内容抽取启动 → LLM文本切分 → 实体关系提取 → 图数据存储
     ↓
知识图谱构建 → 社区检测算法 → 社区摘要生成 → 查询就绪
     ↓
用户提问 → Local/Global检索 → 上下文组装 → LLM生成回答
```

### 状态流转
```
论文状态: [搜索] → [收录] → [抽取中] → [已抽取] → [构建完成]
任务状态: [未开始] → [进行中] → [已完成] → [错误]
查询状态: [输入] → [检索] → [生成] → [返回]
```

## 核心逻辑设计

### 1. 三大界面逻辑

#### 论文检索界面
- **目标**: ArXiv论文搜索和收录管理
- **输入**: 关键词、分页参数、排序方式
- **处理**: ArXiv API调用 → 结果解析 → 收录状态检查
- **输出**: 论文卡片网格 → 收录/查看/下载操作

#### 知识图谱界面
- **目标**: 论文内容抽取和图谱构建
- **左侧**: 收录论文管理 → 抽取进度追踪 → 状态可视化
- **右侧**: 图谱构建控制 → Local/Global问答 → 对话历史

#### 系统设置界面
- **目标**: OpenAI配置和系统参数调优
- **配置**: API Key/Base URL → 模型选择 → 参数调节
- **功能**: 连接测试 → 配置持久化 → 状态监控

### 2. 查询模式设计

#### Local查询模式
- **数据源**: 实体向量数据库 + 关系图
- **检索方式**: 语义相似度匹配 + 图邻域扩展
- **适用场景**: 具体事实查询、实体关系探索
- **响应特点**: 精确、快速、细粒度

#### Global查询模式
- **数据源**: 社区摘要报告
- **检索方式**: 摘要语义匹配 + 主题聚类
- **适用场景**: 概念性问题、领域趋势分析
- **响应特点**: 宏观、深度、概念性

### 3. 异步任务设计

#### 抽取任务流程
```python
async def extract_paper():
    # 1. 状态初始化
    progress = ExtractionProgress(paper_id, "开始抽取")
    
    # 2. 文本预处理
    progress.update("文本切分中...", 0.2)
    chunks = await text_chunking()
    
    # 3. 实体关系抽取
    progress.update("实体抽取中...", 0.6)
    entities = await entity_extraction(chunks)
    
    # 4. 图数据存储
    progress.update("保存图数据...", 0.9)
    await save_graph_data(entities)
    
    # 5. 完成状态
    progress.complete()
```

#### 构建任务流程
```python
async def build_knowledge_graph():
    # 1. 数据完整性检查
    validate_extracted_data()
    
    # 2. 图社区检测
    progress.update("社区检测...", 0.3)
    await graph.clustering()
    
    # 3. 社区摘要生成
    progress.update("生成摘要...", 0.6)
    await generate_community_reports()
    
    # 4. 索引构建完成
    progress.complete()
```

## 技术实现要点

### 1. 配置管理策略
```python
# 统一配置接口
config_manager.get_openai_config()  # OpenAI相关
config_manager.get_system_config()  # 系统参数
config_manager.get_graph_config()   # 图算法参数

# 环境变量同步
os.environ['OPENAI_API_KEY'] = config['api_key']
os.environ['OPENAI_BASE_URL'] = config['api_base']
```

### 2. 存储抽象设计
```python
# 文件存储接口
JsonKVStorage    # 键值对存储 (配置、元数据)
HNSWVectorDB     # 向量存储 (实体嵌入)
NetworkXGraph    # 图存储 (实体关系)
FileSystemStorage # 文件存储 (论文内容)
```

### 3. API设计规范
```python
# RESTful接口标准
GET    /api/config              # 获取配置
POST   /api/config              # 更新配置
GET    /api/collected_papers    # 获取收录论文
POST   /api/extract_paper/{id}  # 启动抽取任务
GET    /api/task_status/{id}    # 查询任务状态
POST   /api/query               # 知识图谱问答
```

## 部署说明

### 环境要求
- **操作系统**: Linux/macOS/Windows
- **Python版本**: 3.8+
- **内存要求**: 4GB+ (推荐8GB+)
- **网络要求**: 能访问ArXiv和OpenAI API

### 一键部署
```bash
# 1. 获取源码
git clone <repository-url>
cd paper_kg_system

# 2. 执行部署脚本
chmod +x run.sh
./run.sh
```

### 手动部署
```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python app.py
```

### 初始配置
1. 打开浏览器访问 `http://localhost:5000`
2. 进入"系统设置"页面
3. 配置OpenAI API信息：
   ```
   API Key: sk-your-openai-api-key
   Base URL: https://api.openai.com/v1 (或代理URL)
   Extract Model: gpt-4o
   QA Model: gpt-4o
   Temperature: 0.1
   ```
4. 点击"测试连接"验证配置
5. 保存设置并开始使用

### 代理配置 (可选)
如需使用代理访问OpenAI，修改Base URL为：
```
https://your-proxy-domain.com/v1
```

## 核心优势

### 架构优势
- **零运维**: 无数据库，无复杂依赖
- **高内聚**: 功能模块清晰分离
- **低耦合**: 接口标准化，易于替换
- **可扩展**: 模块化设计，支持功能扩展

### 技术优势
- **统一接口**: 只依赖OpenAI API，避免多LLM兼容问题
- **直接集成**: nano-graphrag核心代码集成，避免版本冲突
- **实时反馈**: 异步任务进度实时显示
- **状态管理**: 完整的任务状态流转追踪

### 用户体验优势
- **流程清晰**: 搜索→收录→抽取→构建→问答的线性流程
- **状态明确**: 每个阶段都有清晰的视觉反馈
- **模式分离**: Local/Global查询模式界限分明
- **错误友好**: 详细的错误信息和操作指导

---

**设计原则**: 简单、可靠、易用、可维护 