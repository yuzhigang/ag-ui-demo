# Generative Grid Page Runtime Design

## Goal

Build a controlled generative UI runtime where an agent can return a complete page made of multiple registered frontend components. The first version should render a simple 12-column grid page, not arbitrary HTML, CSS, JSX, or nested layout structures.

The runtime must support two UI event levels:

- `render_component` for transient, incremental, or local UI updates.
- `render_page` for final, whole-page UI output that replaces the current generated page.

The key product rule is: multiple `render_component` events are not treated as a page. A complete page must be expressed as one `render_page` event containing a validated `PageSpec`.

## Background

Single-component generative UI is useful for cards, progress indicators, confirmation panels, or immediate tool results. It becomes ambiguous when the agent needs to produce a coherent page composed from several components. The frontend cannot reliably infer whether a stream of individual component events is one page, several intermediate previews, or unrelated UI updates.

This design introduces a first-class page description object. The agent can design a component collection and layout, while the backend and frontend keep rendering safe by restricting the output to a small layout DSL and a known component catalog.

## Scope

In scope:

- A `PageSpec` schema for one 12-column grid.
- A `ComponentCatalog` that describes available components, props, and layout hints.
- Agent instructions that teach the model how to produce valid grid pages.
- Backend validation and normalization of generated page specs.
- Frontend rendering of validated page specs with registered React components.
- Continued support for `render_component`.

Out of scope for the first version:

- Nested layouts.
- Tabs, sidebars, accordions, modals, or freeform sections.
- Agent-generated CSS, HTML, JSX, or remote component code.
- Arbitrary grid column counts.
- Runtime installation or loading of unknown frontend components.

## Protocol

### `render_component`

`render_component` remains available for single-component rendering.

Use it for:

- Progress indicators.
- Loading states.
- Approval or confirmation panels.
- Single tool-result previews.
- Mounting, updating, or unmounting a local component.

Example:

```json
{
  "type": "CUSTOM",
  "name": "render_component",
  "value": {
    "componentId": "ProgressBar",
    "key": "planning-progress",
    "action": "mount",
    "props": {
      "step": 1,
      "total": 3
    }
  }
}
```

For compatibility with the existing demo code, `render_component.value.component` may be accepted as a legacy alias for `render_component.value.componentId`. New code should prefer `componentId` because it matches `PageSpec.GridItem.componentId`.

### `render_page`

`render_page` represents a complete generated page. Receiving it replaces the current generated page.

Example:

```json
{
  "type": "CUSTOM",
  "name": "render_page",
  "value": {
    "version": "1",
    "title": "北京三日旅行方案",
    "layout": {
      "kind": "grid",
      "columns": 12,
      "gap": "md",
      "items": [
        {
          "componentId": "WeatherCard",
          "key": "weather-beijing",
          "span": 4,
          "importance": "supporting",
          "props": {
            "city": "北京",
            "date": "2026-06-03",
            "weather": "晴朗",
            "temperature": "28°C",
            "humidity": "60%"
          }
        },
        {
          "componentId": "HotelList",
          "key": "hotels-beijing",
          "span": 8,
          "importance": "primary",
          "props": {
            "hotels": []
          }
        },
        {
          "componentId": "AttractionList",
          "key": "attractions-beijing",
          "span": 12,
          "importance": "primary",
          "props": {
            "attractions": []
          }
        }
      ]
    }
  }
}
```

## PageSpec Schema

The first version supports only a simple 12-column grid.

```ts
type PageSpec = {
  version: "1";
  title?: string;
  layout: GridLayout;
};

type GridLayout = {
  kind: "grid";
  columns: 12;
  gap?: "sm" | "md" | "lg";
  items: GridItem[];
};

type GridItem = {
  componentId: string;
  key: string;
  span: 3 | 4 | 6 | 8 | 12;
  props: Record<string, unknown>;
  importance?: "primary" | "secondary" | "supporting";
};
```

Allowed spans:

- `3`: four small cards per row.
- `4`: three cards per row.
- `6`: two half-width cards per row.
- `8`: wide primary content.
- `12`: full-width content.

The frontend renders all grid items as full-width items on small screens.

## Component Catalog

The backend needs a catalog that describes the frontend components available to the agent. This catalog is the agent-facing representation of UI capability. It does not include React implementation details.

Each component entry should include:

- `id`: stable component ID used in `PageSpec`.
- `description`: when this component should be used.
- `propsSchema`: expected props shape.
- `allowedSpans`: spans the component may use.
- `preferredSpan`: default span if the agent chooses an invalid span.
- `usageGuidance`: short rules for correct use.
- `exampleProps`: representative props for prompting and testing.

Example:

```json
{
  "id": "WeatherCard",
  "description": "展示单个城市某天的天气",
  "allowedSpans": [3, 4, 6],
  "preferredSpan": 4,
  "propsSchema": {
    "city": "string",
    "date": "string",
    "weather": "string",
    "temperature": "string",
    "humidity": "string"
  },
  "usageGuidance": "适合放在页面顶部或侧边，作为旅行规划的辅助信息。",
  "exampleProps": {
    "city": "北京",
    "date": "2026-06-03",
    "weather": "晴朗",
    "temperature": "28°C",
    "humidity": "60%"
  }
}
```

