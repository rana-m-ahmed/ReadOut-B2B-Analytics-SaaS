"use client"

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, ReactNode } from 'react'
import { queryKeys } from '../../lib/api/queryKeys'

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => {
    const client = new QueryClient({
      defaultOptions: {
        queries: {
          // Explicit "don't refetch and burn quota on tab focus" rule
          refetchOnWindowFocus: false,
          // Default staleTime for anything unconfigured
          staleTime: 60 * 1000, 
        },
      },
    })

    // ~5min for datasets/schema, as they rarely change outside explicit user actions
    client.setQueryDefaults(queryKeys.datasets.all, {
      staleTime: 5 * 60 * 1000,
    })

    // ~60s for ask-adjacent data
    client.setQueryDefaults(queryKeys.ask.all, {
      staleTime: 60 * 1000,
    })

    // ~60s for analytics results
    client.setQueryDefaults(queryKeys.widgets.all, {
      staleTime: 60 * 1000,
    })
    client.setQueryDefaults(queryKeys.insights.all, {
      staleTime: 60 * 1000,
    })
    client.setQueryDefaults(queryKeys.anomalies.all, {
      staleTime: 60 * 1000,
    })

    return client
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
