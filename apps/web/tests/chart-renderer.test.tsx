import { render, screen } from '@testing-library/react';
import { expect, test, describe, vi } from 'vitest';
import { ChartRenderer } from '../components/charts/ChartRenderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock Zustand store so getCategoryColor is available
vi.mock('../lib/store/useAppStore', () => ({
  useAppStore: (selector: any) => selector({
    getCategoryColor: () => 'var(--color-chart-1)'
  })
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('ChartRenderer', () => {
  test('renders truncation note honestly when meta.truncated is true', () => {
    const payload = {
      type: 'line',
      title: 'Test Line',
      y_keys: ['val'],
      x_key: 'date',
      meta: { truncated: true, original_row_count: 500 },
      data: [{ date: '2023', val: 10 }, { date: '2024', val: 20 }]
    };
    render(<ChartRenderer payload={payload} />, { wrapper });
    expect(screen.getByText('Showing 2 of 500 data points')).toBeInTheDocument();
  });

  test('does not render truncation note when meta.truncated is false', () => {
    const payload = {
      type: 'line',
      title: 'Test Line',
      y_keys: ['val'],
      x_key: 'date',
      meta: { truncated: false, original_row_count: 2 },
      data: [{ date: '2023', val: 10 }, { date: '2024', val: 20 }]
    };
    render(<ChartRenderer payload={payload} />, { wrapper });
    expect(screen.queryByText(/Showing/)).not.toBeInTheDocument();
  });

  test('renders unsupported chart type gracefully', () => {
    const payload = {
      type: 'unknown_chart',
      title: 'Test',
      meta: {},
      data: [{ val: 10 }]
    };
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    render(<ChartRenderer payload={payload} />, { wrapper });
    
    expect(screen.getByText('Unsupported Chart Type')).toBeInTheDocument();
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('[known-issues] ChartRenderer encountered an unsupported chart type: unknown_chart'));
    consoleSpy.mockRestore();
  });

  test('renders empty data gracefully', () => {
    const payload = {
      type: 'line',
      title: 'Test',
      meta: {},
      data: []
    };
    render(<ChartRenderer payload={payload} />, { wrapper });
    expect(screen.getByText('No Data Available')).toBeInTheDocument();
  });

  // Verify routing for basic types
  const typesToTest = ['line', 'multi_line', 'bar', 'stacked_bar', 'donut', 'scatter', 'metric_card'];
  for (const type of typesToTest) {
    test(`renders sub-component for type: ${type}`, () => {
      const payload = {
        type,
        title: `Test ${type}`,
        y_keys: ['val'],
        x_key: 'x',
        meta: {},
        data: [{ x: 'a', val: 10 }, { x: 'b', val: 20 }]
      };
      
      const { container } = render(<ChartRenderer payload={payload} />, { wrapper });
      // We don't assert the exact Recharts internals (which are hard to test in JSDOM), 
      // but we assert the wrapper Card and title are present.
      if (type === 'metric_card') {
        expect(container.querySelector('[data-testid="metric-card"]')).toBeInTheDocument();
      } else {
        expect(screen.getByText(`Test ${type}`)).toBeInTheDocument();
      }
    });
  }
});