## Agent Behavior

The agent is responsible for page intent:

1. Understand the user's goal.
2. Call business tools to collect structured data.
3. Use the component catalog to select appropriate components.
4. Assign grid spans based on component importance and catalog hints.
5. Output one `render_page` event for the final page.

The agent must not:

- Output HTML, CSS, JSX, or script.
- Use component IDs that are not in the catalog.
- Use spans outside the component's `allowedSpans`.
- Produce more than the configured maximum number of page items.
- Treat multiple `render_component` events as the final page.

Suggested instruction summary:

```text
You can render a final generated page by producing a render_page PageSpec.
Only use components listed in the component catalog.
Use a single 12-column grid.
Each item must have a unique key, valid componentId, valid props, and an allowed span.
Use at most 6 components.
Use render_component only for transient UI; use render_page for the final composed page.
Do not output HTML, CSS, JSX, Markdown, or unknown component code.
```

## Backend Responsibilities

The backend is the trust boundary.

It should:

- Load the component catalog.
- Inject a compact catalog summary into agent instructions.
- Accept or create a `PageSpec`.
- Validate `componentId` against the catalog.
- Validate `props` against each component's props schema.
- Validate `span` against each component's `allowedSpans`.
- Normalize invalid spans to `preferredSpan` when safe.
- Ensure each item has a unique key.
- Enforce a maximum item count, initially 6.
- Reject unsupported layout kinds.
- Emit a `CUSTOM` `render_page` event only after validation.

Validation should be deterministic. The model may propose a layout, but the backend decides what is safe to send.

## Frontend Responsibilities

The frontend should:

- Keep the existing component registry for React component resolution.
- Continue handling `render_component`.
- Add a `PageRenderer` for `render_page`.
- Render a 12-column grid on desktop.
- Render every item as full width on small screens.
- Resolve every `componentId` through the registry.
- Show a fallback for unknown components.
- Use a safe default span if the incoming value is invalid.

The frontend is a final safety net, not the primary validator.

## Runtime Lifecycle

Recommended event flow:

```text
RUN_STARTED
  clear transient render_component items

render_component ProgressBar
  optional progress UI

business tool calls
  collect weather, hotel, attraction, flight, or other structured data

render_component preview components
  optional immediate feedback

render_page
  replace current generated page with validated PageSpec
  optionally clear transient components

RUN_FINISHED
  finish text and state updates
```

On `RUN_STARTED`, the frontend should clear transient components. It may keep the previous generated page visible until a new `render_page` arrives, depending on product preference.

On `render_page`, the frontend should replace `currentPage`. The default behavior should clear transient components to avoid duplicated previews and final results.

## Error Handling

Backend handling:

- Unknown component: remove the item or replace with a known fallback item.
- Invalid props: remove the item unless a safe default can be derived.
- Invalid span: normalize to `preferredSpan`.
- Duplicate key: append a stable suffix.
- Too many items: keep the highest-priority items first, then preserve order.
- Unsupported layout: reject the page and emit a structured error event.

Frontend handling:

- Unknown component after validation: render `UnknownComponent`.
- Invalid span after validation: use full-width span `12`.
- Component render failure: isolate the failure to that item and show an item-level error fallback.

## Testing Strategy

Unit tests:

- Validate `PageSpec` schema.
- Normalize invalid spans.
- Reject unknown components.
- Enforce maximum item count.
- Ensure duplicate keys are made unique.
- Render registered page items.
- Show fallback for unknown page items.

Integration tests:

- Agent/tool result produces a valid `render_page`.
- `render_page` replaces the current page.
- `render_component` still works for transient UI.
- Receiving `render_page` clears transient components.

E2E tests:

- Mock AG-UI SSE stream sends `render_page` with three components.
- Frontend renders the grid and expected component content.
- Mobile viewport renders all components full-width.
- Invalid page payload does not crash the UI.

## First Version Constraints

The first version should keep these hard constraints:

- One layout kind: `grid`.
- Fixed `columns: 12`.
- Maximum 6 components per page.
- Allowed spans: `3`, `4`, `6`, `8`, `12`.
- No nested layout.
- No freeform CSS.
- No remote component code.
- No unknown component rendering beyond fallback.

These constraints preserve the core demo value while keeping the runtime predictable.

## Future Extensions

After the grid runtime is stable, possible extensions include:

- `dataRef` items where the agent plans layout and the backend fills props from state.
- Additional layout primitives such as `section`, `tabs`, `sidebar`, or `stack`.
- Richer layout hints such as density, height, or responsive preference.
- Page diff/update events instead of full replacement.
- User-editable generated pages.
- Component-level permission rules for sensitive actions.

The first version should not implement these extensions, but the `PageSpec` version field leaves room for them.
