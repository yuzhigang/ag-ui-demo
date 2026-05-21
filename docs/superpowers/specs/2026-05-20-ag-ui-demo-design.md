# AG-UI Demo: 旅行规划多 Agent 助手

## 概述

一个前后端结合的演示程序，展示 Microsoft Agent Framework (MAF) 的多 Agent 工作流能力以及 AG-UI 协议的实时流式通信特性。

**核心目标：**
1. 演示 MAF 框架的 Handoff 多 Agent 工作流
2. 演示 AG-UI 协议的前后端实时通信

---

## 技术栈

| 层面 | 技术 |
|------|------|
| Python 管理 | uv |
| 后端框架 | FastAPI + Microsoft Agent Framework |
| LLM API | DeepSeek v4 (OpenAI-compatible API) |
| 多 Agent | MAF HandoffBuilder |
| 通信协议 | AG-UI over Server-Sent Events (SSE) |
| 前端框架 | React 18 + TypeScript + Vite |
| UI 组件 | CopilotKit React |
| 样式 | Tailwind CSS |

---

## 项目结构

```
backend/
├── pyproject.toml
├── uv.lock
├── .env
└── src/
    ├── __init__.py
    ├── main.py             # FastAPI 入口 + AG-UI 端点
    ├── workflow.py         # MAF 多 Agent 工作流定义
    ├── tools.py            # 工具函数
    └── agents.py           # Agent 定义 + DeepSeek 客户端

frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── .env
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── TravelPlanner.tsx
    │   ├── ChatPanel.tsx
    │   ├── AgentStatus.tsx   # 显示思考/工具调用状态
    │   └── ItineraryCard.tsx
    └── styles/
        └── index.css
```

---

## 场景设计：旅行规划助手

### Agent 职责

| Agent | 职责 | 工具 | 转交条件 |
|-------|------|------|----------|
| **Triage Agent** | 理解用户意图，决定下一步 | 无 | 提到天气→天气 Agent；提到酒店→酒店 Agent；信息收集完毕→总结 Agent |
| **Weather Agent** | 查询目的地天气 | `get_weather(city, date)` | 完成→Triage Agent |
| **Hotel Agent** | 搜索推荐酒店 | `search_hotels(city, check_in, check_out, budget)` | 完成→Triage Agent |
| **Summary Agent** | 整合信息生成旅行计划 | 无 | 完成→结束 |

### 示例对话流

```
用户: "我想去三亚，5月25日到28日，帮我查下天气和酒店"
  → Triage Agent → Weather Agent
Weather Agent: 调用 get_weather("三亚", "2026-05-25")
  → 返回天气信息 → Triage Agent
Triage Agent → Hotel Agent
Hotel Agent: 调用 search_hotels("三亚", "2026-05-25", "2026-05-28", "中等预算")
  → 返回酒店列表 → Triage Agent
Triage Agent → Summary Agent
Summary Agent: 生成完整旅行计划
  → 完成
```

---

## 后端设计

### Python 依赖安装

```bash
# pyproject.toml 依赖
# agent-framework (包含 core + ag_ui)
# fastapi, uvicorn, python-dotenv, openai
```

### DeepSeek 客户端配置

使用 MAF 的 `OpenAIChatClient` 适配 DeepSeek API（OpenAI-compatible）：

```python
from agent_framework.openai import OpenAIChatClient

chat_client = OpenAIChatClient(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
)
```

### Agent 定义

使用 MAF 的 `Agent` 类定义各 Agent：

