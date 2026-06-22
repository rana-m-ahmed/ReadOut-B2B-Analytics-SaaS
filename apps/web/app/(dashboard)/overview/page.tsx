"use client";

import { useAppStore } from "../../../lib/store/useAppStore";
import { DashboardGrid } from "../../../components/dashboard/DashboardGrid";

export default function OverviewPage() { 
  const activeDatasetId = useAppStore(state => state.activeDatasetId);
  
  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--ink)]">Overview</h1>
        <p className="text-[var(--ink-secondary)] mt-1">Your core metrics and insights at a glance.</p>
      </div>
      <DashboardGrid datasetId={activeDatasetId} />
    </div>
  ); 
}
