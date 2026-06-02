import { Component, createElement, type ErrorInfo, type ReactNode } from 'react';
import { ComponentRegistry } from '../registry/ComponentRegistry';
import { gridGapClass, gridSpanClass, type GridItem, type PageSpec } from './PageSpec';

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
    <ItemErrorBoundary componentId={item.componentId}>
      {createElement(ComponentToRender, item.props ?? {})}
    </ItemErrorBoundary>
  );
}

export function PageRenderer({ page }: { page: PageSpec | null }) {
  if (!page) {
    return null;
  }

  return (
    <section data-testid="generated-page">
      {page.title ? <h2>{page.title}</h2> : null}
      <div
        data-testid="generated-page-grid"
        className={`grid grid-cols-12 ${gridGapClass(page.layout.gap)}`}
      >
        {page.layout.items.map((item) => (
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
