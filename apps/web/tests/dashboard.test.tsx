import { render, screen } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { expect, test, describe, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MetricCard } from '../components/dashboard/MetricCard';
import { useKpiMetrics } from '../lib/dashboard/useKpiMetrics';
import { apiClient } from '../lib/api/client';
import { KPI_QUESTIONS } from '../lib/dashboard/kpiQuestions';

vi.mock('../lib/api/client', () => ({
  apiClient: {
    askQuestion: vi.fn(),
  }
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('KPI Metrics & MetricCard', () => {
  test('useKpiMetrics fires all canonical questions in parallel', async () => {
    (apiClient.askQuestion as any).mockResolvedValue({ summary: 'test' });
    
    renderHook(() => useKpiMetrics('dataset-123'), { wrapper });
    
    expect(apiClient.askQuestion).toHaveBeenCalledTimes(KPI_QUESTIONS.length);
    KPI_QUESTIONS.forEach(q => {
      expect(apiClient.askQuestion).toHaveBeenCalledWith('dataset-123', q, null);
    });
  });

  test('MetricCard renders gracefully with full payload including delta', () => {
    const mockQuery: any = {
      isLoading: false,
      isError: false,
      data: {
        summary: 'Revenue increased by 10% vs previous period.',
        chart: {
          type: 'line',
          description: 'total revenue this period',
          y_keys: ['revenue'],
          data: [
            { revenue: 150000, delta_percent: 0.10 },
            { revenue: 140000 }
          ]
        }
      }
    };

    render(<MetricCard queryResult={mockQuery} />);
    
    expect(screen.getByText('150,000')).toBeInTheDocument();
    expect(screen.getByText('10.0%')).toBeInTheDocument();
    // Delta text rendered
  });

  test('MetricCard renders gracefully without delta data', () => {
    const mockQuery: any = {
      isLoading: false,
      isError: false,
      data: {
        summary: 'Total orders.',
        chart: {
          type: 'bar',
          description: 'total orders this period',
          y_keys: ['orders'],
          data: [
            { orders: 450 }
          ] // no delta_percent
        }
      }
    };

    render(<MetricCard queryResult={mockQuery} />);
    
    expect(screen.getByText('450')).toBeInTheDocument();
    expect(screen.getByText('No delta')).toBeInTheDocument();
  });

  test('MetricCard partial failure handles gracefully', () => {
    const mockQuery: any = {
      isLoading: false,
      isError: true, // simulates failed LLM
      data: undefined
    };

    render(<MetricCard queryResult={mockQuery} />);
    expect(screen.getByText('Metric unavailable')).toBeInTheDocument();
  });
});
