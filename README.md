# AG-UI 旅行规划助手演示

本项目是一个基于 Microsoft Agent Framework 和 AG-UI 协议的旅行规划 Agent 演示应用，展示了前后端如何通过标准化事件流进行实时通信，以及"人在回路"（Human-in-the-Loop）的完整实现。

---

## 项目结构

```
.
├── backend/          # FastAPI + Agent Framework 后端
│   └── src/
│       ├── main.py         # FastAPI 应用入口
│       ├── workflow.py     # Agent 工作流定义
│       ├── tools.py        # 工具函数（天气、酒店、景点、航班）
│       └── agents.py       # Agent 配置
├── frontend/         # React + TypeScript 前端
│   └── src/
│       ├── components/
│       │   ├── TravelPlanner.tsx   # 主组件（事件处理核心）
│       │   ├── InterruptPanel.tsx  # 人在回路中断面板
│       │   ├── ChatPanel.tsx       # 聊天界面
│       │   ├── ItineraryCard.tsx   # 行程信息卡片
│       │   ├── AgentStatus.tsx     # Agent 状态栏
│       │   └── EventLog.tsx        # AG-UI 事件流日志
│       └── types.ts                # TypeScript 类型定义
└── README.md
```

---

## AG-UI 通信过程详解

### 一、通信总览

AG-UI（Agent-UI）是 Microsoft Agent Framework 提供的一套**事件驱动协议**，用于前端与 Agent 后端之间的实时双向通信：

- **传输层**：基于 HTTP SSE（Server-Sent Events），后端流式推送事件
- **协议层**：标准化的事件类型（`RUN_STARTED`、`TEXT_MESSAGE_CONTENT`、`TOOL_CALL_START` 等）
- **状态同步**：前后端通过事件保持对话状态、工具调用状态、应用状态的一致

```
┌─────────────┐     POST /api/agent      ┌─────────────┐
│   前端 UI   │ ───────────────────────> │  FastAPI    │
│  (React)    │   {messages, threadId}   │   后端      │
│             │                          │             │
│             │ <─────────────────────── │ AgentFrameworkAgent
│             │    SSE Event Stream      │             │
│             │   RUN_STARTED            │             │
│             │   TEXT_MESSAGE_CONTENT   │             │
│             │   TOOL_CALL_START        │             │
│             │   TOOL_CALL_RESULT       │             │
│             │   RUN_FINISHED           │             │
└─────────────┘                          └─────────────┘
```

### 二、前端：请求发起与事件消费

#### 2.1 发送请求

前端通过标准 `fetch` 发送 POST 请求，请求体包含对话历史和线程 ID：

```typescript
const res = await fetch("/api/agent", {
  method: "POST",
  headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
  body: JSON.stringify({
    threadId: "travel-demo-thread",
    messages: allMessages,
    ...(resumePayload || {}),  // 人在回路恢复时使用
  }),
});
```

**关键点**：
- `Accept: text/event-stream` 表明前端期望 SSE 响应
- `messages` 是对话历史，格式为 AG-UI 标准消息对象数组
- `resumePayload` 用于"人在回路"恢复流程

#### 2.2 解析 SSE 事件流

SSE 数据格式为 `data: {"type":"TEXT_MESSAGE_CONTENT", ...}`，前端逐行解析 JSON：

```typescript
function parseSSEEvent(line: string): SSEEvent | null {
  if (!line.startsWith("data: ")) return null;
  try {
    return JSON.parse(line.slice(6));
  } catch {
    return null;
  }
}
```

#### 2.3 事件分发处理

前端通过 `switch (event.type)` 处理不同事件：

| 事件类型 | 作用 | 前端响应 |
|---------|------|---------|
| `RUN_STARTED` | 新一次 Agent 运行开始 | 重置状态，清空待处理工具调用 |
| `TEXT_MESSAGE_START` | Assistant 开始输出文本 | 创建新消息 ID |
| `TEXT_MESSAGE_CONTENT` | 文本增量（流式） | 追加到 `currentResponse` |
| `TEXT_MESSAGE_END` | 文本输出结束 | 将完整文本加入 `messages` |
| `TOOL_CALL_START` | Agent 发起工具调用 | 显示工具调用状态 |
| `TOOL_CALL_ARGS` | 工具参数增量 | 累积显示参数 |
| `TOOL_CALL_END` | 工具调用声明结束 | 标记工具调用已结束 |
| `TOOL_CALL_RESULT` | 工具执行结果返回 | 更新行程信息（天气/酒店/航班） |
| `STATE_SNAPSHOT` | 状态快照 | 更新 `itinerary` |
| `RUN_FINISHED` | 本次运行结束 | 检查是否有 `interrupt` |
| `RUN_ERROR` | 运行出错 | 显示错误状态 |

