export const queryKeys = {
  datasets: {
    all: ['datasets'] as const,
    list: () => [...queryKeys.datasets.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.datasets.all, 'detail', id] as const,
    schema: (id: string) => [...queryKeys.datasets.all, 'schema', id] as const,
  },
  ask: {
    all: ['ask'] as const,
    session: (id: string) => [...queryKeys.ask.all, 'session', id] as const,
  },
  widgets: {
    all: ['widgets'] as const,
    list: (dashboardId: string) => [...queryKeys.widgets.all, 'list', dashboardId] as const,
  },
  insights: {
    all: ['insights'] as const,
    list: (datasetId: string) => [...queryKeys.insights.all, 'list', datasetId] as const,
  },
  anomalies: {
    all: ['anomalies'] as const,
    list: (datasetId: string) => [...queryKeys.anomalies.all, 'list', datasetId] as const,
  },
}
