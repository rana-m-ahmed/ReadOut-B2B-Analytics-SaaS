import { render, screen, fireEvent } from '@testing-library/react';
import { expect, test, describe, vi } from 'vitest';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useKpiMetrics } from '../lib/dashboard/useKpiMetrics';

vi.mock('../lib/dashboard/useKpiMetrics', () => ({
  useKpiMetrics: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() })
}));

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('DashboardGrid Layout', () => {
  test('Renders Empty State correctly when datasetId is null', () => {
    (useKpiMetrics as any).mockReturnValue([]);
    render(<DashboardGrid datasetId={null} />, { wrapper });
    
    expect(screen.getByTestId('dashboard-empty')).toBeInTheDocument();
    expect(screen.getByText('No Data Connected')).toBeInTheDocument();
  });

  test('Renders Loading State with skeletons when queries are loading', () => {
    (useKpiMetrics as any).mockReturnValue([{ isLoading: true, isError: false }]);
    render(<DashboardGrid datasetId="dataset-123" />, { wrapper });
    
    expect(screen.getByTestId('dashboard-loading')).toBeInTheDocument();
    // Verify a skeleton with widget-lg class exists
    const widgetLgSkeletons = document.querySelectorAll('.widget-lg');
    expect(widgetLgSkeletons.length).toBeGreaterThan(0);
  });

  test('Renders Error State when queries fail', () => {
    (useKpiMetrics as any).mockReturnValue([{ isLoading: false, isError: true }]);
    render(<DashboardGrid datasetId="dataset-123" />, { wrapper });
    
    expect(screen.getByTestId('dashboard-error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load overview')).toBeInTheDocument();
  });

  test('Renders Populated State and scaffold layout grid', () => {
    (useKpiMetrics as any).mockReturnValue([{ 
      isLoading: false, 
      isError: false,
      data: {
        summary: 'ok',
        chart: { type: 'line', data: [{ value: 100 }] }
      }
    }]);

    render(<DashboardGrid datasetId="dataset-123" />, { wrapper });
    
    expect(screen.getByTestId('dashboard-populated')).toBeInTheDocument();
    expect(screen.getByText('Primary Trend')).toBeInTheDocument();
    expect(screen.getByText('Insights & Anomalies')).toBeInTheDocument();
    expect(screen.getByText('Pinned widgets area')).toBeInTheDocument();
    
    // Assert widget sizing tokens are present
    expect(document.querySelector('.widget-lg')).toBeInTheDocument();
    expect(document.querySelector('.widget-md')).toBeInTheDocument();
    expect(document.querySelector('.widget-sm')).toBeInTheDocument();
  });
});
