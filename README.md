# AI 内容运营助手

基于 Vue 3、FastAPI 与 LangGraph 构建的 AI 内容创作工作台，覆盖选题、文案、人工审核、智能配图和发布包导出全流程。

## 功能特性

- **AI 选题生成**: 根据主题方向自动生成候选选题
- **AI 文章撰写**: 根据选定选题生成技术文章
- **Human-in-the-loop**: 支持人工介入的选题和审稿机制
- **配图生成**: 自动提取视觉要点并生成配图
- **状态持久化与断点恢复**: 使用 PostgreSQL Checkpointer 保存任务状态，支持人工审核暂停后继续执行

## 技术栈

### 前端

| 技术 | 用途 |
| --- | --- |
| **Vue 3.4+** | Composition API 驱动的单页工作台 |
| **Vite 5** | 本地开发、代理与生产构建 |
| **Tailwind CSS 4** | 响应式界面与组件样式 |
| **CVA / clsx / tailwind-merge** | 可复用 UI 组件与样式类合并 |
| **Axios** | 登录、工作流、历史任务与发布包接口请求 |
| **Server-Sent Events（SSE）** | 实时展示选题、写稿和配图生成进度 |

### 后端与接口

| 技术 | 用途 |
| --- | --- |
| **Python 3.10+** | 后端运行环境 |
| **FastAPI 0.128+** | 异步 REST API、SSE 流式响应与静态资源服务 |
| **Uvicorn 0.40+** | ASGI 开发与运行服务器 |
| **Pydantic 2 / Pydantic Settings** | 请求校验、数据模型与环境变量配置 |
| **python-dotenv** | 加载本地 `.env` 运行配置 |
| **HTTPX** | 异步调用图片生成服务与下载远程图片 |
| **Pillow** | 图片保存、处理与本地兜底图生成 |

### Agent 工作流与状态恢复

| 技术 | 用途 |
| --- | --- |
| **LangGraph 1.0+** | 选题、写稿、审稿、视觉提取和配图节点编排 |
| **LangChain / LangChain OpenAI** | 模型消息、流式输出、回调和 OpenAI 兼容接口封装 |
| **Human-in-the-loop** | 使用 `interrupt()` 与 `Command` 实现选题、文案和配图人工审核 |
| **langgraph-checkpoint-postgres 3.0+** | PostgreSQL Checkpoint 持久化 |
| **AsyncPostgresSaver** | 保存每个任务状态，支持暂停、恢复、历史查询和断点续跑 |

### 数据库与安全

| 技术 | 用途 |
| --- | --- |
| **PostgreSQL** | 用户、工作流状态和 Checkpoint 数据存储 |
| **SQLAlchemy 2 AsyncIO** | 用户数据异步 ORM |
| **AsyncPG** | SQLAlchemy PostgreSQL 异步驱动 |
| **Psycopg 3 / psycopg-pool** | Checkpointer 异步连接池与原生查询 |
| **JWT（python-jose）** | 用户身份认证与接口权限控制 |
| **Argon2 / Passlib / Bcrypt** | 密码哈希与兼容验证 |

### AI 与图片服务

| 服务 | 用途 |
| --- | --- |
| **阿里百炼 OpenAI 兼容接口** | 选题、文章和视觉 brief 生成 |
| **Qwen Plus / Qwen Turbo** | 标准写作模型与快速提取模型，可通过环境变量替换 |
| **火山方舟图片生成 API** | 根据正文和差异化视觉角色生成三张配套图 |
| **Doubao Seedream 4.5** | 默认图片模型，可通过 `IMAGE_MODEL` 替换 |

### 可观测性与交付

| 技术 | 用途 |
| --- | --- |
| **Structlog** | 结构化日志、请求链路与节点耗时记录 |
| **PII 脱敏处理器** | 对日志中的邮箱、手机号和密钥等信息进行脱敏 |
| **ZIP / Markdown 导出** | 一键导出标题、文案、标签、配图与发布清单 |

## 快速开始

### 1. 环境准备

确保本地已安装并运行 PostgreSQL：

