# 生成式 UI 组件渲染与 E2E 测试链路设计

> **目标**：设计一套可扩展的前端组件渲染框架，使后端 Agent 能通过标准 AG-UI 协议动态控制前端 UI 组件渲染，并建立完整的 E2E 测试链路验证该能力。

**技术栈**：React 18 + TypeScript + Vite + Playwright (E2E) + AG-UI Protocol

---

## 1. 背景与问题

当前前端 `TravelPlanner.tsx` 通过硬编码的 `if/else` 将 `TOOL_CALL_RESULT` 映射到 `itinerary` state，驱动 `ItineraryCard` 渲染：

```typescript
// 当前硬编码映射——每新增工具需改前端
if (toolName === "get_weather") setItinerary(prev => ({...prev, weather: result}));
else if (toolName === "search_hotels") setItinerary(prev => ({...prev, hotels: result}));
// ... 持续增长
```

**问题**：
1. 工具与 UI 强耦合，新增工具必须修改前端代码
2. 无法支持非工具调用场景的 UI 渲染（如进度条、确认面板）
3. 无法支持自定义业务组件的动态接入

---

## 2. 架构设计

### 2.1 核心原则

- **职责分离**：工具只返回数据，`CUSTOM` 事件负责渲染指令
- **注册表模式**：组件通过 ID 注册，前端与后端通过组件 ID 解耦
- **向后兼容**：现有 `STATE_SNAPSHOT` → `ItineraryCard` 链路保留

### 2.2 架构图

```
AG-UI SSE 事件流
    │
    ├── TOOL_CALL_RESULT ──▶ 更新内部 state ──▶ ItineraryCard (向后兼容)
    │
    ├── STATE_SNAPSHOT ──▶ 同步 itinerary state ──▶ ItineraryCard (向后兼容)
    │
    └── CUSTOM (name="render_component") ──▶ ComponentRegistry
                                                │
                                                ├── 查找组件 ID
                                                │
                                                └── 渲染 React 组件
```

### 2.3 新增模块

| 模块 | 职责 | 文件路径 |
|------|------|----------|
| `ComponentRegistry` | 维护 `componentId → React.FC` 映射，支持注册/注销/查找 | `src/components/registry/ComponentRegistry.ts` |
| `AGUIRenderer` | 接收 AG-UI 事件流，提取 `render_component` 事件，调用注册表 | `src/components/AGUIRenderer.tsx` |
| 内置组件包 | 将 `ItineraryCard` 拆分为独立可注册组件 | `src/components/registry/built-in/*.tsx` |

---

## 3. AG-UI 协议：CUSTOM 渲染事件

### 3.1 事件格式

后端通过 `CUSTOM` 事件发送渲染指令：

```typescript
interface RenderComponentEvent {
  type: "CUSTOM";
  name: "render_component";
  value: {
    component?: string;                   // 组件 ID，mount/update 时必须存在；unmount 时可省略
    props?: Record<string, unknown>;      // 传递给组件的 props，unmount 时可省略
    key?: string;                         // React key，用于更新/卸载已有组件
    action?: "mount" | "update" | "unmount";  // 默认 "mount"
  };
}
```

### 3.2 事件示例

**渲染天气卡片**：
```json
{
  "type": "CUSTOM",
  "name": "render_component",
  "value": {
    "component": "WeatherCard",
    "props": { "city": "北京", "temperature": "28°C", "weather": "晴朗" },
    "key": "weather-1"
  }
}
```

**更新已有组件**：
```json
{
  "type": "CUSTOM",
  "name": "render_component",
  "value": {
    "component": "ProgressBar",
    "props": { "step": 2, "total": 4 },
    "key": "progress-1",
    "action": "update"
  }
}
```

**卸载组件**：
```json
{
  "type": "CUSTOM",
  "name": "render_component",
  "value": {
    "key": "weather-1",
    "action": "unmount"
  }
}
```

### 3.3 渲染规则

| action | 行为 |
|--------|------|
| `mount` (默认) | 将组件加入渲染列表。如 key 已存在，则更新该组件的 props |
| `update` | 查找相同 key 的组件，更新其 props。如不存在，等价于 mount |
| `unmount` | 从渲染列表移除指定 key 的组件 |
| `RUN_STARTED` | 清空渲染列表（新对话轮次） |

---

## 4. 组件注册机制

### 4.1 注册表 API

```typescript
// src/components/registry/ComponentRegistry.ts
class ComponentRegistry {
  private static instance: ComponentRegistry;
  private components = new Map<string, React.FC<any>>();

  static getInstance(): ComponentRegistry;

  register(id: string, component: React.FC<any>): void;
  unregister(id: string): void;
  resolve(id: string): React.FC<any> | undefined;
  list(): string[];
}

// 全局便捷函数
export function registerComponent(id: string, component: React.FC<any>): void;
```

