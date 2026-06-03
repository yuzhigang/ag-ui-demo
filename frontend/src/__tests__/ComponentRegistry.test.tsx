import { describe, it, expect, beforeEach } from 'vitest';
import { ComponentRegistry, registerComponent } from '../components/generated-ui/component-registry/ComponentRegistry';

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
  beforeEach(() => {
    ComponentRegistry.getInstance().clear();
  });

  it('registers via helper function', () => {
    registerComponent('HelperTest', TestComponent);
    expect(ComponentRegistry.getInstance().resolve('HelperTest')).toBe(TestComponent);
  });
});