### 三、后端：Agent 执行与事件生成

#### 3.1 端点注册

后端使用 `add_agent_framework_fastapi_endpoint` 注册 AG-UI 端点：

```python
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint

travel_agent = create_travel_workflow()

add_agent_framework_fastapi_endpoint(
    app=app,
    agent=travel_agent,
    path="/api/agent",
)
```

该函数负责：
1. 接收前端的 POST 请求
2. 解析 AG-UI 格式的消息
3. 调用 Agent 执行
4. 将 Agent 输出转换为 AG-UI 事件流返回

#### 3.2 Agent 定义

```python
def create_travel_workflow():
    travel_agent = Agent(
        id="travel_agent",
        name="travel_agent",
        instructions=_build_instructions(),  # 动态注入当前日期
        client=chat_client,
        tools=[get_weather, search_hotels, search_attractions, book_flight],
    )
    return AgentFrameworkAgent(
        agent=travel_agent,
        name="TravelPlanner",
        description="旅行规划 Agent 工作流演示",
        state_schema={
            "itinerary": {"type": "object", "description": "当前行程信息"},
            "tools_called": {"type": "array", "description": "已调用的工具列表"},
        },
    )
```

`AgentFrameworkAgent` 是 AG-UI 的包装器，它将底层 Agent 的执行过程转换为 AG-UI 标准事件，并管理 `STATE_SNAPSHOT` / `STATE_DELTA` 以及工具调用的中断/恢复逻辑。

#### 3.3 工具定义与审批模式

```python
@tool(approval_mode="always_require")
def book_flight(departure: str, arrival: str, date: str, passenger_name: str) -> dict:
    """预订航班（需要用户确认）。"""
    ...
```

`approval_mode="always_require"` 是触发"人在回路"的关键。当 Agent 调用此工具时，框架不会立即执行函数，而是生成一个 `function_approval_request`，等待用户确认。

#### 3.4 后端事件生成流程

后端事件生成的简化流程：

```
1. 解析请求（thread_id, messages, resume）
2. 处理 resume（人在回路恢复）
   - _extract_resume_payload() 提取 resume
   - _resume_to_tool_messages() 转换为 tool 消息
3. 转换消息格式（AG-UI -> Agent Framework）
4. 执行 approved 的工具调用
   - _resolve_approval_responses()
5. 流式运行 Agent
   - yield RunStartedEvent
   - for update in agent.run(stream=True):
       for content in update.contents:
           yield _emit_content(content)  # TEXT_MESSAGE_CONTENT, TOOL_CALL_START, etc.
       if waiting_for_approval:
           break  # 中断，等待用户确认
   - yield RunFinishedEvent(interrupts=...)
```

### 四、人在回路（Human-in-the-Loop）完整流程

这是前后端配合最复杂的场景，以 `book_flight` 为例：

#### 4.1 首次调用 -> 中断

```
前端: "帮我订机票，北京到上海，明天，余心刀"
  |
后端: Agent 解析意图，调用 book_flight(departure="北京", arrival="上海",
     date="2026-05-22", passenger_name="余心刀")
  |
框架: approval_mode="always_require" -> 不执行函数，生成 function_approval_request
  |
AG-UI: 将 approval request 转换为 INTERRUPT 事件，附加到 RUN_FINISHED
  |
前端: 收到 RUN_FINISHED，检测到 event.interrupt 非空
  |
前端: 渲染 InterruptPanel，显示航班信息，等待用户点击"确认"或"拒绝"
```

#### 4.2 用户确认 -> 恢复

