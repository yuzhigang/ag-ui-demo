# Generative Grid Page Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first-version generative UI page runtime where the agent can request a validated `render_page` AG-UI event and the frontend renders it as a 12-column grid of registered components.

**Architecture:** Keep `render_component` for transient UI and add `render_page` for complete page replacement. The frontend owns `PageRenderer` and registry-based rendering; the backend owns component catalog loading, PageSpec validation, and a wrapper that converts a controlled `render_page` tool result into an AG-UI `CustomEvent`.

**Tech Stack:** React 18, TypeScript, Vitest, Playwright, FastAPI, Microsoft Agent Framework, AG-UI `CustomEvent`, Pydantic-style Python validation with plain dataclasses/functions where simpler.

---

## File Structure

Frontend files:

- Create `frontend/src/components/page/PageSpec.ts`: shared TypeScript types and small helpers for grid spans and gaps.
- Create `frontend/src/components/page/PageRenderer.tsx`: renders a validated-ish `PageSpec` into a responsive grid using `ComponentRegistry`.
- Create `frontend/src/__tests__/PageRenderer.test.tsx`: unit tests for registered rendering, fallback, invalid spans, and page title.
- Modify `frontend/src/components/TravelPlanner.tsx`: keep transient `render_component` items, add `currentPage`, handle `CUSTOM render_page`, clear transient components when a page arrives, and accept `componentId` plus legacy `component`.
- Modify `frontend/e2e/fixtures/agui-events.ts`: add `renderPage`.
- Create `frontend/e2e/tests/render-page.spec.ts`: E2E test for a three-component generated page and the transient clearing behavior.

Backend files:

- Create `backend/config/components.yaml`: component catalog for built-in frontend components.
- Create `backend/src/ui/__init__.py`: exports UI runtime helpers.
- Create `backend/src/ui/component_catalog.py`: loads and formats the component catalog.
- Create `backend/src/ui/page_spec.py`: validates and normalizes `PageSpec` objects.
- Create `backend/src/ui/render_page_tool.py`: exposes the controlled `render_page(page)` tool and marker helpers.
- Create `backend/src/ui/agui_runtime.py`: wraps an AG-UI runner and injects `CustomEvent(name="render_page")` when a validated render-page tool result is observed.
- Modify `backend/src/workflow.py`: inject catalog instructions and register the `render_page` tool.
- Modify `backend/src/main.py`: wrap the existing workflow with `AGUIPageRuntime`.
- Create `backend/tests/test_component_catalog.py`: catalog loading and prompt-summary tests.
- Create `backend/tests/test_page_spec.py`: validation and normalization tests.
- Create `backend/tests/test_agui_page_runtime.py`: wrapper injects a `CUSTOM render_page` event after render-page tool result.

Implementation order:

1. Frontend `PageRenderer`.
2. Frontend `TravelPlanner` protocol integration.
3. Frontend E2E coverage.
4. Backend component catalog.
5. Backend PageSpec validation.
6. Backend render-page tool and AG-UI event wrapper.
7. Full verification.

---

### Task 1: Frontend PageSpec Types And PageRenderer

**Files:**
- Create: `frontend/src/components/page/PageSpec.ts`
- Create: `frontend/src/components/page/PageRenderer.tsx`
- Create: `frontend/src/__tests__/PageRenderer.test.tsx`

- [ ] **Step 1: Write the failing PageRenderer tests**

Create `frontend/src/__tests__/PageRenderer.test.tsx`:

```tsx
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ComponentRegistry } from "../components/registry/ComponentRegistry";
import { PageRenderer } from "../components/page/PageRenderer";
import type { PageSpec } from "../components/page/PageSpec";

function TestCard({ title }: { title: string }) {
  return <div data-testid="test-card">{title}</div>;
}

function ExplodingCard() {
  throw new Error("render failed");
}

describe("PageRenderer", () => {
  beforeEach(() => {
    ComponentRegistry.getInstance().clear();
  });

  it("renders a page title and registered grid items", () => {
    ComponentRegistry.getInstance().register("TestCard", TestCard);
    const page: PageSpec = {
      version: "1",
      title: "Generated Page",
      layout: {
        kind: "grid",
        columns: 12,
        gap: "md",
        items: [
          {
            componentId: "TestCard",
            key: "a",
            span: 4,
            props: { title: "A" },
          },
          {
            componentId: "TestCard",
            key: "b",
            span: 8,
            props: { title: "B" },
          },
        ],
      },
    };

    render(<PageRenderer page={page} />);

    expect(screen.getByRole("heading", { name: "Generated Page" })).toBeInTheDocument();
    expect(screen.getAllByTestId("test-card")).toHaveLength(2);
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
  });

  it("shows a fallback for unknown components", () => {
    const page: PageSpec = {
      version: "1",
      layout: {
        kind: "grid",
        columns: 12,
        items: [
          {
            componentId: "MissingCard",
            key: "missing",
            span: 4,
            props: {},
          },
        ],
      },
    };

    render(<PageRenderer page={page} />);

    expect(screen.getByText("未知组件: MissingCard")).toBeInTheDocument();
  });

  it("uses full-width fallback for invalid spans", () => {
    ComponentRegistry.getInstance().register("TestCard", TestCard);
    const page = {
      version: "1",
      layout: {
        kind: "grid",
        columns: 12,
        items: [
          {
            componentId: "TestCard",
            key: "bad-span",
            span: 5,
            props: { title: "Bad span" },
          },
        ],
      },
    } as unknown as PageSpec;

    render(<PageRenderer page={page} />);

    const item = screen.getByTestId("page-grid-item-bad-span");
    expect(item).toHaveClass("md:col-span-12");
  });

  it("isolates component render failures to the failed item", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    ComponentRegistry.getInstance().register("ExplodingCard", ExplodingCard);
    const page: PageSpec = {
      version: "1",
      layout: {
        kind: "grid",
        columns: 12,
        items: [
          {
            componentId: "ExplodingCard",
            key: "boom",
            span: 12,
            props: {},
          },
        ],
      },
    };

    render(<PageRenderer page={page} />);

    expect(screen.getByText("组件渲染失败: ExplodingCard")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd frontend
npx vitest run src/__tests__/PageRenderer.test.tsx
```

