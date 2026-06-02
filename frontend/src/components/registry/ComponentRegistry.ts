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