### 4.2 自定义组件接入示例

业务方在任意位置注册组件：

```typescript
// MyBusinessComponent.tsx
import { registerComponent } from "../registry/ComponentRegistry";

function FlightComparisonTable({ flights }: { flights: Flight[] }) {
  return (
    <table>
      <thead>...</thead>
      <tbody>{flights.map(f => <tr>...</tr>)}</tbody>
    </table>
  );
}

// 注册（可在应用入口或组件文件内）
registerComponent("FlightComparisonTable", FlightComparisonTable);
```

Agent 通过 CUSTOM 事件渲染：
```json
{
  "type": "CUSTOM",
  "name": "render_component",
  "value": {
    "component": "FlightComparisonTable",
    "props": { "flights": [{...}, {...}] }
  }
}
```

### 4.3 内置组件注册

应用启动时注册所有内置组件：

```typescript
// src/components/registry/built-in/index.ts
import { registerComponent } from "../ComponentRegistry";
import WeatherCard from "./WeatherCard";
import HotelList from "./HotelList";
import FlightCard from "./FlightCard";
import AttractionList from "./AttractionList";
import ProgressBar from "./ProgressBar";  // E2E 测试用组件

export function registerBuiltInComponents() {
  registerComponent("WeatherCard", WeatherCard);
  registerComponent("HotelList", HotelList);
  registerComponent("FlightCard", FlightCard);
  registerComponent("AttractionList", AttractionList);
  registerComponent("ProgressBar", ProgressBar);
}
```

### 4.4 内置组件 Props 接口

各内置组件从现有 `ItineraryCard.tsx` 提取，props 接口保持与工具返回数据结构一致：

```typescript
// WeatherCard props
interface WeatherCardProps {
  city: string;
  date: string;
  weather: string;
  temperature: string;
  humidity: string;
}

// HotelList props
interface HotelListProps {
  hotels: Array<{
    name: string;
    price: string;
    rating: number;
    location: string;
  }>;
}

// FlightCard props
interface FlightCardProps {
  flight_number: string;
  departure: string;
  arrival: string;
  date: string;
  passenger: string;
  status: string;
  gate: string;
  seat: string;
}

// AttractionList props
interface AttractionListProps {
  attractions: Array<{
    name: string;
    type: string;
    rating: number;
    duration: string;
    description: string;
  }>;
}

// ProgressBar props（E2E 测试用组件）
interface ProgressBarProps {
  step: number;
  total: number;
}
// 渲染输出：<div data-testid="rendered-ProgressBar">{step} / {total}</div>
```

---

## 5. 与现有架构集成

### 5.1 TravelPlanner.tsx 事件处理修订

保留现有事件处理逻辑，新增 `CUSTOM` 事件分支：

```typescript
// TravelPlanner.tsx
const { items: renderedItems, render: handleRenderComponent, clear: clearRendered } = useAGUIRenderer();

switch (event.type) {
  case "RUN_STARTED":
    setStatus("thinking");
    openToolCalls.clear();
    clearRendered();  // 新对话轮次清空已有渲染组件
    break;

  // ... 现有分支保留（TEXT_MESSAGE_*, TOOL_CALL_*, STATE_*, INTERRUPT, RUN_*）

  case "CUSTOM": {
    const name = event.name as string;
    if (name === "render_component") {
      const value = event.value as RenderInstruction;
      // component 在 unmount 时可省略
      if (value.action === "unmount") {
        handleRenderComponent({ componentId: "", props: {}, key: value.key, action: "unmount" });
      } else {
        handleRenderComponent({
          componentId: value.component!,
          props: value.props || {},
          key: value.key,
          action: value.action || "mount",
        });
      }
    }
    break;
  }
}
```

### 5.2 AGUIRenderer 组件

