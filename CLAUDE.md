# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AG-UI 旅行规划助手演示。基于 Microsoft Agent Framework 和 AG-UI 协议的前后端实时通信演示，展示 SSE 事件流和"人在回路"（Human-in-the-Loop）交互。

- **Backend**: FastAPI + Microsoft Agent Framework (`AgentFrameworkAgent`)
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS v4
- **Communication**: AG-UI protocol over Server-Sent Events (SSE)

## Common Commands

### Backend

```bash
cd backend
# 安装依赖（使用 uv 或 pip）
uv sync
# 或: pip install -e .

# 启动开发服务器（默认端口 8000）
.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

后端入口：`backend/src/main.py`，通过 `add_agent_framework_fastapi_endpoint(app, agent, path="/api/agent")` 注册 AG-UI 端点。

### Frontend

```bash
cd frontend
# 安装依赖
npm install

# 启动开发服务器（默认端口 5173，带代理）
npm run dev

# 构建
npm run build
```

Vite 开发服务器代理配置：`/api/agent` → `http://127.0.0.1:8000`。

## Environment

后端需要 `.env` 文件（位于 `backend/` 目录）：

```
DEEPSEEK_API_KEY=<key>
DEEPSEEK_MODEL=deepseek-v4-flash
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

依赖管理：
- 后端：`backend/pyproject.toml`（requires Python >= 3.12）
- 前端：`frontend/package.json`

## High-Level Architecture

### Backend Agent Setup

`backend/src/workflow.py` 中的 `create_travel_workflow()` 是核心：

1. `Agent`（来自 `agent_framework`）定义 LLM agent、工具列表和指令
2. `AgentFrameworkAgent` 包装上述 Agent，启用 AG-UI 协议事件（`STATE_SNAPSHOT`、`STATE_DELTA` 等）
3. `_build_instructions()` 动态注入当前日期到系统提示词，使 LLM 能正确解析"明天"、"后天"等相对日期

工具定义在 `backend/src/tools.py`，`book_flight` 使用 `@tool(approval_mode="always_require")` 触发人在回路中断。

LLM 客户端配置在 `backend/src/agents.py`，使用 DeepSeek API（OpenAI 兼容格式）。

### Frontend Event Handling

`frontend/src/components/TravelPlanner.tsx` 处理完整的 AG-UI SSE 事件流：

- 解析 SSE → `parseSSEEvent()` → 按 `event.type` 分发处理
- 关键事件：`RUN_STARTED`、`TEXT_MESSAGE_CONTENT`、`TOOL_CALL_START/ARGS/END/RESULT`、`STATE_SNAPSHOT`、`RUN_FINISHED`（携带 `interrupt`）、`INTERRUPT`

### Critical: Human-in-the-Loop Resume Flow

当 `book_flight` 触发中断时，后端在 `RUN_FINISHED` 中返回 `interrupt` 数组。用户点击"确认"后，前端必须构造 resume payload 并**补充 assistant 的 `tool_calls` 消息**，否则后端 `_find_matching_func_call()` 无法匹配 approval 与原始函数调用，导致工具不被执行、Agent 重新调用工具的死循环。

这是跨前后端的关键约束，实现见 `TravelPlanner.tsx` 中 `resumeToolCalls` 的构造逻辑：

```typescript
// resume 时必须补充 assistant tool_calls，否则后端无法匹配 approval
const resumeToolCalls = [];
for (const interrupt of interrupts) {
  const fn = interrupt?.value?.function_call;
  if (fn?.call_id) {
    resumeToolCalls.push({
      role: "assistant",
      tool_calls: [{
        id: fn.call_id,
        type: "function",
        function: { name: fn.name, arguments: JSON.stringify(fn.arguments) }
      }]
    });
  }
}
const allMessages = [...messages, ...resumeToolCalls];
```

### State Synchronization

- 后端 `AgentFrameworkAgent` 的 `state_schema` 定义了 `itinerary`（行程对象）和 `tools_called`（工具列表）
- 状态变化通过 `STATE_SNAPSHOT` 事件推送到前端
- 前端用 `itinerary` state 驱动 `ItineraryCard` 组件显示天气、酒店、景点、航班信息

### Message Flow (Human-in-the-Loop)

```
User: "帮我订机票..."
  → Agent 调用 book_flight → approval_mode="always_require" 触发中断
  → 后端发送 RUN_FINISHED + interrupt（含 function_call 详情）
  → 前端渲染 InterruptPanel，等待用户确认

User 点击确认
  → 前端构造 resume payload + 补充 assistant tool_calls 消息
  → 发送 POST /api/agent
  → 后端 _resolve_approval_responses() 执行工具，获取结果
  → Agent 重新运行，看到 tool result，生成最终回复
  → 前端收到 TEXT_MESSAGE_CONTENT + TOOL_CALL_RESULT + RUN_FINISHED（无 interrupt）
```

## File Responsibilities

- `backend/src/main.py` — FastAPI 应用创建、CORS、AG-UI 端点注册
- `backend/src/workflow.py` — Agent 组装、指令构建、状态 schema 定义
- `backend/src/tools.py` — 工具函数（天气、酒店、景点、航班）及 approval 配置
- `backend/src/agents.py` — LLM 客户端和未使用的多 Agent 定义（triage/weather/hotel/summary）
- `frontend/src/components/TravelPlanner.tsx` — 核心组件：SSE 连接、事件分发、消息管理、中断处理
- `frontend/src/types.ts` — TypeScript 类型定义