Expected: FAIL because `../components/page/PageRenderer` and `../components/page/PageSpec` do not exist.

- [ ] **Step 3: Create the PageSpec types**

Create `frontend/src/components/page/PageSpec.ts`:

```ts
export type GridSpan = 3 | 4 | 6 | 8 | 12;
export type GridGap = "sm" | "md" | "lg";
export type GridImportance = "primary" | "secondary" | "supporting";

export interface PageSpec {
  version: "1";
  title?: string;
  layout: GridLayout;
}

export interface GridLayout {
  kind: "grid";
  columns: 12;
  gap?: GridGap;
  items: GridItem[];
}

export interface GridItem {
  componentId: string;
  key: string;
  span: GridSpan;
  props: Record<string, unknown>;
  importance?: GridImportance;
}

export const VALID_GRID_SPANS = [3, 4, 6, 8, 12] as const;

export function normalizeGridSpan(span: unknown): GridSpan {
  return VALID_GRID_SPANS.includes(span as GridSpan) ? (span as GridSpan) : 12;
}

export function gridSpanClass(span: unknown): string {
  const normalized = normalizeGridSpan(span);
  return `col-span-12 md:col-span-${normalized}`;
}

export function gridGapClass(gap: unknown): string {
  if (gap === "sm") return "gap-2";
  if (gap === "lg") return "gap-6";
  return "gap-4";
}
```

- [ ] **Step 4: Create the PageRenderer implementation**

Create `frontend/src/components/page/PageRenderer.tsx`:

```tsx
import type { FC, ReactNode } from "react";
import { Component, createElement } from "react";
import { ComponentRegistry } from "../registry/ComponentRegistry";
import type { GridItem, PageSpec } from "./PageSpec";
import { gridGapClass, gridSpanClass } from "./PageSpec";

interface PageRendererProps {
  page: PageSpec | null;
}

interface ItemErrorBoundaryProps {
  componentId: string;
  children: ReactNode;
}

interface ItemErrorBoundaryState {
  hasError: boolean;
}

class ItemErrorBoundary extends Component<ItemErrorBoundaryProps, ItemErrorBoundaryState> {
  state: ItemErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ItemErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error(`Generated page component failed: ${this.props.componentId}`, error);
  }

  render() {
    if (this.state.hasError) {
      return <ItemErrorFallback componentId={this.props.componentId} />;
    }
    return this.props.children;
  }
}

export function PageRenderer({ page }: PageRendererProps) {
  if (!page) return null;

  const items = Array.isArray(page.layout?.items) ? page.layout.items : [];

  return (
    <section className="generated-page p-2" data-testid="generated-page">
      {page.title && (
        <h2 className="mb-3 text-sm font-semibold text-gray-700">{page.title}</h2>
      )}
      <div
        className={`grid grid-cols-12 ${gridGapClass(page.layout?.gap)}`}
        data-testid="generated-page-grid"
      >
        {items.map((item) => (
          <GeneratedGridItem key={item.key} item={item} />
        ))}
      </div>
    </section>
  );
}

function GeneratedGridItem({ item }: { item: GridItem }) {
  const registry = ComponentRegistry.getInstance();
  const ResolvedComponent = registry.resolve(item.componentId) as FC<Record<string, unknown>> | undefined;

  return (
    <div
      className={gridSpanClass(item.span)}
      data-testid={`page-grid-item-${item.key}`}
    >
      {!ResolvedComponent ? (
        <UnknownPageComponent id={item.componentId} />
      ) : (
        <ItemErrorBoundary componentId={item.componentId}>
          {createElement(ResolvedComponent, item.props)}
        </ItemErrorBoundary>
      )}
    </div>
  );
}

function UnknownPageComponent({ id }: { id: string }) {
  return (
    <div className="p-2 text-sm text-red-600 bg-red-50 rounded border border-red-200">
      未知组件: {id}
    </div>
  );
}

function ItemErrorFallback({ componentId }: { componentId: string }) {
  return (
    <div className="p-2 text-sm text-red-600 bg-red-50 rounded border border-red-200">
      组件渲染失败: {componentId}
    </div>
  );
}
```

