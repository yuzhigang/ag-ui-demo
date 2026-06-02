export type GridSpan = 3 | 4 | 6 | 8 | 12;
export type GridGap = 'sm' | 'md' | 'lg';
export type GridImportance = 'primary' | 'secondary' | 'supporting';

export interface PageSpec {
  title?: string;
  layout: GridLayout;
}

export interface GridLayout {
  gap?: unknown;
  items: GridItem[];
}

export interface GridItem {
  key: string;
  componentId: string;
  span?: unknown;
  importance?: GridImportance;
  props?: Record<string, unknown>;
}

export const VALID_GRID_SPANS = [3, 4, 6, 8, 12] as const;

export function normalizeGridSpan(span: unknown): GridSpan {
  return VALID_GRID_SPANS.includes(span as GridSpan) ? (span as GridSpan) : 12;
}

export function gridSpanClass(span: unknown): string {
  return `col-span-12 md:col-span-${normalizeGridSpan(span)}`;
}

export function gridGapClass(gap: unknown): string {
  if (gap === 'sm') {
    return 'gap-2';
  }

  if (gap === 'lg') {
    return 'gap-6';
  }

  return 'gap-4';
}