```typescript
// src/components/AGUIRenderer.tsx
import { useState, useCallback } from "react";
import { ComponentRegistry } from "./registry/ComponentRegistry";

// 渲染指令类型（前端内部使用，字段名与 AG-UI 事件略有不同）
export interface RenderInstruction {
  componentId: string;
  props: Record<string, unknown>;
  key?: string;
  action?: "mount" | "update" | "unmount";
}

interface RenderedItem {
  id: string;
  componentId: string;
  props: Record<string, unknown>;
}

export function useAGUIRenderer() {
  const [items, setItems] = useState<RenderedItem[]>([]);

  const render = useCallback((instruction: RenderInstruction) => {
    const { componentId, props, key, action = "mount" } = instruction;
    const id = key || `${componentId}-${Date.now()}`;

    setItems(prev => {
      if (action === "unmount") {
        return prev.filter(item => item.id !== id);
      }

      const exists = prev.find(item => item.id === id);
      if (exists) {
        // update
        return prev.map(item =>
          item.id === id ? { ...item, componentId, props } : item
        );
      }
      // mount
      return [...prev, { id, componentId, props }];
    });
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return { items, render, clear };
}

// 渲染组件树
export function AGUIComponentTree({ items }: { items: RenderedItem[] }) {
  const registry = ComponentRegistry.getInstance();

  return (
    <div className="agui-rendered-components">
      {items.map(item => {
        const Component = registry.resolve(item.componentId);
        if (!Component) {
          return <UnknownComponent key={item.id} id={item.componentId} />;
        }
        return <Component key={item.id} {...item.props} />;
      })}
    </div>
  );
}

function UnknownComponent({ id }: { id: string }) {
  return <div className="unknown-component">未知组件: {id}</div>;
}
```

### 5.3 页面布局调整

```tsx
// TravelPlanner.tsx render 部分
return (
  <div className="h-screen flex flex-col">
    {/* ... header ... */}
    <div className="flex-1 flex gap-4 p-4 overflow-hidden">
      {/* 左侧：聊天 + 生成式组件 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 聊天区域：占据主要空间，可滚动 */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          <ChatPanel messages={messages} currentResponse={currentResponse} onSend={handleSend} />
        </div>
        {/* 生成式 UI 渲染区域：固定在聊天下方，最大高度限制，超出可滚动 */}
        <div className="max-h-[40%] overflow-y-auto border-t border-gray-200">
          <AGUIComponentTree items={renderedItems} />
        </div>
      </div>
      {/* 右侧：行程信息（向后兼容） */}
      <div className="w-96 flex flex-col gap-4 overflow-hidden">
        <ItineraryCard itinerary={itinerary} />
        <div className="flex-1 min-h-0">
          <EventLog events={events} onClear={clearEvents} />
        </div>
      </div>
    </div>
  </div>
);
```

---

## 6. E2E 测试链路

### 6.1 测试策略

Playwright 拦截 `/api/agent` POST 请求，返回 Mock SSE 流，模拟后端发送 AG-UI 事件序列。

### 6.2 Mock SSE 辅助

**E2E 测试运行方式**：Playwright 启动浏览器访问前端 dev server（`http://localhost:5173`）。`page.route("/api/agent")` 在浏览器网络层拦截 `fetch("/api/agent")` 发出的请求（在请求到达 Vite dev server 代理之前），直接返回 Mock SSE 响应。无需启动后端服务。

```typescript
// e2e/helpers/mock-sse.ts
import type { Page } from "@playwright/test";

export async function mockAgentEndpoint(
  page: Page,
  eventGenerator: () => AsyncGenerator<string>
) {
  await page.route("/api/agent", async (route) => {
    const stream = new ReadableStream({
      async start(controller) {
        for await (const event of eventGenerator()) {
          controller.enqueue(new TextEncoder().encode(event));
        }
        controller.close();
      },
    });

    route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
      body: stream,
    });
  });
}
```

### 6.3 AG-UI 事件构建器

```typescript
// e2e/fixtures/agui-events.ts
export function sseEvent(data: object): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

export const agui = {
  runStarted: () => sseEvent({ type: "RUN_STARTED" }),

  textDelta: (delta: string) =>
    sseEvent({ type: "TEXT_MESSAGE_CONTENT", delta }),

  textEnd: () => sseEvent({ type: "TEXT_MESSAGE_END" }),

  toolCallStart: (id: string, name: string) =>
    sseEvent({ type: "TOOL_CALL_START", toolCallId: id, toolCallName: name }),

  toolCallResult: (id: string, content: unknown) =>
    sseEvent({ type: "TOOL_CALL_RESULT", toolCallId: id, content }),

  renderComponent: (component: string, props: object, key?: string) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_component",
      value: { component, props, key, action: "mount" },
    }),

  updateComponent: (component: string, props: object, key: string) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_component",
      value: { component, props, key, action: "update" },
    }),

  unmountComponent: (key: string) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_component",
      value: { key, action: "unmount" },
    }),

  runFinished: () => sseEvent({ type: "RUN_FINISHED" }),
};
```

### 6.4 测试用例