- [ ] **Step 5: Run the PageRenderer test to verify it passes**

Run:

```bash
cd frontend
npx vitest run src/__tests__/PageRenderer.test.tsx
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add frontend/src/components/page/PageSpec.ts frontend/src/components/page/PageRenderer.tsx frontend/src/__tests__/PageRenderer.test.tsx
git commit -m "feat(frontend): add generated page renderer"
```

Expected: commit succeeds with only the three Task 1 files staged.

---

### Task 2: Frontend TravelPlanner `render_page` Integration

**Files:**
- Modify: `frontend/src/components/TravelPlanner.tsx`
- Test: `frontend/src/__tests__/AGUIRenderer.test.tsx`

- [ ] **Step 1: Add coverage for normalized `componentId` rendering**

Append this test to `frontend/src/__tests__/AGUIRenderer.test.tsx`:

```tsx
it("accepts componentId values after legacy component alias normalization", () => {
  const { result } = renderHook(() => useAGUIRenderer());
  act(() => {
    result.current.render({ componentId: "AliasCard", props: { ok: true }, key: "alias", action: "mount" });
  });
  expect(result.current.items).toEqual([
    {
      id: "alias",
      componentId: "AliasCard",
      props: { ok: true },
    },
  ]);
});
```

- [ ] **Step 2: Run the renderer tests**

Run:

```bash
cd frontend
npx vitest run src/__tests__/AGUIRenderer.test.tsx
```

Expected: PASS. This confirms the hook already accepts normalized `componentId`; the TravelPlanner change will normalize incoming event payloads before calling it.

- [ ] **Step 3: Import PageRenderer and PageSpec in TravelPlanner**

Modify the imports in `frontend/src/components/TravelPlanner.tsx`:

```tsx
import { PageRenderer } from "./page/PageRenderer";
import type { PageSpec } from "./page/PageSpec";
```

- [ ] **Step 4: Add generated page state**

Inside `TravelPlanner`, next to the existing `useState` calls, add:

```tsx
const [currentPage, setCurrentPage] = useState<PageSpec | null>(null);
```

- [ ] **Step 5: Update `RUN_STARTED` lifecycle behavior**

In the `RUN_STARTED` case, keep clearing transient components. Do not clear `currentPage` here, so the previous page remains visible until a new page arrives:

```tsx
case "RUN_STARTED":
  setStatus("thinking");
  openToolCalls.clear();
  clearRendered();
  break;
```

- [ ] **Step 6: Normalize `render_component` component IDs and add `render_page` handling**

Replace the current `case "CUSTOM"` `render_component` branch with this logic while preserving the existing `workflow_output` branch below it:

```tsx
case "CUSTOM": {
  const name = (event.name as string) || "";
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
      const componentId = (value.componentId || value.component) as string;
      handleRenderComponent({
        componentId,
        props: (value.props as Record<string, unknown>) || {},
        key: value.key as string | undefined,
        action: action as "mount" | "update",
      });
    }
  } else if (name === "render_page") {
    setCurrentPage(event.value as PageSpec);
    clearRendered();
  } else if (name === "workflow_output") {
    const value = event.value as any;
    const contents = value?.contents || [];
    for (const content of contents) {
      if (content.type === "function_result" && content.result) {
        const callId = content.call_id;
        const toolName = openToolCalls.get(callId) || "";
        try {
          const result =
            typeof content.result === "string"
              ? JSON.parse(content.result)
              : content.result;
          if (toolName === "get_weather" && result?.city) {
            setItinerary((prev) => ({
              ...prev,
              city: result.city,
              weather: result,
            }));
          } else if (
            toolName === "search_hotels" &&
            Array.isArray(result)
          ) {
            setItinerary((prev) => ({
              ...prev,
              hotels: result,
            }));
          } else if (
            toolName === "search_attractions" &&
            Array.isArray(result)
          ) {
            setItinerary((prev) => ({
              ...prev,
              attractions: result,
            }));
          } else if (toolName === "book_flight" && result?.flight_number) {
            setItinerary((prev) => ({
              ...prev,
              flight: result,
            }));
          }
        } catch {
          // ignore parse errors
        }
        openToolCalls.delete(callId);
      }
    }
    if (openToolCalls.size === 0) {
      setStatus("thinking");
      setActiveTool(null);
    }
  }
  break;
}
```

- [ ] **Step 7: Render the generated page below transient components**

In the left panel, below the existing transient component tree, render `PageRenderer`:

```tsx
<div className="max-h-[40%] overflow-y-auto border-t border-gray-200">
  <AGUIComponentTree items={renderedItems} />
  <PageRenderer page={currentPage} />
</div>
```

- [ ] **Step 8: Run focused frontend tests**

Run:

```bash
cd frontend
npx vitest run src/__tests__/AGUIRenderer.test.tsx src/__tests__/AGUIComponentTree.test.tsx src/__tests__/PageRenderer.test.tsx
```

Expected: PASS.

- [ ] **Step 9: Commit Task 2**

Run:

```bash
git add frontend/src/components/TravelPlanner.tsx frontend/src/__tests__/AGUIRenderer.test.tsx
git commit -m "feat(frontend): handle generated page events"
```

Expected: commit succeeds with only Task 2 files staged.

