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