```python
from agent_framework import Agent

triage = Agent(
    id="triage_agent",
    name="triage_agent",
    instructions=(
        "你是旅行规划助手的调度员。\n"
        "1. 理解用户想去的目的地和日期范围。\n"
        "2. 如果用户提到天气或想了解目的地天气，转交给 weather_agent。\n"
        "3. 如果用户提到酒店、住宿，转交给 hotel_agent。\n"
        "4. 如果天气和酒店信息都已收集完毕，转交给 summary_agent 生成旅行计划。\n"
        "5. 不要重复询问已经确认的信息。"
    ),
    client=chat_client,
    require_per_service_call_history_persistence=True,
)

weather = Agent(
    id="weather_agent",
    name="weather_agent",
    instructions=(
        "你是天气查询专家。\n"
        "1. 从用户对话中提取目的地城市和日期。\n"
        "2. 调用 get_weather(city, date) 查询天气。\n"
        "3. 返回天气结果后，将对话交回 triage_agent。"
    ),
    client=chat_client,
    tools=[get_weather],
    require_per_service_call_history_persistence=True,
)

hotel = Agent(
    id="hotel_agent",
    name="hotel_agent",
    instructions=(
        "你是酒店推荐专家。\n"
        "1. 从用户对话中提取目的地、入住日期、退房日期和预算等级。\n"
        "2. 调用 search_hotels(city, check_in, check_out, budget) 搜索酒店。\n"
        "3. 向用户展示推荐酒店，然后交回 triage_agent。"
    ),
    client=chat_client,
    tools=[search_hotels],
    require_per_service_call_history_persistence=True,
)

summary = Agent(
    id="summary_agent",
    name="summary_agent",
    instructions=(
        "你是旅行计划整合专家。\n"
        "1. 根据已收集的天气信息和酒店信息，生成完整的旅行计划。\n"
        "2. 计划应包含：目的地、日期、天气情况、推荐酒店。\n"
        "3. 以友好的方式呈现计划，然后结束对话。"
    ),
    client=chat_client,
    require_per_service_call_history_persistence=True,
)
```

### HandoffBuilder 工作流

使用 `HandoffBuilder` 定义 Agent 转交拓扑：

```python
from agent_framework.orchestrations import HandoffBuilder
from agent_framework import Message

def _termination_condition(conversation: list[Message]) -> bool:
    """当 Summary Agent 输出结束标记时终止工作流。"""
    for message in reversed(conversation):
        if message.role != "assistant":
            continue
        if "旅行计划已生成" in (message.text or ""):
            return True
    return False

def create_travel_workflow():
    builder = HandoffBuilder(
        name="travel_planner_workflow",
        participants=[triage, weather, hotel, summary],
        termination_condition=_termination_condition,
    )
    (
        builder
        .add_handoff(triage, [weather], description="用户需要查询天气")
        .add_handoff(triage, [hotel], description="用户需要查询酒店")
        .add_handoff(triage, [summary], description="信息收集完毕，生成旅行计划")
        .add_handoff(weather, [triage], description="天气查询完成，返回调度")
        .add_handoff(hotel, [triage], description="酒店查询完成，返回调度")
        .add_handoff(summary, [triage], description="计划生成完毕")
    )
    return builder.with_start_agent(triage).build()
```

### AG-UI 端点暴露

使用 `AgentFrameworkWorkflow` 包装工作流，并通过 `add_agent_framework_fastapi_endpoint` 暴露：

```python
from agent_framework.ag_ui import AgentFrameworkWorkflow, add_agent_framework_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="旅行规划 AG-UI Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

travel_workflow = AgentFrameworkWorkflow(
    workflow_factory=lambda _thread_id: create_travel_workflow(),
    name="travel_planner_workflow",
    description="旅行规划多 Agent 工作流演示",
)

add_agent_framework_fastapi_endpoint(
    app=app,
    agent=travel_workflow,
    path="/api/agent",
)
```

### 工具实现

**`get_weather(city: str, date: str) -> dict`**
- 模拟天气查询（返回模拟数据，避免真实 API 依赖）
- 返回：`{"city": "三亚", "date": "2026-05-25", "weather": "晴朗", "temperature": "28°C", "humidity": "65%"}`

**`search_hotels(city: str, check_in: str, check_out: str, budget: str) -> list`**
- 模拟酒店搜索
- `budget` 参数为枚举值："经济型" | "中等预算" | "豪华"
- 返回：`[{"name": "三亚湾假日酒店", "price": "¥580/晚", "rating": 4.6, "location": "三亚湾"}]`

---

## 前端设计

### 架构

前端为纯 React 应用，通过 `@ag-ui/client` 的 `HttpAgent` **直接连接**后端 SSE 端点，不需要额外的 CopilotKit Runtime 服务。

```
React + Vite (port 5173) ──SSE──► FastAPI AG-UI (port 8000)
```

**Vite 代理配置**：
```typescript
// vite.config.ts
export default {
  server: {
    proxy: {
      "/api/agent": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
};
```

**前端连接**：
```typescript
import { HttpAgent } from "@ag-ui/client";

const agent = new HttpAgent({ url: "/api/agent" });
```

### 组件设计