---

### Task 3: Frontend E2E For `render_page`

**Files:**
- Modify: `frontend/e2e/fixtures/agui-events.ts`
- Create: `frontend/e2e/tests/render-page.spec.ts`

- [ ] **Step 1: Add the failing E2E spec**

Create `frontend/e2e/tests/render-page.spec.ts`:

```ts
import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("generated page rendering", () => {
  test("renders a complete grid page from render_page", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("ProgressBar", { step: 1, total: 2 }, "progress");
      yield agui.renderPage({
        version: "1",
        title: "北京三日旅行方案",
        layout: {
          kind: "grid",
          columns: 12,
          gap: "md",
          items: [
            {
              componentId: "WeatherCard",
              key: "weather",
              span: 4,
              props: {
                city: "北京",
                date: "2026-06-03",
                weather: "晴朗",
                temperature: "28°C",
                humidity: "65%",
              },
            },
            {
              componentId: "HotelList",
              key: "hotels",
              span: 8,
              props: {
                hotels: [
                  {
                    name: "北京湾假日酒店",
                    price: "¥580/晚",
                    rating: 4.6,
                    location: "市中心",
                  },
                ],
              },
            },
            {
              componentId: "AttractionList",
              key: "attractions",
              span: 12,
              props: {
                attractions: [
                  {
                    name: "北京博物馆",
                    type: "文化",
                    rating: 4.6,
                    duration: "3小时",
                    description: "了解当地历史",
                  },
                ],
              },
            },
          ],
        },
      });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("规划北京三日游");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByRole("heading", { name: "北京三日旅行方案" })).toBeVisible();
    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByTestId("rendered-HotelList")).toBeVisible();
    await expect(page.getByTestId("rendered-AttractionList")).toBeVisible();
    await expect(page.getByText("1 / 2")).not.toBeVisible();
  });

  test("renders generated page items full width on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderPage({
        version: "1",
        layout: {
          kind: "grid",
          columns: 12,
          items: [
            {
              componentId: "WeatherCard",
              key: "weather-mobile",
              span: 4,
              props: {
                city: "北京",
                date: "2026-06-03",
                weather: "晴朗",
                temperature: "28°C",
                humidity: "65%",
              },
            },
          ],
        },
      });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("北京天气");
    await page.getByRole("button", { name: "发送" }).click();

    const item = page.getByTestId("page-grid-item-weather-mobile");
    await expect(item).toBeVisible();
    await expect(item).toHaveClass(/col-span-12/);
  });
});
```

- [ ] **Step 2: Run the E2E spec to verify it fails**

Run:

```bash
cd frontend
npx playwright test e2e/tests/render-page.spec.ts --project=chromium
```

Expected: FAIL because `agui.renderPage` does not exist.

- [ ] **Step 3: Add `renderPage` fixture helper**

Modify `frontend/e2e/fixtures/agui-events.ts` and add this method before `runFinished`:

```ts
  renderPage: (page: object) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_page",
      value: page,
    }),
```

- [ ] **Step 4: Run the E2E spec to verify it passes**

Run:

```bash
cd frontend
npx playwright test e2e/tests/render-page.spec.ts --project=chromium
```

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add frontend/e2e/fixtures/agui-events.ts frontend/e2e/tests/render-page.spec.ts
git commit -m "test(e2e): cover generated page rendering"
```

Expected: commit succeeds with only Task 3 files staged.

---

### Task 4: Backend Component Catalog

**Files:**
- Create: `backend/config/components.yaml`
- Create: `backend/src/ui/__init__.py`
- Create: `backend/src/ui/component_catalog.py`
- Create: `backend/tests/test_component_catalog.py`

- [ ] **Step 1: Write failing catalog tests**

Create `backend/tests/test_component_catalog.py`:

```python
from pathlib import Path

from src.ui.component_catalog import load_component_catalog, render_catalog_for_instructions


def test_load_component_catalog_from_yaml():
    catalog = load_component_catalog(Path("config/components.yaml"))

    assert "WeatherCard" in catalog.components
    weather = catalog.components["WeatherCard"]
    assert weather.id == "WeatherCard"
    assert weather.allowed_spans == [3, 4, 6]
    assert weather.preferred_span == 4
    assert weather.props_schema["city"] == "string"


def test_render_catalog_for_instructions_is_compact():
    catalog = load_component_catalog(Path("config/components.yaml"))

    rendered = render_catalog_for_instructions(catalog)

    assert "可用前端组件" in rendered
    assert "WeatherCard" in rendered
    assert "allowedSpans=3,4,6" in rendered
    assert "不要输出 HTML、CSS、JSX" in rendered
```

- [ ] **Step 2: Run the failing catalog tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_component_catalog.py -v
```

Expected: FAIL because `src.ui.component_catalog` does not exist.

- [ ] **Step 3: Add the built-in component catalog**

Create `backend/config/components.yaml`:

