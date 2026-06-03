import { useState, useCallback } from 'react';
import { ComponentRegistry } from '../generative-ui/ComponentRegistry';

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

export function AGUIComponentTree({ items }: { items: RenderedItem[] }) {
  const registry = ComponentRegistry.getInstance();

  return (
    <div className="agui-rendered-components p-2">
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
  return <div className="unknown-component p-2 text-sm text-red-600 bg-red-50 rounded border border-red-200">未知组件: {id}</div>;
}