**TravelPlanner**
- 主布局容器
- 管理 `HttpAgent` 连接和 AG-UI 事件流状态
- 维护消息列表、系统状态、行程数据

**AgentStatus**
- 显示当前系统状态（思考中 / 调用工具 / 等待输入）
- 基于 AG-UI 事件流的状态推断：
  - `RUN_STARTED` → "思考中..."
  - `TOOL_CALL_START` → "正在查询...（工具名）"
  - `TOOL_CALL_RESULT` → "已获取结果"
  - `RUN_FINISHED` → 清空状态
- 由于 AG-UI 协议不携带 Agent 身份信息，不显示具体 Agent 名称

**ItineraryCard**
- 展示已收集的旅行信息
- 天气信息、酒店信息实时更新
- 通过解析 `TOOL_CALL_RESULT` 事件中的结果数据来更新

**ChatPanel**
- 消息列表（用户/助手）
- 输入框和发送按钮
- 流式消息显示（手动处理 `TEXT_MESSAGE_CONTENT` 事件拼接）

### AG-UI 事件 → UI 映射

| AG-UI Event | UI 表现 |
|-------------|---------|
| `RUN_STARTED` | AgentStatus 显示"思考中..." |
| `TEXT_MESSAGE_START` | ChatPanel 开始显示新消息气泡 |
| `TEXT_MESSAGE_CONTENT` | ChatPanel 流式追加文字 |
| `TOOL_CALL_START` | AgentStatus 显示"正在查询...（工具名）" |
| `TOOL_CALL_RESULT` | ItineraryCard 更新对应信息 |
| `RUN_FINISHED` | AgentStatus 清空状态 |

---

## 数据流

```
用户输入
    │
    ▼
┌─────────────┐    POST/SSE    ┌─────────────┐
│  React      │ ─────────────► │  FastAPI    │
│  (Vite)     │   AG-UI        │   (MAF)     │
│  (port 5173)│   /travel-     │  (port 8000)│
└─────────────┘   agent        └──────┬──────┘
    ▲                                 │
    │                                 ▼
    │  AG-UI Events (SSE)       ┌──────────┐
    │  ├─ RUN_STARTED           │  Triage  │
    │  ├─ TEXT_MESSAGE_CONTENT  │  Agent   │
    │  ├─ TOOL_CALL_START       └────┬─────┘
    │  ├─ TOOL_CALL_RESULT           │
    │  └─ RUN_FINISHED               ▼
    └────────────────────────── ┌──────────┐
                                │ Weather/ │
                                │ Hotel    │
                                │ Agent    │
                                └──────────┘
```

---

## 配置

### 后端环境变量 (backend/.env)

```bash
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 前端环境变量 (frontend/.env)

```bash
VITE_AGENT_URL=/api/agent
```

---

## 运行方式

### 后端

```bash
cd backend
uv sync
uv run python src/main.py
# 服务启动于 http://localhost:8000
# AG-UI 端点: POST /api/agent
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 服务启动于 http://localhost:5173
# Vite 代理 /api/agent → http://localhost:8000
```

---

## 依赖

### Python (pyproject.toml)

- `fastapi`
- `uvicorn`
- `agent-framework` (MAF 主包，包含 ag_ui)
- `python-dotenv`
- `openai` (DeepSeek 使用 OpenAI-compatible API)

### Node (package.json)

- `react`
- `react-dom`
- `typescript`
- `vite`
- `@ag-ui/client`
- `tailwindcss`

---

## 验收标准

1. [ ] 后端能正常启动，FastAPI 文档页面 (`/docs`) 可访问
2. [ ] AG-UI 端点 `/api/agent` 能正确响应 SSE 请求
3. [ ] DeepSeek API 调用正常，流式返回内容
4. [ ] 多 Agent Handoff 工作流能按预期切换 Agent（Triage → Weather/Hotel → Summary）
5. [ ] 工具调用能正确执行并返回模拟数据
6. [ ] 前端能正常启动，通过 `@ag-ui/client` 连接后端并发送消息
7. [ ] 聊天消息能实时流式显示
8. [ ] AgentStatus 能正确显示系统状态（思考中 / 调用工具 / 等待输入）
9. [ ] ItineraryCard 能随工具调用结果更新
10. [ ] 完整对话示例能成功运行（三亚 5/25-5/28 天气+酒店查询）
