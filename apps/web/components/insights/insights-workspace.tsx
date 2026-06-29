"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Orbit, Pin, Sparkles } from "lucide-react";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queryKeys";
import { Chart } from "@/lib/api/types";
import type { InsightT } from "@/lib/api/types";
import { getDefaultDashboard } from "@/lib/dashboard";
import { useAppStore } from "@/stores/app-store";
import { ChartRenderer } from "@/components/charts/chart-renderer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Badge,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/components/ui/states";

export function InsightsWorkspace() {
  const dataset = useAppStore((state) => state.activeDataset);
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const configQuery = useQuery({
    queryKey: queryKeys.datasets.analysisConfig(dataset ?? "missing"),
    queryFn: () => api.getAnalysisConfig(dataset!),
    enabled: Boolean(dataset),
  });

  const listQuery = useQuery({
    queryKey: queryKeys.insights.list(dataset ?? "missing", configQuery.data?.active_version),
    queryFn: () => api.getInsights(dataset!),
    enabled: Boolean(dataset) && configQuery.data?.mapping_status === "active",
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateInsights(dataset!),
    onMutate: () => {
      setError("");
      setNotice("");
    },
    onSuccess: (items) => {
      queryClient.setQueryData(
        queryKeys.insights.list(dataset!, configQuery.data?.active_version),
        items,
      );
    },
    onError: () =>
      setError("Readout could not generate insights right now. Try again shortly."),
  });

  const pinMutation = useMutation({
    mutationFn: async (item: InsightT) => {
      const dashboardId = await getDefaultDashboard();
      await api.createWidget({
        dashboard_id: dashboardId,
        source_type: "insight",
        source_id: item.id,
        title: item.title,
      });
      return item.title;
    },
    onSuccess: (title) => setNotice(`Pinned "${title}".`),
    onError: () =>
      setNotice(
        "This insight does not contain a reusable chart, so it was not pinned.",
      ),
  });

  const mappingRequired =
    Boolean(dataset) && configQuery.data?.mapping_status !== "active";
  const items = listQuery.data ?? [];

  if (configQuery.error || listQuery.error) {
    return (
      <ErrorState
        message={error || "Insights could not be loaded. Your dataset is unchanged."}
        retry={() => {
          setError("");
          void configQuery.refetch();
          void listQuery.refetch();
        }}
      />
    );
  }

  if (mappingRequired) {
    return (
      <EmptyState
        title="Map this dataset to discover insights"
        description="Confirm key metrics and dimensions before Readout generates automated business claims."
        action={
          <a
            className="font-semibold text-[var(--marketing-mint)]"
            href={`/onboarding/schema-preview?dataset=${dataset}`}
          >
            Open mapping workbench -&gt;
          </a>
        }
      />
    );
  }

  if (!dataset) {
    return (
      <EmptyState
        title="Choose a dataset first"
        description="Select a source from the top bar before generating insights."
      />
    );
  }

  const isLoading =
    configQuery.isLoading || (configQuery.data?.mapping_status === "active" && listQuery.isLoading);
  const isGenerating = generateMutation.isPending;

  return (
    <>
      <div className="dashboard-action-rail">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-full bg-[rgba(96,70,232,.15)] text-[var(--accent)]">
            <Orbit size={16} />
          </span>
          <div>
            <p className="dashboard-section-label">Discovery engine</p>
            <p className="mt-1 text-xs text-white/70">
              Scan the active dataset for decision-worthy movement.
            </p>
          </div>
        </div>
        <Button onClick={() => generateMutation.mutate()} disabled={isGenerating}>
          <Sparkles size={16} />
          {isGenerating ? "Discovering insights..." : "Discover insights"}
        </Button>
      </div>

      {notice && (
        <p role="status" className="mb-4 text-sm font-semibold text-[var(--accent)]">
          {notice}
        </p>
      )}

      {error && (
        <p
          role="alert"
          className="mb-4 rounded-xl bg-[color-mix(in_srgb,var(--warning)_12%,white)] p-3 text-sm"
        >
          {error}{" "}
          <button
            className="font-bold underline"
            onClick={() => {
              setError("");
              void listQuery.refetch();
            }}
          >
            Retry
          </button>
        </p>
      )}

      {isLoading || isGenerating ? (
        <div className="grid gap-5 md:grid-cols-2">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          title="No significant insights yet"
          description="Run discovery to look for decision-worthy patterns in the current data."
          action={<Button onClick={() => generateMutation.mutate()}>Discover insights</Button>}
        />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item, index) => {
            const parsed = Chart.safeParse(item.metadata.chart_payload);
            return (
              <Card
                key={item.id}
                className={`signal-card insight-card min-w-0 p-6 md:p-7 ${index === 0 ? "md:col-span-2" : ""}`}
              >
                <span className="metric-card__index">
                  DISCOVERY / {String(index + 1).padStart(2, "0")}
                </span>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex flex-wrap gap-2">
                    <Badge>{item.severity}</Badge>
                    {item.score !== null && (
                      <Badge tone="success">Score {item.score.toFixed(1)}</Badge>
                    )}
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label={`Pin ${item.title}`}
                    onClick={() => pinMutation.mutate(item)}
                  >
                    <Pin size={16} />
                  </Button>
                </div>
                <h2 className="mt-10 max-w-xl text-2xl font-semibold tracking-[-.04em]">
                  {item.title}
                </h2>
                <p className="mt-3 leading-7 text-[var(--ink-secondary)]">
                  {item.body}
                </p>
                {parsed.success && (
                  <div className="mt-6">
                    <ChartRenderer payload={parsed.data} />
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
