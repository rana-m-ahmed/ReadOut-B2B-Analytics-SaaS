import { useQueries } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { KPI_QUESTIONS } from './kpiQuestions';

export function useKpiMetrics(datasetId: string | null) {
  return useQueries({
    queries: KPI_QUESTIONS.map((question) => ({
      queryKey: ['kpi', datasetId, question],
      queryFn: () => apiClient.askQuestion(datasetId!, question, null),
      enabled: !!datasetId,
      staleTime: 5 * 60 * 1000, // 5 minutes cache
      retry: 1, // Minimize aggressive retries on LLM failures
    }))
  });
}
