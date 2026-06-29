"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Check, ScanSearch } from "lucide-react";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queryKeys";
import { Chart } from "@/lib/api/types";
import type { AnomalyT } from "@/lib/api/types";
import { useAppStore } from "@/stores/app-store";
import { ChartRenderer } from "@/components/charts/chart-renderer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";
import {
  Badge,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/components/ui/states";

export function AnomaliesWorkspace() {
  const dataset = useAppStore((state) => state.activeDataset);
  const queryClient = useQueryClient();
  const [detail, setDetail] = useState<AnomalyT | null>(null);
  const [error, setError] = useState("");

  const configQuery = useQuery({
    queryKey: queryKeys.datasets.analysisConfig(dataset ?? "missing"),
    queryFn: () => api.getAnalysisConfig(dataset!),
    enabled: Boolean(dataset),
  });

  const listQuery = useQuery({
    queryKey: queryKeys.anomalies.list(dataset ?? "missing", configQuery.data?.active_version),
    queryFn: () => api.getAnomalies(dataset!),
    enabled: Boolean(dataset) && configQuery.data?.mapping_status === "active",
  });

  const scanMutation = useMutation({
    mutationFn: () => api.scanAnomalies(dataset!),
    onMutate: () => setError(""),
    onSuccess: (items) => {
      queryClient.setQueryData(
        queryKeys.anomalies.list(dataset!, configQuery.data?.active_version),
        items,
      );
    },
    onError: () =>
      setError("The scan could not complete right now. Please retry shortly."),
  });

  const dismissMutation = useMutation({
    mutationFn: async (item: AnomalyT) => {
      await api.deleteAnomaly(item.id);
      return item.id;
    },
    onSuccess: (id) => {
      queryClient.setQueryData<AnomalyT[] | undefined>(
        queryKeys.anomalies.list(dataset!, configQuery.data?.active_version),
        (items) => items?.filter((entry) => entry.id !== id) ?? [],
      );
      setDetail(null);
    },
    onError: () =>
      setError("That signal could not be dismissed. Nothing was changed."),
  });

  const mappingRequired =
    Boolean(dataset) && configQuery.data?.mapping_status !== "active";
  const items = listQuery.data ?? [];
  const chart = detail
    ? Chart.safeParse(detail.anomaly_payload.chart_payload)
    : null;

  if (configQuery.error || listQuery.error) {
    return (
      <ErrorState
        message={error || "Anomaly signals could not be loaded. Your data is unchanged."}
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
        title="Map this dataset to monitor anomalies"
        description="Anomaly detection needs a confirmed metric and time axis before it can establish a trustworthy baseline."
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
        description="Select a data source before reviewing anomaly signals."
      />
    );
  }

  const isLoading =
    configQuery.isLoading || (configQuery.data?.mapping_status === "active" && listQuery.isLoading);
  const isScanning = scanMutation.isPending;

  return (
    <>
      <div className="dashboard-action-rail">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-full bg-[rgba(255,204,102,.1)] text-[var(--warning)]">
            <Activity size={16} />
          </span>
          <div>
            <p className="dashboard-section-label">Baseline monitor</p>
            <p className="mt-1 text-xs text-white/70">
              A calm scan for movement beyond expected ranges.
            </p>
          </div>
        </div>
        <Button onClick={() => scanMutation.mutate()} disabled={isScanning}>
          <ScanSearch size={16} />
          {isScanning ? "Scanning baseline..." : "Scan anomalies"}
        </Button>
      </div>

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

      {isLoading || isScanning ? (
        <div className="grid gap-3">
          <Skeleton />
          <Skeleton />
          <Skeleton />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          title="No notable deviations found"
          description="The current signals remain within their expected ranges. You can scan again as the data changes."
          action={<Button onClick={() => scanMutation.mutate()}>Scan now</Button>}
        />
      ) : (
        <div className="grid gap-4">
          {items.map((item) => (
            <Card
              key={item.id}
              className="signal-card anomaly-row flex flex-wrap items-center justify-between gap-5 p-5 md:p-6"
            >
              <div className="flex min-w-0 items-start gap-4">
                <span className="anomaly-pulse mt-2 h-3 w-3 shrink-0 rounded-full bg-[var(--warning)]" />
                <div>
                  <h2 className="text-lg font-bold">
                    {item.metric_name ?? "Dataset signal"}
                  </h2>
                  <p className="mt-1 line-clamp-2 text-[var(--ink-secondary)]">
                    {item.explanation ?? "A value moved outside its expected range."}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge tone="warning">{item.severity}</Badge>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setDetail(item)}
                >
                  Review
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Drawer
        open={!!detail}
        onOpenChange={(open) => !open && setDetail(null)}
        title="Signal detail"
      >
        {detail && (
          <div>
            <Badge tone="warning">{detail.severity}</Badge>
            <h3 className="mt-5 text-2xl font-bold">
              {detail.metric_name ?? "Dataset signal"}
            </h3>
            <p className="mt-3 leading-7 text-[var(--ink-secondary)]">
              {detail.explanation ?? "A value moved outside its expected range."}
            </p>
            {chart?.success ? (
              <div className="mt-6">
                <ChartRenderer payload={chart.data} />
              </div>
            ) : (
              <div className="mt-6 rounded-xl bg-[color-mix(in_srgb,var(--warning)_10%,white)] p-5 text-sm">
                The explanation is available, but this signal has no chart
                preview.
              </div>
            )}
            <Button
              className="mt-6"
              variant="secondary"
              onClick={() => dismissMutation.mutate(detail)}
            >
              <Check size={16} />
              Acknowledge and dismiss
            </Button>
          </div>
        )}
      </Drawer>
    </>
  );
}
