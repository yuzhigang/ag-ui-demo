import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ComponentRegistry } from "../components/registry/ComponentRegistry";
import { PageRenderer } from "../components/page/PageRenderer";
import type { PageSpec } from "../components/page/PageSpec";

function TestCard({ label }: { label: string }) {
  return <article>{label}</article>;
}

function ExplodingCard(): ReactElement {
  throw new Error('render failed');
}

describe('PageRenderer', () => {
  beforeEach(() => {
    ComponentRegistry.getInstance().clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders page title and two registered TestCard grid items', () => {
    ComponentRegistry.getInstance().register('TestCard', TestCard);

    const page: PageSpec = {
      title: 'Generated Trip',
      layout: {
        gap: 'md',
        items: [
          { key: 'first', componentId: 'TestCard', span: 6, props: { label: 'First card' } },
          { key: 'second', componentId: 'TestCard', span: 6, props: { label: 'Second card' } },
        ],
      },
    };

    render(<PageRenderer page={page} />);

    expect(screen.getByRole('heading', { name: 'Generated Trip', level: 2 })).toBeInTheDocument();
    expect(screen.getByTestId('page-grid-item-first')).toHaveTextContent('First card');
    expect(screen.getByTestId('page-grid-item-second')).toHaveTextContent('Second card');
  });

  it('renders unknown component fallback text', () => {
    const page: PageSpec = {
      layout: {
        items: [{ key: 'missing', componentId: 'MissingCard', props: {} }],
      },
    };

    render(<PageRenderer page={page} />);

    expect(screen.getByText('未知组件: MissingCard')).toBeInTheDocument();
  });

  it('falls back invalid span 5 to md:col-span-12', () => {
    ComponentRegistry.getInstance().register('TestCard', TestCard);

    const page: PageSpec = {
      layout: {
        items: [
          { key: 'bad-span', componentId: 'TestCard', span: 5, props: { label: 'Bad span' } },
        ],
      },
    };

    render(<PageRenderer page={page} />);

    expect(screen.getByTestId('page-grid-item-bad-span')).toHaveClass('md:col-span-12');
  });

  it('isolates component render failure and shows fallback text', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const preventExpectedError = (event: ErrorEvent) => event.preventDefault();
    window.addEventListener('error', preventExpectedError);
    ComponentRegistry.getInstance().register('ExplodingCard', ExplodingCard);

    const page: PageSpec = {
      layout: {
        items: [{ key: 'exploding', componentId: 'ExplodingCard', props: {} }],
      },
    };

    try {
      render(<PageRenderer page={page} />);
    } finally {
      window.removeEventListener('error', preventExpectedError);
    }

    expect(screen.getByText('组件渲染失败: ExplodingCard')).toBeInTheDocument();
  });

  it('renders an empty grid for malformed layout data', () => {
    const malformedPage = {
      title: 'Malformed Page',
      layout: {
        items: 'not-items',
      },
    } as unknown as PageSpec;

    render(<PageRenderer page={malformedPage} />);

    expect(screen.getByTestId('generated-page')).toBeInTheDocument();
    expect(screen.getByTestId('generated-page-grid')).toBeInTheDocument();
    expect(screen.queryByTestId(/^page-grid-item-/)).not.toBeInTheDocument();
  });

  it('recovers when an item key is reused with a different component', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const preventExpectedError = (event: ErrorEvent) => event.preventDefault();
    window.addEventListener('error', preventExpectedError);
    ComponentRegistry.getInstance().register('ExplodingCard', ExplodingCard);
    ComponentRegistry.getInstance().register('TestCard', TestCard);

    const { rerender } = render(
      <PageRenderer
        page={{
          layout: {
            items: [{ key: 'reused', componentId: 'ExplodingCard', props: {} }],
          },
        }}
      />,
    );
    window.removeEventListener('error', preventExpectedError);

    rerender(
      <PageRenderer
        page={{
          layout: {
            items: [
              { key: 'reused', componentId: 'TestCard', props: { label: 'Recovered card' } },
            ],
          },
        }}
      />,
    );

    expect(screen.getByTestId('page-grid-item-reused')).toHaveTextContent('Recovered card');
  });
});