```yaml
components:
  WeatherCard:
    id: WeatherCard
    description: 展示单个城市某天的天气
    allowed_spans: [3, 4, 6]
    preferred_span: 4
    props_schema:
      city: string
      date: string
      weather: string
      temperature: string
      humidity: string
    usage_guidance: 适合放在页面顶部或辅助区域，作为旅行规划的天气背景信息。
    example_props:
      city: 北京
      date: "2026-06-03"
      weather: 晴朗
      temperature: "28°C"
      humidity: "60%"

  HotelList:
    id: HotelList
    description: 展示多个酒店推荐
    allowed_spans: [6, 8, 12]
    preferred_span: 8
    props_schema:
      hotels: array
    usage_guidance: 酒店列表通常是主内容，优先使用 8 或 12 栅格宽度。
    example_props:
      hotels:
        - name: 北京湾假日酒店
          price: "¥580/晚"
          rating: 4.6
          location: 市中心

  AttractionList:
    id: AttractionList
    description: 展示多个景点和体验活动推荐
    allowed_spans: [8, 12]
    preferred_span: 12
    props_schema:
      attractions: array
    usage_guidance: 景点列表信息密度较高，通常使用整行或主内容宽度。
    example_props:
      attractions:
        - name: 北京博物馆
          type: 文化
          rating: 4.6
          duration: 3小时
          description: 了解当地历史

  FlightCard:
    id: FlightCard
    description: 展示一次航班预订结果
    allowed_spans: [6, 8, 12]
    preferred_span: 6
    props_schema:
      flight_number: string
      departure: string
      arrival: string
      date: string
      passenger: string
      status: string
      gate: string
      seat: string
    usage_guidance: 航班结果适合放在行程页面顶部或订单确认区域。
    example_props:
      flight_number: CA1234
      departure: 北京
      arrival: 上海
      date: "2026-06-03"
      passenger: 张三
      status: 已确认
      gate: "12"
      seat: 8A

  ProgressBar:
    id: ProgressBar
    description: 展示任务进度，通常用于 transient render_component，不推荐用于最终 render_page
    allowed_spans: [12]
    preferred_span: 12
    props_schema:
      step: number
      total: number
    usage_guidance: 只在规划过程中展示进度；最终页面一般不要使用。
    example_props:
      step: 1
      total: 3
```

- [ ] **Step 4: Add the catalog loader**

Create `backend/src/ui/__init__.py`:

```python
"""Generative UI runtime helpers."""
```

Create `backend/src/ui/component_catalog.py`:

```python
"""Component catalog loading and prompt rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ComponentSpec:
    id: str
    description: str
    allowed_spans: list[int]
    preferred_span: int
    props_schema: dict[str, str]
    usage_guidance: str
    example_props: dict[str, Any]


@dataclass(frozen=True)
class ComponentCatalog:
    components: dict[str, ComponentSpec]


def load_component_catalog(path: Path) -> ComponentCatalog:
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    components: dict[str, ComponentSpec] = {}
    for key, value in (raw.get("components") or {}).items():
        component = ComponentSpec(
            id=str(value.get("id") or key),
            description=str(value.get("description") or ""),
            allowed_spans=[int(span) for span in value.get("allowed_spans", [])],
            preferred_span=int(value.get("preferred_span", 12)),
            props_schema=dict(value.get("props_schema") or {}),
            usage_guidance=str(value.get("usage_guidance") or ""),
            example_props=dict(value.get("example_props") or {}),
        )
        components[component.id] = component

    return ComponentCatalog(components=components)


def render_catalog_for_instructions(catalog: ComponentCatalog) -> str:
    lines = [
        "## 可用前端组件",
        "",
        "你可以通过 render_page 工具请求渲染一个最终页面。",
        "页面只能是 12 栅格 grid，最多 6 个组件。",
        "不要输出 HTML、CSS、JSX、Markdown 或未知组件代码。",
        "",
    ]
    for component in catalog.components.values():
        props = ", ".join(f"{name}:{kind}" for name, kind in component.props_schema.items())
        spans = ",".join(str(span) for span in component.allowed_spans)
        lines.append(
            f"- {component.id}: {component.description}; "
            f"allowedSpans={spans}; preferredSpan={component.preferred_span}; "
            f"props={{{props}}}; guidance={component.usage_guidance}"
        )
    return "\n".join(lines)
```

- [ ] **Step 5: Run catalog tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_component_catalog.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add backend/config/components.yaml backend/src/ui/__init__.py backend/src/ui/component_catalog.py backend/tests/test_component_catalog.py
git commit -m "feat(backend): add component catalog"
```

Expected: commit succeeds with only Task 4 files staged.

---

### Task 5: Backend PageSpec Validation

**Files:**
- Create: `backend/src/ui/page_spec.py`
- Create: `backend/tests/test_page_spec.py`

- [ ] **Step 1: Write failing PageSpec validation tests**

Create `backend/tests/test_page_spec.py`:

```python
import pytest

from src.ui.component_catalog import ComponentCatalog, ComponentSpec
from src.ui.page_spec import PageSpecValidationError, validate_page_spec


def _catalog() -> ComponentCatalog:
    return ComponentCatalog(
        components={
            "WeatherCard": ComponentSpec(
                id="WeatherCard",
                description="Weather",
                allowed_spans=[3, 4, 6],
                preferred_span=4,
                props_schema={"city": "string", "temperature": "string"},
                usage_guidance="Use for weather.",
                example_props={},
            ),
            "HotelList": ComponentSpec(
                id="HotelList",
                description="Hotels",
                allowed_spans=[6, 8, 12],
                preferred_span=8,
                props_schema={"hotels": "array"},
                usage_guidance="Use for hotels.",
                example_props={},
            ),
        }
    )