```
前端: 用户点击"确认执行"
  |
前端: 构造 resume payload
      {
        "resume": {
          "interrupts": [{
            "id": "call_xxx",
            "value": {
              "accepted": true,
              "function_call": {
                "call_id": "call_xxx",
                "name": "book_flight",
                "arguments": {...}
              }
            }
          }]
        }
      }
  |
前端: 发送 POST /api/agent，messages 包含完整历史 + assistant tool_call
  |
后端: _extract_resume_payload() -> 提取 resume
  |
后端: _resume_to_tool_messages() -> 转换为 role="tool" 的 AG-UI 消息
  |
后端: _resolve_approval_responses() -> 执行 approved 的工具调用，获取结果
  |
后端: Agent 重新运行，看到 tool result，生成最终回复
  |
前端: 收到 TEXT_MESSAGE_CONTENT + TOOL_CALL_RESULT + RUN_FINISHED（无 interrupt）
  |
前端: 更新行程卡片，显示航班信息
```

#### 4.4 关键实现要点

**Resume 时补充 assistant tool_call**

前端 resume 时必须在 messages 数组中包含对应的 assistant `tool_calls`，否则后端无法将 approval response 与之前的 function call 匹配，会导致工具未被执行、Agent 重新调用工具的死循环。

```typescript
// 从 resume payload 提取 function_call，补充 assistant tool_call 消息
const resumeToolCalls = [];
if (resumePayload) {
  const interrupts = resumePayload.resume?.interrupts || [];
  for (const interrupt of interrupts) {
    const fn = interrupt?.value?.function_call;
    if (fn?.call_id) {
      resumeToolCalls.push({
        role: "assistant",
        tool_calls: [{
          id: fn.call_id,
          type: "function",
          function: {
            name: fn.name,
            arguments: JSON.stringify(fn.arguments),
          }
        }]
      });
    }
  }
}

const allMessages = resumePayload
  ? [...messages, ...resumeToolCalls]  // 包含 tool_calls 的完整历史
  : [...messages, userMsg];
```

### 五、状态同步机制

#### 5.1 应用状态（State）

后端 `AgentFrameworkAgent` 定义了 `state_schema`：

```python
state_schema={
    "itinerary": {"type": "object", "description": "当前行程信息"},
    "tools_called": {"type": "array", "description": "已调用的工具列表"},
}
```

当 Agent 运行时，状态变化通过 `STATE_SNAPSHOT` 事件推送到前端。

#### 5.2 对话状态（Messages）

前后端通过消息数组保持对话上下文：
- 前端维护 `messages` state（文本消息）
- 后端通过 `MessagesSnapshotEvent` 发送完整消息快照（包含 tool_calls 和 tool results）
- resume 时前端需要发送完整历史，否则后端会丢失上下文

#### 5.3 工具调用状态

前端使用 `openToolCalls` Map 跟踪未完成的工具调用：

```typescript
const openToolCalls = new Map<string, string>(); // callId -> toolName
```

- `TOOL_CALL_START` 时添加
- `TOOL_CALL_RESULT` 时移除
- 用于正确关联工具结果与工具名称（更新对应的行程信息）

### 六、前后端职责划分

| 职责 | 前端 (React) | 后端 (FastAPI + Agent Framework) |
|-----|-------------|--------------------------------|
| **UI 渲染** | 聊天消息、工具状态、中断面板、行程卡片 | -- |
| **事件消费** | 解析 SSE，按事件类型更新 state | -- |
| **事件生成** | -- | Agent 执行过程中实时生成 AG-UI 事件 |
| **消息格式** | AG-UI 标准消息（role/content/tool_calls） | 与 LLM 提供商的消息格式转换 |
| **工具执行** | -- | 实际调用 Python 函数，返回结果 |
| **审批控制** | 显示中断面板，收集用户确认/拒绝 | `approval_mode` 控制是否中断 |
| **Resume 处理** | 构造 resume payload，发送完整历史 | `_resolve_approval_responses` 执行 approved 工具 |
| **状态管理** | 接收 `STATE_SNAPSHOT` 更新 UI | `state_schema` 定义，预测性状态更新 |

---

## 启动方式

### 后端

```bash
cd backend
.venv/Scripts/python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

### 前端

```bash
cd frontend
npm run dev
```

---

## 技术栈

- **后端**：Python 3.12 + FastAPI + Microsoft Agent Framework + Agent Framework AG-UI
- **前端**：React 19 + TypeScript + Vite + Tailwind CSS
- **通信协议**：AG-UI over Server-Sent Events (SSE)
