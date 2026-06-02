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