```typescript
// e2e/tests/render-component.spec.ts
import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("生成式 UI 组件渲染", () => {
  test("单组件渲染：天气卡片", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.textDelta("正在为您查询天气...");
      yield agui.toolCallStart("call_1", "get_weather");
      yield agui.toolCallResult("call_1", {
        city: "北京",
        temperature: "28°C",
      });
      yield agui.renderComponent("WeatherCard", {
        city: "北京",
        temperature: "28°C",
      });
      yield agui.textEnd();
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("输入消息...").fill("北京天气");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByText("北京")).toBeVisible();
    await expect(page.getByText("28°C")).toBeVisible();
  });

  test("多组件同时渲染", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent(
        "WeatherCard",
        { city: "北京" },
        "weather-1"
      );
      yield agui.renderComponent(
        "HotelList",
        { hotels: [{ name: "酒店A" }] },
        "hotels-1"
      );
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("输入消息...").fill("规划行程");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByTestId("rendered-HotelList")).toBeVisible();
  });

  test("组件更新", async ({ page }) => {
    // ProgressBar 为内置测试组件：接收 {step, total} props，渲染 "step / total" 文本
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent(
        "ProgressBar",
        { step: 1, total: 3 },
        "progress"
      );
      yield agui.updateComponent(
        "ProgressBar",
        { step: 2, total: 3 },
        "progress"
      );
      yield agui.updateComponent(
        "ProgressBar",
        { step: 3, total: 3 },
        "progress"
      );
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("输入消息...").fill("开始规划");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByText("3 / 3")).toBeVisible();
  });

  test("未注册组件显示占位符", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("UnknownWidget", { data: "test" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("输入消息...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByText("未知组件: UnknownWidget")).toBeVisible();
  });
});
```

### 6.5 错误场景覆盖

| 场景 | 测试文件 | 预期行为 |
|------|----------|----------|
| 渲染未注册组件 | `error-handling.spec.ts` | 显示"未知组件: xxx"占位符，不崩溃 |
| 重复 key 的组件 | `multi-component.spec.ts` | 更新已有组件，不重复渲染 |
| 组件卸载 | `multi-component.spec.ts` | 组件从 DOM 移除 |
| update 先于 mount（相同 key） | `error-handling.spec.ts` | 等价于 mount，正常渲染组件 |
| unmount 不存在的 key | `error-handling.spec.ts` | 静默忽略，不报错 |
| RUN_STARTED 清空组件 | `render-component.spec.ts` | 新对话轮次清空已有渲染组件 |

---

## 7. 文件结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── registry/
│   │   │   ├── ComponentRegistry.ts         # 组件注册表
│   │   │   └── built-in/
│   │   │       ├── index.ts                 # 注册所有内置组件
│   │   │       ├── WeatherCard.tsx          # 天气卡片
│   │   │       ├── HotelList.tsx            # 酒店列表
│   │   │       ├── FlightCard.tsx           # 航班卡片
│   │   │       ├── AttractionList.tsx       # 景点列表
│   │   │       └── ProgressBar.tsx          # 进度条（E2E测试用）
│   │   ├── AGUIRenderer.tsx                 # 渲染协调器 + useAGUIRenderer hook
│   │   ├── TravelPlanner.tsx                # 修订：集成 AGUIRenderer
│   │   ├── ItineraryCard.tsx                # 保留（向后兼容）
│   │   └── ...
│   └── main.tsx                             # 应用入口：注册内置组件
├── e2e/
│   ├── fixtures/
│   │   └── agui-events.ts                   # AG-UI 事件构建器
│   ├── helpers/
│   │   └── mock-sse.ts                      # SSE Mock 辅助
│   └── tests/
│       ├── render-component.spec.ts         # 组件渲染基础测试
│       ├── multi-component.spec.ts          # 多组件、更新、卸载
│       └── error-handling.spec.ts           # 错误场景
└── playwright.config.ts                     # Playwright 配置
```

---

## 8. 实现顺序

1. **ComponentRegistry**：实现注册表单例
2. **AGUIRenderer**：实现 useAGUIRenderer hook 和 AGUIComponentTree
3. **TravelPlanner 集成**：新增 CUSTOM 事件分支，接入渲染区域
4. **内置组件拆分**：将 ItineraryCard 拆分为独立注册组件
5. **E2E 测试基础设施**：Mock SSE + 事件构建器
6. **E2E 测试用例**：覆盖单组件、多组件、更新、卸载、错误场景

---

## 9. 向后兼容

- 现有 `STATE_SNAPSHOT` / `TOOL_CALL_RESULT` → `itinerary` → `ItineraryCard` 链路**完全保留**
- 新增 `CUSTOM render_component` 链路**独立运行**
- 现有业务不受影响，新功能通过注册表渐进接入
