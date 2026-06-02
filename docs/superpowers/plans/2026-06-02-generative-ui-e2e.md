# 生成式 UI 组件渲染与 E2E 测试链路实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现可扩展的前端组件注册表与渲染框架，使 Agent 能通过 AG-UI `CUSTOM` 事件动态控制前端 UI 渲染，并建立 Playwright E2E 测试链路验证完整能力。

**Architecture:** 前端通过 `ComponentRegistry` 单例维护 `id → React.FC` 映射；`useAGUIRenderer` Hook 管理已渲染组件状态（mount/update/unmount/clear）；`AGUIComponentTree` 组件遍历状态并渲染对应组件；`TravelPlanner` 在 `CUSTOM` 事件分支中调用渲染逻辑。Playwright E2E 通过 `page.route` 拦截 `/api/agent` 并返回 Mock SSE 事件流。

**Tech Stack:** React 18 + TypeScript + Vite + Tailwind CSS v4 + Vitest (单元测试) + React Testing Library (组件测试) + Playwright (E2E)

---

## 文件结构映射

```
frontend/
├── src/
│   ├── components/
│   │   ├── registry/
│   │   │   ├── ComponentRegistry.ts         # 组件注册表单例
│   │   │   └── built-in/
│   │   │       ├── index.ts                 # 注册所有内置组件
│   │   │       ├── WeatherCard.tsx          # 天气卡片（从 ItineraryCard 提取）
│   │   │       ├── HotelList.tsx            # 酒店列表（从 ItineraryCard 提取）
│   │   │       ├── FlightCard.tsx           # 航班卡片（从 ItineraryCard 提取）
│   │   │       ├── AttractionList.tsx       # 景点列表（从 ItineraryCard 提取）
│   │   │       └── ProgressBar.tsx          # 进度条（E2E 测试用）
│   │   ├── AGUIRenderer.tsx                 # useAGUIRenderer + AGUIComponentTree
│   │   ├── TravelPlanner.tsx                # 修订：CUSTOM 事件 + 渲染区域
│   │   └── ItineraryCard.tsx                # 保留（向后兼容）
│   ├── main.tsx                             # 应用入口：注册内置组件
│   └── ...
├── src/__tests__/                           # 单元测试（Vitest）
│   ├── ComponentRegistry.test.ts
│   └── AGUIRenderer.test.tsx
├── e2e/                                     # E2E 测试（Playwright）
│   ├── fixtures/
│   │   └── agui-events.ts
│   ├── helpers/
│   │   └── mock-sse.ts
│   └── tests/
│       ├── render-component.spec.ts
│       ├── multi-component.spec.ts
│       └── error-handling.spec.ts
├── vitest.config.ts                         # Vitest 配置
└── playwright.config.ts                     # Playwright 配置
```

---

## Task 1: 安装测试依赖

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: 安装依赖**

Run:
```bash
cd frontend
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom jsdom
npm install -D @playwright/test
npx playwright install
```

- [ ] **Step 2: 配置 Vitest**

Create `frontend/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
  },
});
```

Create `frontend/src/__tests__/setup.ts`:
```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 3: 验证安装**

Run:
```bash
npx vitest run
```
Expected: No tests found, but command succeeds.

- [ ] **Step 4: Commit**

```bash
cd frontend
git add package.json package-lock.json vitest.config.ts src/__tests__/
git commit -m "chore(test): install vitest, react-testing-library, playwright"
```

---

## Task 2: ComponentRegistry

**Files:**
- Create: `frontend/src/components/registry/ComponentRegistry.ts`
- Create: `frontend/src/__tests__/ComponentRegistry.test.ts`

- [ ] **Step 1: 写失败测试**

Create `frontend/src/__tests__/ComponentRegistry.test.ts`:
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { ComponentRegistry, registerComponent } from '../components/registry/ComponentRegistry';

function TestComponent() {
  return <div>Test</div>;
}

describe('ComponentRegistry', () => {
  beforeEach(() => {
    ComponentRegistry.getInstance().clear();
  });

  it('registers and resolves a component', () => {
    const registry = ComponentRegistry.getInstance();
    registry.register('Test', TestComponent);
    expect(registry.resolve('Test')).toBe(TestComponent);
  });

  it('returns undefined for unregistered component', () => {
    const registry = ComponentRegistry.getInstance();
    expect(registry.resolve('Unknown')).toBeUndefined();
  });

  it('lists registered components', () => {
    const registry = ComponentRegistry.getInstance();
    registry.register('A', TestComponent);
    registry.register('B', TestComponent);
    expect(registry.list()).toEqual(['A', 'B']);
  });

  it('unregister removes component', () => {
    const registry = ComponentRegistry.getInstance();
    registry.register('X', TestComponent);
    registry.unregister('X');
    expect(registry.resolve('X')).toBeUndefined();
  });
});

describe('registerComponent helper', () => {
  it('registers via helper function', () => {
    registerComponent('HelperTest', TestComponent);
    expect(ComponentRegistry.getInstance().resolve('HelperTest')).toBe(TestComponent);
  });
});
```

