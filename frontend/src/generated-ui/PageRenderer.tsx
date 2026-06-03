import { Component, createElement, type ErrorInfo, type ReactNode } from 'react';
import { ComponentRegistry } from './ComponentRegistry';
import { gridGapClass, gridSpanClass, type GridItem, type PageDocument } from './PageDocument';

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

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return <>组件渲染失败: {this.props.componentId}</>;
    }

    return this.props.children;
  }
}

function renderGridItem(item: GridItem): ReactNode {
  const ComponentToRender = ComponentRegistry.getInstance().resolve(item.componentId);

  if (!ComponentToRender) {
    return <>未知组件: {item.componentId}</>;
  }

  return (
    <ItemErrorBoundary
      key={`${item.key}:${item.componentId}:${stableSerialize(item.props ?? {})}`}
      componentId={item.componentId}
    >
      {createElement(ComponentToRender, item.props ?? {})}
    </ItemErrorBoundary>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function stableSerialize(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableSerialize).join(',')}]`;
  }

  if (isRecord(value)) {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`)
      .join(',')}}`;
  }

  return JSON.stringify(value);
}

function normalizeGridItem(item: unknown): GridItem | null {
  if (!isRecord(item) || typeof item.key !== 'string' || typeof item.componentId !== 'string') {
    return null;
  }

  return {
    key: item.key,
    componentId: item.componentId,
    span: item.span,
    importance: item.importance as GridItem['importance'],
    props: isRecord(item.props) ? item.props : undefined,
  };
}

function safeLayout(page: PageDocument): { gap: unknown; items: GridItem[] } {
  if (!isRecord(page.layout)) {
    return { gap: undefined, items: [] };
  }

  return {
    gap: page.layout.gap,
    items: Array.isArray(page.layout.items)
      ? page.layout.items.flatMap((item) => {
          const normalized = normalizeGridItem(item);
          return normalized ? [normalized] : [];
        })
      : [],
  };
}

export function PageRenderer({ page }: { page: PageDocument | null }) {
  if (!isRecord(page)) {
    return null;
  }

  const layout = safeLayout(page);

  return (
    <section data-testid="generated-page">
      {page.title ? <h2>{page.title}</h2> : null}
      <div
        data-testid="generated-page-grid"
        className={`grid grid-cols-12 ${gridGapClass(layout.gap)}`}
      >
        {layout.items.map((item) => (
          <div
            key={item.key}
            data-testid={`page-grid-item-${item.key}`}
            className={gridSpanClass(item.span)}
          >
            {renderGridItem(item)}
          </div>
        ))}
      </div>
    </section>
  );
}