def test_validate_page_spec_accepts_valid_page():
    page = {
        "version": "1",
        "title": "Trip",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "WeatherCard",
                    "key": "weather",
                    "span": 4,
                    "props": {"city": "北京", "temperature": "28°C"},
                }
            ],
        },
    }

    normalized = validate_page_spec(page, _catalog())

    assert normalized["layout"]["items"][0]["span"] == 4


def test_validate_page_spec_normalizes_invalid_span():
    page = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "WeatherCard",
                    "key": "weather",
                    "span": 8,
                    "props": {"city": "北京", "temperature": "28°C"},
                }
            ],
        },
    }

    normalized = validate_page_spec(page, _catalog())

    assert normalized["layout"]["items"][0]["span"] == 4


def test_validate_page_spec_rejects_unknown_component():
    page = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "UnknownCard",
                    "key": "unknown",
                    "span": 12,
                    "props": {},
                }
            ],
        },
    }

    with pytest.raises(PageSpecValidationError, match="Unknown component"):
        validate_page_spec(page, _catalog())


def test_validate_page_spec_rejects_invalid_props():
    page = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "HotelList",
                    "key": "hotels",
                    "span": 8,
                    "props": {"hotels": "not-an-array"},
                }
            ],
        },
    }

    with pytest.raises(PageSpecValidationError, match="props.hotels"):
        validate_page_spec(page, _catalog())


def test_validate_page_spec_makes_duplicate_keys_unique_and_limits_items():
    items = [
        {
            "componentId": "WeatherCard",
            "key": "same",
            "span": 4,
            "props": {"city": f"城市{idx}", "temperature": "28°C"},
            "importance": "supporting",
        }
        for idx in range(8)
    ]
    page = {"version": "1", "layout": {"kind": "grid", "columns": 12, "items": items}}

    normalized = validate_page_spec(page, _catalog(), max_items=6)

    keys = [item["key"] for item in normalized["layout"]["items"]]
    assert len(keys) == 6
    assert len(set(keys)) == 6
    assert keys[0] == "same"
    assert keys[1] == "same-2"
```

- [ ] **Step 2: Run the failing PageSpec tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_page_spec.py -v
```

Expected: FAIL because `src.ui.page_spec` does not exist.

- [ ] **Step 3: Implement PageSpec validation**

Create `backend/src/ui/page_spec.py`:

```python
"""Validation for generated grid PageSpec payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .component_catalog import ComponentCatalog


class PageSpecValidationError(ValueError):
    """Raised when a generated PageSpec is unsafe or unsupported."""


def validate_page_spec(
    page: dict[str, Any],
    catalog: ComponentCatalog,
    *,
    max_items: int = 6,
) -> dict[str, Any]:
    if page.get("version") != "1":
        raise PageSpecValidationError("Unsupported PageSpec version")

    layout = page.get("layout")
    if not isinstance(layout, dict):
        raise PageSpecValidationError("PageSpec.layout must be an object")
    if layout.get("kind") != "grid":
        raise PageSpecValidationError("Only grid layout is supported")
    if layout.get("columns") != 12:
        raise PageSpecValidationError("Only 12-column grid layout is supported")

    raw_items = layout.get("items")
    if not isinstance(raw_items, list):
        raise PageSpecValidationError("PageSpec.layout.items must be an array")

    normalized_items: list[dict[str, Any]] = []
    seen_keys: dict[str, int] = {}
    for raw_item in raw_items[:max_items]:
        if not isinstance(raw_item, dict):
            raise PageSpecValidationError("Grid item must be an object")

        component_id = str(raw_item.get("componentId") or "")
        component = catalog.components.get(component_id)
        if component is None:
            raise PageSpecValidationError(f"Unknown component: {component_id}")

        props = raw_item.get("props")
        if not isinstance(props, dict):
            raise PageSpecValidationError(f"{component_id}.props must be an object")
        _validate_props(component_id, props, component.props_schema)

        raw_key = str(raw_item.get("key") or component_id)
        key = _unique_key(raw_key, seen_keys)

        raw_span = raw_item.get("span")
        span = int(raw_span) if isinstance(raw_span, int) else component.preferred_span
        if span not in component.allowed_spans:
            span = component.preferred_span

        item: dict[str, Any] = {
            "componentId": component_id,
            "key": key,
            "span": span,
            "props": deepcopy(props),
        }
        if raw_item.get("importance") in {"primary", "secondary", "supporting"}:
            item["importance"] = raw_item["importance"]
        normalized_items.append(item)

    normalized: dict[str, Any] = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": normalized_items,
        },
    }
    if isinstance(page.get("title"), str) and page["title"].strip():
        normalized["title"] = page["title"].strip()
    if layout.get("gap") in {"sm", "md", "lg"}:
        normalized["layout"]["gap"] = layout["gap"]

    return normalized


def _unique_key(key: str, seen_keys: dict[str, int]) -> str:
    count = seen_keys.get(key, 0) + 1
    seen_keys[key] = count
    if count == 1:
        return key
    return f"{key}-{count}"


def _validate_props(component_id: str, props: dict[str, Any], schema: dict[str, str]) -> None:
    for name, kind in schema.items():
        if name not in props:
            raise PageSpecValidationError(f"{component_id}.props.{name} is required")
        value = props[name]
        if kind == "string" and not isinstance(value, str):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be string")
        if kind == "number" and not isinstance(value, int | float):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be number")
        if kind == "array" and not isinstance(value, list):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be array")
        if kind == "object" and not isinstance(value, dict):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be object")
```

