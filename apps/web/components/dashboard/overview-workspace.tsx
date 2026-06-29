"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Pin, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queryKeys";
import { getDefaultDashboard } from "@/lib/dashboard";
import { useAppStore } from "@/stores/app-store";
import { ChartRenderer } from "@/components/charts/chart-renderer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge, EmptyState, Skeleton } from "@/components/ui/states";

export function OverviewWorkspace() {
  const dataset = useAppStore((state) => state.activeDataset);
  const queryClient = useQueryClient();
  const config = useQuery({
    queryKey: queryKeys.datasets.analysisConfig(dataset ?? "missing"),
    queryFn: () => api.getAnalysisConfig(dataset!),
    enabled: Boolean(dataset),
  });
  const overview = useQuery({
    queryKey: queryKeys.datasets.overview(dataset ?? "missing", config.data?.active_version),
    queryFn: () => api.getOverview(dataset!),
    enabled: Boolean(dataset) && config.data?.mapping_status === "active",
  });
  const widgets = useQuery({
    queryKey: [...queryKeys.widgets.list(dataset ?? "missing"), "overview"],
    queryFn: async () => api.getWidgets(await getDefaultDashboard()),
    enabled: Boolean(dataset),
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.deleteWidget(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.widgets.list(dataset ?? "missing") }),
  });

  if (!dataset) {
    return (
      <EmptyState
        title="Choose data to begin"
        description="Select a dataset above or upload a CSV to turn this overview on."
        action={<Link className="font-semibold text-[var(--marketing-mint)]" href="/onboarding/connect-data">Connect data →</Link>}
      />
    );
  }

  if (config.isLoading) {
    return <div className="grid gap-4"><Skeleton className="h-36"/><Skeleton className="h-80"/></div>;
  }

  if (config.error) {
    return (
      <Card className="signal-card grid min-h-80 place-items-center p-8 text-center">
        <div>
          <p className="dashboard-section-label">OVERVIEW UNAVAILABLE</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-.05em]">We couldn’t load the dataset contract.</h2>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-white/70">Retry the configuration request. If this is the demo workspace, the shared dataset should recover automatically once the API responds.</p>
          <Button className="mt-7" onClick={() => config.refetch()}>Retry</Button>
        </div>
      </Card>
    );
  }

  if (config.data?.mapping_status !== "active") {
    return (
      <Card className="signal-card grid min-h-80 place-items-center p-8 text-center">
        <div>
          <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-[rgba(168,255,120,.08)] text-[var(--marketing-mint)]"><Sparkles size={19}/></span>
          <p className="dashboard-section-label mt-6">ANALYSIS CONTRACT REQUIRED</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-.05em]">Choose what matters first.</h2>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-white/70">Readout found the columns. Confirm which ones should power KPIs, trends, and automated signals before this dashboard builds itself.</p>
          <Link href={`/onboarding/schema-preview?dataset=${dataset}`} className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-xl bg-[var(--marketing-mint)] px-5 text-sm font-bold text-[var(--marketing-ink)]">Map this dataset <ArrowRight size={15}/></Link>
        </div>
      </Card>
    );
  }

  if (overview.isLoading) {
    return <div className="grid gap-4"><div className="grid gap-3 md:grid-cols-3"><Skeleton className="h-40"/><Skeleton className="h-40"/><Skeleton className="h-40"/></div><Skeleton className="h-80"/></div>;
  }

  if (overview.error || !overview.data) {
    return (
      <Card className="signal-card grid min-h-80 place-items-center p-8 text-center">
        <div>
          <p className="dashboard-section-label">OVERVIEW UNAVAILABLE</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-.05em]">The overview request didn’t complete.</h2>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-white/70">We stopped showing a fake loading state here. Retry the live overview query and the dashboard will render as soon as the dataset responds.</p>
          <Button className="mt-7" onClick={() => overview.refetch()}>Reload overview</Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="grid gap-5">
      <div className="dashboard-status-line">Mapping v{overview.data.mapping_version} · active analysis contract</div>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {overview.data.kpis.map((kpi, index) => (
          <Card key={`${kpi.column_name}-${kpi.aggregation}`} className="signal-card min-h-40 p-6">
            <span className="metric-card__index">0{index + 1}</span>
            <p className="dashboard-section-label">{kpi.label}</p>
            <p className="mt-6 text-4xl font-semibold tracking-[-.06em] tabular">{kpi.formatted_value}</p>
            <p className="mt-2 text-[10px] uppercase tracking-[.12em] text-white/65">{kpi.aggregation.replace("_", " ")}</p>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.65fr_.75fr]">
        <Card className="signal-card min-w-0 p-6 md:p-7">
          <div className="mb-6 flex justify-between">
            <div>
              <p className="dashboard-section-label">Primary trajectory</p>
              <h2 className="dashboard-section-title">The shape of momentum</h2>
            </div>
            <Link className="text-sm font-semibold text-[var(--marketing-mint)]" href="/dashboard/ask">Ask why <ArrowRight className="ml-1 inline" size={14}/></Link>
          </div>
          {overview.data.primary_chart ? (
            <ChartRenderer payload={overview.data.primary_chart}/>
          ) : (
            <div className="grid h-72 place-items-center text-center text-sm text-white/70">No time axis is mapped.<br/>KPIs and categorical analysis remain available.</div>
          )}
        </Card>

        <Card className="signal-card flex flex-col p-6 md:p-7">
          <span className="flex size-10 items-center justify-center rounded-full bg-[rgba(168,255,120,.09)] text-[var(--marketing-mint)]"><Sparkles size={17}/></span>
          <p className="dashboard-section-label mt-8">Capabilities</p>
          <h2 className="dashboard-section-title">Built from your mapping.</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            <Badge tone="success">KPIs ready</Badge>
            {overview.data.capabilities.can_render_trends && <Badge>Trends ready</Badge>}
            {overview.data.capabilities.can_group && <Badge>Breakdowns ready</Badge>}
          </div>
          <Link className="mt-auto pt-8 text-sm font-semibold text-[var(--marketing-mint)]" href={`/onboarding/schema-preview?dataset=${dataset}`}>Edit mapping →</Link>
        </Card>
      </section>

      <section>
        <div className="mb-4 mt-3 flex items-end justify-between border-t border-white/[.07] pt-7">
          <div>
            <p className="dashboard-section-label">Pinned widgets</p>
            <h2 className="dashboard-section-title">Your working set</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => widgets.refetch()}><RefreshCw size={15}/>Refresh</Button>
        </div>

        {widgets.isLoading ? (
          <Skeleton className="h-64"/>
        ) : !widgets.data?.length ? (
          <EmptyState
            title="Pin your first answer"
            description="Ask Readout a question, then pin the chart your team should return to."
            action={<Link className="font-semibold text-[var(--marketing-mint)]" href="/dashboard/ask"><Pin className="mr-2 inline" size={16}/>Ask a question</Link>}
          />
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {widgets.data.map((widget, index) => (
              <Card key={widget.id} className={`${index % 3 === 0 ? "md:col-span-2" : ""} signal-card group relative min-w-0 p-6`}>
                {widget.mapping_version !== null && widget.mapping_version !== overview.data.mapping_version && (
                  <span className="mb-4 inline-flex rounded-full bg-[rgba(255,204,102,.09)] px-2.5 py-1 text-[9px] font-bold text-[var(--warning)]">Snapshot from mapping v{widget.mapping_version}</span>
                )}
                <button aria-label={`Delete ${widget.title}`} onClick={() => remove.mutate(widget.id)} className="absolute right-3 top-3 z-10 grid h-9 w-9 place-items-center rounded-xl bg-[var(--surface)] opacity-0 transition group-hover:opacity-100 focus:opacity-100"><Trash2 size={15}/></button>
                {widget.config.chart_payload ? <ChartRenderer payload={widget.config.chart_payload}/> : <p className="text-sm text-white/70">This widget has no reusable chart payload.</p>}
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