Run:
```bash
cd frontend
npx vitest run ComponentRegistry.test.ts
```
Expected: FAIL - "ComponentRegistry" not found

- [ ] **Step 2: 实现 ComponentRegistry**

Create `frontend/src/components/registry/ComponentRegistry.ts`:
```typescript
import type { FC } from 'react';

export class ComponentRegistry {
  private static instance: ComponentRegistry | null = null;
  private components = new Map<string, FC<any>>();

  static getInstance(): ComponentRegistry {
    if (!ComponentRegistry.instance) {
      ComponentRegistry.instance = new ComponentRegistry();
    }
    return ComponentRegistry.instance;
  }

  register(id: string, component: FC<any>): void {
    this.components.set(id, component);
  }

  unregister(id: string): void {
    this.components.delete(id);
  }

  resolve(id: string): FC<any> | undefined {
    return this.components.get(id);
  }

  list(): string[] {
    return Array.from(this.components.keys());
  }

  clear(): void {
    this.components.clear();
  }
}

export function registerComponent(id: string, component: FC<any>): void {
  ComponentRegistry.getInstance().register(id, component);
}
```

- [ ] **Step 3: 运行测试**

```bash
cd frontend
npx vitest run ComponentRegistry.test.ts
```
Expected: 5 tests passed

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/registry/ComponentRegistry.ts frontend/src/__tests__/ComponentRegistry.test.ts
git commit -m "feat(registry): add ComponentRegistry singleton"
```

---

## Task 3: useAGUIRenderer Hook

**Files:**
- Create: `frontend/src/components/AGUIRenderer.tsx` (hook 部分)
- Create: `frontend/src/__tests__/AGUIRenderer.test.tsx`

- [ ] **Step 1: 写失败测试**

Create `frontend/src/__tests__/AGUIRenderer.test.tsx`:
```typescript
import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAGUIRenderer } from '../components/AGUIRenderer';

describe('useAGUIRenderer', () => {
  it('mounts a component', () => {
    const { result } = renderHook(() => useAGUIRenderer());
    act(() => {
      result.current.render({ componentId: 'Test', props: { x: 1 }, action: 'mount' });
    });
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].componentId).toBe('Test');
    expect(result.current.items[0].props).toEqual({ x: 1 });
  });

  it('updates by key', () => {
    const { result } = renderHook(() => useAGUIRenderer());
    act(() => {
      result.current.render({ componentId: 'Test', props: { x: 1 }, key: 'k1', action: 'mount' });
    });
    act(() => {
      result.current.render({ componentId: 'Test', props: { x: 2 }, key: 'k1', action: 'update' });
    });
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].props).toEqual({ x: 2 });
  });

  it('unmounts by key', () => {
    const { result } = renderHook(() => useAGUIRenderer());
    act(() => {
      result.current.render({ componentId: 'Test', props: {}, key: 'k1', action: 'mount' });
    });
    act(() => {
      result.current.render({ componentId: '', props: {}, key: 'k1', action: 'unmount' });
    });
    expect(result.current.items).toHaveLength(0);
  });

  it('clears all items', () => {
    const { result } = renderHook(() => useAGUIRenderer());
    act(() => {
      result.current.render({ componentId: 'A', props: {}, action: 'mount' });
      result.current.render({ componentId: 'B', props: {}, action: 'mount' });
    });
    act(() => {
      result.current.clear();
    });
    expect(result.current.items).toHaveLength(0);
  });
});
```

Run:
```bash
cd frontend
npx vitest run AGUIRenderer.test.tsx
```
Expected: FAIL - "useAGUIRenderer" not found

- [ ] **Step 2: 实现 Hook**

Create `frontend/src/components/AGUIRenderer.tsx`:
```typescript
import { useState, useCallback } from 'react';