- [ ] **Step 4: Run PageSpec tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_page_spec.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

Run:

```bash
git add backend/src/ui/page_spec.py backend/tests/test_page_spec.py
git commit -m "feat(backend): validate generated page specs"
```

Expected: commit succeeds with only Task 5 files staged.

---

### Task 6: Backend Render Page Tool And AG-UI Custom Event Wrapper

**Files:**
- Create: `backend/src/ui/render_page_tool.py`
- Create: `backend/src/ui/agui_runtime.py`
- Modify: `backend/src/workflow.py`
- Modify: `backend/src/main.py`
- Create: `backend/tests/test_agui_page_runtime.py`

- [ ] **Step 1: Write the failing AG-UI wrapper test**

Create `backend/tests/test_agui_page_runtime.py`:

```python
import json

import pytest
from ag_ui.core import CustomEvent, ToolCallResultEvent, ToolCallStartEvent

from src.ui.agui_runtime import AGUIPageRuntime
from src.ui.component_catalog import ComponentCatalog, ComponentSpec
from src.ui.render_page_tool import render_page_marker


class FakeRunner:
    async def run(self, input_data):
        yield ToolCallStartEvent(toolCallId="call_1", toolCallName="render_page")
        yield ToolCallResultEvent(
            messageId="msg_1",
            toolCallId="call_1",
            content=json.dumps(
                render_page_marker(
                    {
                        "version": "1",
                        "layout": {
                            "kind": "grid",
                            "columns": 12,
                            "items": [
                                {
                                    "componentId": "WeatherCard",
                                    "key": "weather",
                                    "span": 4,
                                    "props": {"city": "北京", "temperature": "28°C"},
                                }
                            ],
                        },
                    }
                )
            ),
        )


def _catalog() -> ComponentCatalog:
    return ComponentCatalog(
        components={
            "WeatherCard": ComponentSpec(
                id="WeatherCard",
                description="Weather",
                allowed_spans=[3, 4, 6],
                preferred_span=4,
                props_schema={"city": "string", "temperature": "string"},
                usage_guidance="Use for weather.",
                example_props={},
            )
        }
    )


@pytest.mark.asyncio
async def test_runtime_injects_render_page_custom_event():
    runtime = AGUIPageRuntime(FakeRunner(), catalog=_catalog())

    events = [event async for event in runtime.run({"messages": []})]

    custom_events = [event for event in events if isinstance(event, CustomEvent)]
    assert len(custom_events) == 1
    assert custom_events[0].name == "render_page"
    assert custom_events[0].value["layout"]["items"][0]["componentId"] == "WeatherCard"


@pytest.mark.asyncio
async def test_runtime_keeps_original_tool_events():
    runtime = AGUIPageRuntime(FakeRunner(), catalog=_catalog())

    events = [event async for event in runtime.run({"messages": []})]

    assert isinstance(events[0], ToolCallStartEvent)
    assert isinstance(events[1], ToolCallResultEvent)
```

- [ ] **Step 2: Run the failing wrapper test**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_agui_page_runtime.py -v
```

Expected: FAIL because `src.ui.agui_runtime` and `src.ui.render_page_tool` do not exist.

- [ ] **Step 3: Add the controlled render_page tool**

Create `backend/src/ui/render_page_tool.py`:

```python
"""Controlled render_page tool for agent-requested generated pages."""

from __future__ import annotations

from typing import Any

from agent_framework import tool


RENDER_PAGE_MARKER = "__agui_render_page__"


def render_page_marker(page: dict[str, Any]) -> dict[str, Any]:
    return {
        RENDER_PAGE_MARKER: True,
        "page": page,
    }


def extract_render_page_marker(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict) and value.get(RENDER_PAGE_MARKER) is True:
        page = value.get("page")
        return page if isinstance(page, dict) else None
    return None


@tool(approval_mode="never_require")
def render_page(page: dict) -> dict:
    """请求渲染一个最终生成页面。

    Args:
        page: PageSpec JSON。必须是 version='1'，layout.kind='grid'，columns=12，
            items 最多 6 个。每个 item 必须使用组件目录中的 componentId。
    """
    return render_page_marker(page)