```bash
# Windows - 确认 PostgreSQL 服务运行
# 可以在服务管理器中查看 postgresql 服务状态

# 创建数据库
psql -U postgres -c "CREATE DATABASE aicontent;"
```

### 2. 安装依赖

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `.env` 文件，修改数据库连接信息：

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/aicontent
POSTGRES_URI=postgresql://postgres:your_password@localhost:5432/aicontent
```

### 4. 启动服务

```bash
# 方式 1: 使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 直接运行
python -m app.main
```

### 5. 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

## API 接口

### 启动工作流

```bash
POST /api/v1/workflow/start
Content-Type: application/json

{
    "topic_direction": "AI技术"
}
```

**响应示例:**

```json
{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "topics_generated",
    "generated_topics": [
        "LangGraph入门：构建你的第一个AI工作流 - AI技术方向",
        "AI Agent实战：从零搭建智能助手 - AI技术方向",
        "Python高并发编程：asyncio深度解析 - AI技术方向"
    ],
    "message": "工作流已启动，请选择一个选题继续"
}
```

### 获取工作流状态

```bash
GET /api/v1/workflow/state/{thread_id}
```

### 恢复工作流 - 选择选题

```bash
POST /api/v1/workflow/resume/{thread_id}
Content-Type: application/json

{
    "action": "select_topic",
    "data": {
        "selected_topic": "LangGraph入门：构建你的第一个AI工作流"
    }
}
```

### 恢复工作流 - 审核通过

```bash
POST /api/v1/workflow/resume/{thread_id}
Content-Type: application/json

{
    "action": "approve"
}
```

### 恢复工作流 - 审核驳回

```bash
POST /api/v1/workflow/resume/{thread_id}
Content-Type: application/json

{
    "action": "reject",
    "data": {
        "feedback": "请增加更多实际代码示例"
    }
}
```

## 工作流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         START                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     plan_topics                                  │
│                  (AI 生成 3-5 个选题)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              ⏸️ INTERRUPT: human_select_topic                    │
│                    (等待人工选题)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      write_draft                                 │
│                  (AI 根据选题写长文)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              ⏸️ INTERRUPT: human_review                          │
│                    (等待人工审稿)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
         [approved]                      [rejected]
              │                               │
              ▼                               │
┌─────────────────────────┐                   │
│    extract_visuals      │                   │
│    (提炼图片要点)        │                   │
└─────────────────────────┘                   │
              │                               │
              ▼                               │
┌─────────────────────────┐                   │
│    generate_images      │                   │
│    (生成配图)           │                   │
└─────────────────────────┘                   │
              │                               │
              ▼                               │
┌─────────────────────────┐                   │
│          END            │◀──────────────────┘
│       (工作流完成)       │    (回到 write_draft 重写)
└─────────────────────────┘
```

## 项目结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── workflow.py      # 核心 API 接口
│   ├── core/
│   │   ├── config.py            # 配置管理
│   │   └── db.py                # 数据库连接
│   ├── graph/
│   │   ├── nodes/               # LangGraph 节点
│   │   │   ├── planner.py       # 选题规划
│   │   │   ├── writer.py        # 文章撰写
│   │   │   ├── visualizer.py    # 视觉内容
│   │   │   └── human.py         # 人工介入
│   │   ├── state.py             # 状态定义
│   │   ├── workflow.py          # 工作流组装
│   │   └── utils.py             # 工具函数
│   ├── services/
│   │   ├── llm_service.py       # LLM 服务 (火山引擎 Doubao)
│   │   └── image_service.py     # 图片生成服务
│   └── main.py                  # 应用入口
├── scripts/
│   └── init_db.sql              # 数据库初始化脚本
├── requirements.txt
├── .env
└── README.md
```

## 注意事项

1. **数据库连接**: 确保 PostgreSQL 服务运行且可访问
2. **LLM 配置**: 在 `.env` 中配置火山引擎 Doubao API Key
3. **状态持久化**: LangGraph Checkpointer 会自动创建所需表结构

## License

MIT