export interface RenderInstruction {
  componentId: string;
  props: Record<string, unknown>;
  key?: string;
  action?: 'mount' | 'update' | 'unmount';
}

interface RenderedItem {
  id: string;
  componentId: string;
  props: Record<string, unknown>;
}

export function useAGUIRenderer() {
  const [items, setItems] = useState<RenderedItem[]>([]);

  const render = useCallback((instruction: RenderInstruction) => {
    const { componentId, props, key, action = 'mount' } = instruction;
    const id = key || `${componentId}-${Date.now()}`;

    setItems(prev => {
      if (action === 'unmount') {
        return prev.filter(item => item.id !== id);
      }

      const exists = prev.find(item => item.id === id);
      if (exists) {
        return prev.map(item =>
          item.id === id ? { ...item, componentId, props } : item
        );
      }
      return [...prev, { id, componentId, props }];
    });
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return { items, render, clear };
}
```

- [ ] **Step 3: 运行测试**

```bash
cd frontend
npx vitest run AGUIRenderer.test.tsx
```
Expected: 4 tests passed

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AGUIRenderer.tsx frontend/src/__tests__/AGUIRenderer.test.tsx
git commit -m "feat(renderer): add useAGUIRenderer hook"
```

---

## Task 4: AGUIComponentTree + UnknownComponent

**Files:**
- Modify: `frontend/src/components/AGUIRenderer.tsx` (添加组件树渲染)
- Create: `frontend/src/__tests__/AGUIComponentTree.test.tsx`

- [ ] **Step 1: 注册测试组件并写测试**

Create `frontend/src/__tests__/AGUIComponentTree.test.tsx`:
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AGUIComponentTree } from '../components/AGUIRenderer';
import { ComponentRegistry } from '../components/registry/ComponentRegistry';

function TestCard({ title }: { title: string }) {
  return <div data-testid="test-card">{title}</div>;
}

describe('AGUIComponentTree', () => {
  beforeEach(() => {
    ComponentRegistry.getInstance().clear();
  });

  it('renders registered component', () => {
    ComponentRegistry.getInstance().register('TestCard', TestCard);
    render(<AGUIComponentTree items={[{ id: '1', componentId: 'TestCard', props: { title: 'Hello' } }]} />);
    expect(screen.getByTestId('test-card')).toHaveTextContent('Hello');
  });

  it('shows placeholder for unknown component', () => {
    render(<AGUIComponentTree items={[{ id: '1', componentId: 'Unknown', props: {} }]} />);
    expect(screen.getByText('未知组件: Unknown')).toBeInTheDocument();
  });

  it('renders multiple components', () => {
    ComponentRegistry.getInstance().register('TestCard', TestCard);
    render(
      <AGUIComponentTree
        items={[
          { id: '1', componentId: 'TestCard', props: { title: 'A' } },
          { id: '2', componentId: 'TestCard', props: { title: 'B' } },
        ]}
      />
    );
    expect(screen.getAllByTestId('test-card')).toHaveLength(2);
  });
});
```

Run:
```bash
cd frontend
npx vitest run AGUIComponentTree.test.tsx
```
Expected: FAIL - AGUIComponentTree not exported

- [ ] **Step 2: 实现组件树**

Append to `frontend/src/components/AGUIRenderer.tsx`:
```typescript
import { ComponentRegistry } from './registry/ComponentRegistry';

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

- [ ] **Step 3: 运行测试**

```bash
cd frontend
npx vitest run AGUIComponentTree.test.tsx
```
Expected: 3 tests passed

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AGUIRenderer.tsx frontend/src/__tests__/AGUIComponentTree.test.tsx
git commit -m "feat(renderer): add AGUIComponentTree with unknown component fallback"
```

---

## Task 5: TravelPlanner 集成 CUSTOM 事件

**Files:**
- Modify: `frontend/src/components/TravelPlanner.tsx`

- [ ] **Step 1: 导入并接入 Hook**

在 `TravelPlanner.tsx` 顶部添加导入：
```typescript
import { useAGUIRenderer, AGUIComponentTree } from './AGUIRenderer';
import type { RenderInstruction } from './AGUIRenderer';
```

在组件内部初始化：
```typescript
const { items: renderedItems, render: handleRenderComponent, clear: clearRendered } = useAGUIRenderer();
```

- [ ] **Step 2: 添加 RUN_STARTED 处理**

在 `switch (event.type)` 的 `RUN_STARTED` case 中添加：
```typescript
case "RUN_STARTED":
  setStatus("thinking");
  openToolCalls.clear();
  clearRendered();  // 新对话轮次清空已有渲染组件
  break;
```

- [ ] **Step 3: 添加 CUSTOM 事件处理**

在 `switch` 中添加新 case：
```typescript
case "CUSTOM": {
  const name = event.name as string;
  if (name === "render_component") {
    const value = event.value as Record<string, unknown>;
    const action = (value.action as string) || "mount";
    if (action === "unmount") {
      handleRenderComponent({
        componentId: "",
        props: {},
        key: value.key as string,
        action: "unmount",
      });
    } else {
      handleRenderComponent({
        componentId: value.component as string,
        props: (value.props as Record<string, unknown>) || {},
        key: value.key as string | undefined,
        action: action as "mount" | "update",
      });
    }
  }
  break;
}
```

- [ ] **Step 4: 添加渲染区域到布局**

修改 render 部分的左侧布局：
```tsx
<div className="flex-1 flex flex-col min-w-0">
  <div className="flex-1 min-h-0 overflow-y-auto">
    <ChatPanel messages={messages} currentResponse={currentResponse} onSend={handleSend} />
  </div>
  <div className="max-h-[40%] overflow-y-auto border-t border-gray-200">
    <AGUIComponentTree items={renderedItems} />
  </div>
</div>
```

- [ ] **Step 5: 验证编译**

```bash
cd frontend
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/TravelPlanner.tsx
git commit -m "feat(planner): integrate AGUIRenderer with CUSTOM event handling"
```

---

## Task 6: 内置组件拆分

**Files:**
- Create: `frontend/src/components/registry/built-in/WeatherCard.tsx`
- Create: `frontend/src/components/registry/built-in/HotelList.tsx`
- Create: `frontend/src/components/registry/built-in/FlightCard.tsx`
- Create: `frontend/src/components/registry/built-in/AttractionList.tsx`
- Create: `frontend/src/components/registry/built-in/ProgressBar.tsx`
- Create: `frontend/src/components/registry/built-in/index.ts`

**策略**：从现有 `ItineraryCard.tsx` 中复制各子组件的 JSX 和类型，保持样式不变。

- [ ] **Step 1: 创建 WeatherCard**

Create `frontend/src/components/registry/built-in/WeatherCard.tsx`:
```tsx
import type { WeatherInfo } from "../../../types";

export default function WeatherCard(props: WeatherInfo) {
  return (
    <div data-testid="rendered-WeatherCard" className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
        </svg>
        <span className="text-xs text-blue-700 font-semibold">天气</span>
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-gray-800">{props.date} {props.weather}</p>
        <p className="text-xs text-gray-600">气温: {props.temperature}</p>
        <p className="text-xs text-gray-600">湿度: {props.humidity}</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 HotelList**

Create `frontend/src/components/registry/built-in/HotelList.tsx`:
```tsx
import type { HotelInfo } from "../../../types";

export default function HotelList({ hotels }: { hotels: HotelInfo[] }) {
  return (
    <div data-testid="rendered-HotelList" className="mb-4">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span className="text-xs text-gray-500 font-semibold uppercase tracking-wide">推荐酒店</span>
      </div>
      <div className="space-y-2">
        {hotels.map((hotel, idx) => (
          <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
            <p className="font-semibold text-sm text-gray-800">{hotel.name}</p>
            <p className="text-xs text-gray-500 mt-0.5">{hotel.location}</p>
            <div className="flex justify-between mt-1.5">
              <span className="text-xs font-medium text-emerald-600">{hotel.price}</span>
              <span className="text-xs font-medium text-amber-600">★ {hotel.rating}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 FlightCard、AttractionList、ProgressBar**

Create `frontend/src/components/registry/built-in/FlightCard.tsx`:
```tsx
import type { FlightInfo } from "../../../types";

export default function FlightCard(props: FlightInfo) {
  return (
    <div data-testid="rendered-FlightCard" className="mb-4 p-3 bg-gradient-to-r from-sky-50 to-blue-50 rounded-lg border border-sky-100">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-sky-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
        <span className="text-xs text-sky-700 font-semibold">航班信息</span>
      </div>
      <div className="space-y-1.5">
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">航班号</span>
          <span className="text-xs font-medium text-gray-800">{props.flight_number}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">航线</span>
          <span className="text-xs font-medium text-gray-800">{props.departure} → {props.arrival}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">日期</span>
          <span className="text-xs font-medium text-gray-800">{props.date}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">座位</span>
          <span className="text-xs font-medium text-gray-800">{props.seat}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">状态</span>
          <span className="text-xs font-medium text-emerald-600">{props.status}</span>
        </div>
      </div>
    </div>
  );
}
```

Create `frontend/src/components/registry/built-in/AttractionList.tsx`:
```tsx
import type { AttractionInfo } from "../../../types";

export default function AttractionList({ attractions }: { attractions: AttractionInfo[] }) {
  return (
    <div data-testid="rendered-AttractionList">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span className="text-xs text-gray-500 font-semibold uppercase tracking-wide">推荐景点</span>
      </div>
      <div className="space-y-2">
        {attractions.map((attr, idx) => (
          <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm text-gray-800">{attr.name}</p>
              <span className="text-xs px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-700">{attr.type}</span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{attr.description}</p>
            <div className="flex justify-between mt-1.5">
              <span className="text-xs text-gray-500">⏱ {attr.duration}</span>
              <span className="text-xs font-medium text-amber-600">★ {attr.rating}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

Create `frontend/src/components/registry/built-in/ProgressBar.tsx`:
```tsx
export default function ProgressBar({ step, total }: { step: number; total: number }) {
  return (
    <div data-testid="rendered-ProgressBar" className="p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">进度</span>
        <span className="text-xs font-medium text-gray-700">{step} / {total}</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-300"
          style={{ width: `${(step / total) * 100}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 创建 index.ts**

Create `frontend/src/components/registry/built-in/index.ts`:
```typescript
import { registerComponent } from "../ComponentRegistry";
import WeatherCard from "./WeatherCard";
import HotelList from "./HotelList";
import FlightCard from "./FlightCard";
import AttractionList from "./AttractionList";
import ProgressBar from "./ProgressBar";

export function registerBuiltInComponents() {
  registerComponent("WeatherCard", WeatherCard);
  registerComponent("HotelList", HotelList);
  registerComponent("FlightCard", FlightCard);
  registerComponent("AttractionList", AttractionList);
  registerComponent("ProgressBar", ProgressBar);
}
```

- [ ] **Step 5: 验证编译**

```bash
cd frontend
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/registry/built-in/
git commit -m "feat(components): extract built-in cards from ItineraryCard"
```

---

## Task 7: main.tsx 注册内置组件

**Files:**
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: 添加注册调用**

在 `frontend/src/main.tsx` 中，在 `createRoot(...).render(...)` 之前添加：
```typescript
import { registerBuiltInComponents } from "./components/registry/built-in";

registerBuiltInComponents();
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/main.tsx
git commit -m "feat(main): register built-in components on app startup"
```

---

## Task 8: Playwright E2E 基础设施

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/fixtures/agui-events.ts`
- Create: `frontend/e2e/helpers/mock-sse.ts`

- [ ] **Step 1: 配置 Playwright**

Create `frontend/playwright.config.ts`:
```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
```

- [ ] **Step 2: 创建 AG-UI 事件构建器**

Create `frontend/e2e/fixtures/agui-events.ts`:
```typescript
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

- [ ] **Step 3: 创建 Mock SSE 辅助**

Create `frontend/e2e/helpers/mock-sse.ts`:
```typescript
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

- [ ] **Step 4: Commit**

```bash
git add frontend/playwright.config.ts frontend/e2e/
git commit -m "test(e2e): add playwright config, agui event fixtures, mock sse helper"
```

---

## Task 9: E2E 测试用例

**Files:**
- Create: `frontend/e2e/tests/render-component.spec.ts`
- Create: `frontend/e2e/tests/multi-component.spec.ts`
- Create: `frontend/e2e/tests/error-handling.spec.ts`

- [ ] **Step 1: 单组件渲染测试**

Create `frontend/e2e/tests/render-component.spec.ts`:
```typescript
import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("单组件渲染", () => {
  test("天气卡片", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.textDelta("正在为您查询天气...");
      yield agui.toolCallStart("call_1", "get_weather");
      yield agui.toolCallResult("call_1", { city: "北京", temperature: "28°C" });
      yield agui.renderComponent("WeatherCard", {
        city: "北京",
        temperature: "28°C",
        weather: "晴朗",
        date: "2026-06-03",
        humidity: "65%",
      });
      yield agui.textEnd();
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("北京天气");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByText("北京")).toBeVisible();
    await expect(page.getByText("28°C")).toBeVisible();
  });

  test("RUN_STARTED 清空已有组件", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("第一次");
    await page.getByRole("button", { name: "发送" }).click();
    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();

    // 第二次对话，RUN_STARTED 应清空
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.runFinished();
    });
    await page.getByPlaceholder("说点什么...").fill("第二次");
    await page.getByRole("button", { name: "发送" }).click();
    await expect(page.getByTestId("rendered-WeatherCard")).not.toBeVisible();
  });
});
```

- [ ] **Step 2: 多组件与更新测试**

Create `frontend/e2e/tests/multi-component.spec.ts`:
```typescript
import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("多组件与生命周期", () => {
  test("多组件同时渲染", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" }, "weather-1");
      yield agui.renderComponent("HotelList", { hotels: [{ name: "酒店A", price: "¥580/晚", rating: 4.6, location: "市中心" }] }, "hotels-1");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("规划行程");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByTestId("rendered-HotelList")).toBeVisible();
  });

  test("组件更新", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("ProgressBar", { step: 1, total: 3 }, "progress");
      yield agui.updateComponent("ProgressBar", { step: 2, total: 3 }, "progress");
      yield agui.updateComponent("ProgressBar", { step: 3, total: 3 }, "progress");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("开始规划");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByText("3 / 3")).toBeVisible();
  });

  test("组件卸载", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" }, "weather-1");
      yield agui.unmountComponent("weather-1");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试卸载");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).not.toBeVisible();
  });
});
```

- [ ] **Step 3: 错误处理测试**

Create `frontend/e2e/tests/error-handling.spec.ts`:
```typescript
import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("错误处理", () => {
  test("未注册组件显示占位符", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("UnknownWidget", { data: "test" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByText("未知组件: UnknownWidget")).toBeVisible();
  });

  test("update 先于 mount（相同 key）等价于 mount", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.updateComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" }, "weather-1");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
  });

  test("unmount 不存在的 key 静默忽略", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.unmountComponent("nonexistent");
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
  });
});
```

- [ ] **Step 4: 运行 E2E 测试**

```bash
cd frontend
npx playwright test
```
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/tests/
git commit -m "test(e2e): add generative UI rendering tests"
```

---

## 任务总结

| 任务 | 产出 | 验证方式 |
|------|------|----------|
| Task 1 | 测试依赖安装 | `vitest` 命令成功 |
| Task 2 | ComponentRegistry | 5 个单元测试通过 |
| Task 3 | useAGUIRenderer | 4 个单元测试通过 |
| Task 4 | AGUIComponentTree | 3 个单元测试通过 |
| Task 5 | TravelPlanner 集成 | `tsc --noEmit` 通过 |
| Task 6 | 内置组件拆分 | `tsc --noEmit` 通过 |
| Task 7 | main.tsx 注册 | 运行时组件可用 |
| Task 8 | Playwright 基础设施 | 配置加载成功 |
| Task 9 | E2E 测试用例 | Playwright 全部通过 |