```

- [ ] **Step 4: Add the AG-UI runtime wrapper**

Create `backend/src/ui/agui_runtime.py`:

```python
"""AG-UI runtime wrapper that injects validated render_page CustomEvents."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from ag_ui.core import CustomEvent, ToolCallResultEvent

from .component_catalog import ComponentCatalog
from .page_spec import PageSpecValidationError, validate_page_spec
from .render_page_tool import extract_render_page_marker


class AGUIPageRuntime:
    def __init__(self, runner: Any, *, catalog: ComponentCatalog) -> None:
        self._runner = runner
        self._catalog = catalog

    async def run(self, input_data: dict[str, Any]) -> AsyncGenerator[Any]:
        async for event in self._runner.run(input_data):
            yield event
            custom = self._custom_event_from_tool_result(event)
            if custom is not None:
                yield custom

    def _custom_event_from_tool_result(self, event: Any) -> CustomEvent | None:
        if not isinstance(event, ToolCallResultEvent):
            return None

        try:
            content = json.loads(event.content)
        except json.JSONDecodeError:
            return None

        page = extract_render_page_marker(content)
        if page is None:
            return None

        try:
            normalized = validate_page_spec(page, self._catalog)
        except PageSpecValidationError:
            return None

        return CustomEvent(name="render_page", value=normalized)
```

- [ ] **Step 5: Run the wrapper tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_agui_page_runtime.py -v
```

Expected: PASS.

- [ ] **Step 6: Inject the catalog and render_page tool into workflow instructions**

Modify `backend/src/workflow.py`:

Add imports:

```python
from pathlib import Path

from .ui.component_catalog import load_component_catalog, render_catalog_for_instructions
from .ui.render_page_tool import render_page
```

Add module-level catalog:

```python
COMPONENT_CATALOG_PATH = Path(__file__).resolve().parents[1] / "config" / "components.yaml"
COMPONENT_CATALOG = load_component_catalog(COMPONENT_CATALOG_PATH)
```

In `_build_instructions()`, append the catalog instructions before returning:

```python
        "\n\n"
        + render_catalog_for_instructions(COMPONENT_CATALOG)
```

In `create_travel_workflow()`, add `render_page` to the tools list:

```python
tools=[get_weather, search_hotels, search_attractions, book_flight, render_page],
```

- [ ] **Step 7: Wrap the workflow in main**

Modify `backend/src/main.py`:

Add imports:

```python
from .ui.agui_runtime import AGUIPageRuntime
from .workflow import COMPONENT_CATALOG, create_travel_workflow
```

Replace the existing separate `create_travel_workflow` import if present.

Replace:

```python
travel_agent = create_travel_workflow()
```

with:

```python
travel_agent = AGUIPageRuntime(
    create_travel_workflow(),
    catalog=COMPONENT_CATALOG,
)
```

- [ ] **Step 8: Run backend focused tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_component_catalog.py tests/test_page_spec.py tests/test_agui_page_runtime.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit Task 6**

Run:

```bash
git add backend/src/ui/render_page_tool.py backend/src/ui/agui_runtime.py backend/src/workflow.py backend/src/main.py backend/tests/test_agui_page_runtime.py
git commit -m "feat(backend): emit generated page events"
```

Expected: commit succeeds with only Task 6 files staged.

---

### Task 7: Full Verification

**Files:**
- Verify only; no planned file edits.

- [ ] **Step 1: Run frontend unit tests**

Run:

```bash
cd frontend
npx vitest run
```

Expected: PASS for all Vitest suites.

- [ ] **Step 2: Run frontend E2E tests**

Run:

```bash
cd frontend
npx playwright test --project=chromium
```

Expected: PASS for all Playwright tests.

- [ ] **Step 3: Run backend tests**

Run:

```bash
cd backend
.venv/Scripts/python -m pytest -v
```

Expected: PASS for all backend tests.

- [ ] **Step 4: Run frontend production build**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS with TypeScript and Vite build succeeding.

- [ ] **Step 5: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intentional files changed, or clean if all task commits were made. Do not revert unrelated pre-existing worktree changes.

- [ ] **Step 6: Commit verification notes if any docs changed**

If no files changed during verification, do not commit.

If a small doc update was required, run:

```bash
git add docs/superpowers/plans/2026-06-02-generative-grid-page-runtime.md
git commit -m "docs: update generated page runtime plan"
```

Expected: commit only includes the plan doc if it was intentionally updated.

---

## Self-Review

Spec coverage:

- `render_component` is preserved in Tasks 2 and 3.
- `render_page` protocol is implemented in Tasks 1, 2, 3, 5, and 6.
- Simple 12-column grid `PageSpec` is implemented in Tasks 1 and 5.
- Component catalog is implemented in Task 4.
- Backend validation and normalization are implemented in Task 5.
- Agent instructions and render-page capability are implemented in Task 6.
- Frontend registry-based rendering is implemented in Task 1.
- Runtime lifecycle clearing transient components on `render_page` is implemented in Tasks 2 and 3.
- Unit, backend, and E2E testing are covered in Tasks 1, 3, 4, 5, 6, and 7.

Type consistency:

- Frontend uses `componentId` consistently in `PageSpec.GridItem`.
- `render_component.value.component` remains a legacy alias normalized in `TravelPlanner`.
- Backend catalog uses YAML snake_case and Python dataclass snake_case.
- Backend PageSpec payload keeps frontend-facing camelCase `componentId`.

Known execution note:

- The backend uses a controlled `render_page(page)` tool to let the model request page rendering. The wrapper preserves original tool events and injects a validated `CustomEvent(name="render_page")` after the render-page tool result.
