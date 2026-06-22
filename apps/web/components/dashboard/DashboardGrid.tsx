"use client";

import { useKpiMetrics } from "../../lib/dashboard/useKpiMetrics";
import { MetricCard } from "./MetricCard";
import { Card } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { Database, AlertTriangle } from "lucide-react";
import { Button } from "../ui/button";
import { useRouter } from "next/navigation";

interface DashboardGridProps {
  datasetId: string | null;
}

export function DashboardGrid({ datasetId }: DashboardGridProps) {
  const kpiQueries = useKpiMetrics(datasetId);
  const router = useRouter();

  // 1. Empty State
  if (!datasetId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center" data-testid="dashboard-empty">
        <div className="bg-[var(--surface-subtle)] p-6 rounded-full mb-6 text-[var(--ink-secondary)]">
          <Database size={48} />
        </div>
        <h2 className="text-3xl font-bold text-[var(--ink)] mb-3">No Data Connected</h2>
        <p className="text-[var(--ink-secondary)] max-w-md mb-8">
          Connect your first dataset to start analyzing and generating insights automatically.
        </p>
        <div className="flex gap-4">
          <Button onClick={() => router.push('/connect-data')} size="lg">Upload CSV</Button>
          <Button onClick={() => router.push('/data-sources')} variant="outline" size="lg">Browse Sources</Button>
        </div>
      </div>
    );
  }

  const isLoading = kpiQueries.some(q => q.isLoading);
  const isError = kpiQueries.every(q => q.isError);

  // 2. Loading State
  if (isLoading) {
    return (
      <div className="flex flex-col gap-6" data-testid="dashboard-loading">
        {/* KPI Skeletons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i} className="p-4 flex flex-col gap-3 min-h-[140px] border-[var(--hairline)]">
              <Skeleton className="h-4 w-24 rounded" />
              <Skeleton className="h-8 w-32 rounded" />
              <Skeleton className="h-12 w-full rounded" />
            </Card>
          ))}
        </div>
        {/* Main Masonry Grid Skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          <Skeleton className="widget-lg rounded-xl" />
          <Skeleton className="col-span-1 row-span-2 min-h-[400px] rounded-xl" />
        </div>
      </div>
    );
  }

  // 3. Error State (All failed)
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center" data-testid="dashboard-error">
        <AlertTriangle size={48} className="text-[var(--danger)] mb-4" />
        <h3 className="text-xl font-bold text-[var(--ink)] mb-2">Failed to load overview</h3>
        <p className="text-[var(--ink-secondary)]">There was a problem querying the analytical engine.</p>
        <Button onClick={() => window.location.reload()} variant="outline" className="mt-6">Retry</Button>
      </div>
    );
  }

  // 4. Populated State
  return (
    <div className="flex flex-col gap-6" data-testid="dashboard-populated">
      {/* KPI Row (Auto-fit or explicitly 5 cols) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {kpiQueries.map((query, i) => (
          <MetricCard key={i} queryResult={query} />
        ))}
      </div>

      {/* Main Masonry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        
        {/* Hero Chart Scaffold */}
        <Card className="widget-lg p-6 flex flex-col justify-between overflow-hidden relative border-[var(--hairline)] shadow-sm bg-[var(--surface)]">
          <div className="z-10 relative">
            <h3 className="text-xl font-bold text-[var(--ink)]">Primary Trend</h3>
            <p className="text-sm text-[var(--ink-secondary)] mt-1">Overall performance vs previous period</p>
          </div>
          
          {/* Faux Smooth Curve */}
          <div className="absolute bottom-0 left-0 right-0 h-2/3 pointer-events-none opacity-20 dark:opacity-40">
            <svg viewBox="0 0 1000 400" preserveAspectRatio="none" className="w-full h-full text-[var(--accent)] fill-current">
              <path d="M0,400 C200,300 300,100 500,200 C700,300 800,50 1000,150 L1000,400 Z" />
            </svg>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-2/3 pointer-events-none opacity-50">
            <svg viewBox="0 0 1000 400" preserveAspectRatio="none" className="w-full h-full stroke-[var(--accent)] stroke-[4px] fill-transparent">
              <path d="M0,400 C200,300 300,100 500,200 C700,300 800,50 1000,150" />
            </svg>
          </div>
          
          <div className="z-10 text-xs font-mono text-[var(--ink-secondary)]/50 uppercase tracking-widest text-right mt-auto">
            Interactive chart rendering in Phase 20
          </div>
        </Card>

        {/* Insight Panel Scaffold */}
        <Card className="col-span-1 row-span-2 min-h-[400px] p-6 border-[var(--hairline)] shadow-sm bg-[var(--surface-subtle)]/30 flex flex-col">
          <h3 className="text-lg font-bold text-[var(--ink)] mb-4">Insights & Anomalies</h3>
          <div className="flex-1 border-2 border-dashed border-[var(--hairline)] rounded-lg flex items-center justify-center text-[var(--ink-secondary)]/60 text-sm text-center p-4">
            Automated insight panel<br/>(Phase 19)
          </div>
        </Card>

        {/* Pinned Widgets Scaffold */}
        <Card className="widget-md p-6 border-[var(--hairline)] shadow-sm flex flex-col justify-center items-center text-center text-[var(--ink-secondary)]/60 bg-[var(--surface-subtle)]/10 border-dashed border-2">
          <p className="text-sm">Pinned widgets area</p>
          <span className="text-xs uppercase tracking-widest mt-2">Phase 20</span>
        </Card>

        <Card className="widget-sm p-6 border-[var(--hairline)] shadow-sm flex flex-col justify-center items-center text-center text-[var(--ink-secondary)]/60 bg-[var(--surface-subtle)]/10 border-dashed border-2">
           <p className="text-sm">Small widget</p>
        </Card>

      </div>
    </div>
  );
}
