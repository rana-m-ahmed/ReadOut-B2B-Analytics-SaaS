"use client";

import { useCallback, useEffect, useMemo, useState, type DragEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowRight,
  CalendarDays,
  Check,
  GripVertical,
  Plus,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queryKeys";
import type { AnalysisConfigInputT, AnalysisConfigT } from "@/lib/api/types";
import { useAppStore } from "@/stores/app-store";
import { ChartRenderer } from "@/components/charts/chart-renderer";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/states";

type Column = AnalysisConfigT["columns"][number];
type ColumnType = AnalysisConfigInputT["type_overrides"][number]["data_type"];
type Aggregation = AnalysisConfigInputT["metrics"][number]["aggregation"];

const emptyDraft: AnalysisConfigInputT = {
  base_version: 0,
  primary_time_column_id: null,
  metrics: [],
  dimensions: [],
  type_overrides: [],
};

function readStoredDraft(datasetId?: string): AnalysisConfigInputT | null {
  if (!datasetId || typeof window === "undefined") return null;
  try {
    const cached = window.sessionStorage.getItem(`readout:mapping:${datasetId}`);
    return cached ? (JSON.parse(cached) as AnalysisConfigInputT) : null;
  } catch {
    window.sessionStorage.removeItem(`readout:mapping:${datasetId}`);
    return null;
  }
}

function buildDraft(config: AnalysisConfigT | undefined): AnalysisConfigInputT | null {
  if (!config) return null;
  if (config.mapping_status === "active") {
    return {
      base_version: config.active_version,
      primary_time_column_id: config.primary_time_column_id,
      metrics: config.metrics,
      dimensions: config.dimensions,
      type_overrides: [],
    };
  }
  return config.suggestions ?? emptyDraft;
}

function compatibleAggregationsForType(
  dataType: ColumnType,
  inferredRole: string | null,
): Aggregation[] {
  if (dataType === "number") return ["sum", "avg", "count", "count_distinct", "min", "max"];
  if (
    inferredRole === "identifier" ||
    dataType === "date" ||
    dataType === "boolean" ||
    dataType === "category" ||
    dataType === "string"
  ) {
    return ["count", "count_distinct"];
  }
  return ["count"];
}

export function SchemaProfile({ datasetId }: { datasetId?: string }) {
  return <SchemaProfileWorkbench key={datasetId ?? "missing"} datasetId={datasetId} />;
}

function SchemaProfileWorkbench({ datasetId }: { datasetId?: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setActiveDataset = useAppStore((state) => state.setActiveDataset);
  const [draftOverride, setDraftOverride] = useState<AnalysisConfigInputT | null>(
    () => readStoredDraft(datasetId),
  );
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState("");

  const configQuery = useQuery({
    queryKey: queryKeys.datasets.analysisConfig(datasetId ?? "missing"),
    queryFn: () => api.getAnalysisConfig(datasetId!),
    enabled: Boolean(datasetId),
  });
  const profileQuery = useQuery({
    queryKey: queryKeys.datasets.profile(datasetId ?? "missing"),
    queryFn: () => api.getProfile(datasetId!),
    enabled: Boolean(datasetId),
  });

  const derivedDraft = useMemo(() => buildDraft(configQuery.data), [configQuery.data]);
  const draft = draftOverride ?? derivedDraft;

  useEffect(() => {
    if (!datasetId || !draft || typeof window === "undefined") return;
    window.sessionStorage.setItem(`readout:mapping:${datasetId}`, JSON.stringify(draft));
  }, [datasetId, draft]);

  const preview = useMutation({
    mutationFn: (input: AnalysisConfigInputT) => api.previewAnalysisConfig(datasetId!, input),
    onError: () =>
      setNotice("Preview could not be generated. Review the selected column types."),
  });

  const save = useMutation({
    mutationFn: (input: AnalysisConfigInputT) => api.saveAnalysisConfig(datasetId!, input),
    onSuccess: async (data) => {
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(`readout:mapping:${datasetId}`);
      }
      setActiveDataset(datasetId!);
      await queryClient.invalidateQueries({ queryKey: queryKeys.datasets.all });
      queryClient.setQueryData(queryKeys.datasets.analysisConfig(datasetId!), data);
      await queryClient.invalidateQueries({
        queryKey: queryKeys.datasets.overview(datasetId!),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.datasets.profile(datasetId!),
      });
      router.push("/onboarding/walkthrough");
    },
    onError: () =>
      setNotice("The mapping was not saved. Reload if it changed in another session."),
  });

  const profileByName = useMemo(
    () => new Map(profileQuery.data?.columns.map((column) => [column.name, column]) ?? []),
    [profileQuery.data],
  );
  const columnById = useMemo(
    () => new Map(configQuery.data?.columns.map((column) => [column.id, column]) ?? []),
    [configQuery.data],
  );

  const effectiveType = useCallback(
    (column: Column): ColumnType =>
      draft?.type_overrides.find((override) => override.column_id === column.id)?.data_type ??
      (column.data_type as ColumnType),
    [draft?.type_overrides],
  );

  const filteredColumns = useMemo(() => {
    const query = search.toLowerCase();
    return (
      configQuery.data?.columns.filter((column) =>
        `${column.display_name} ${effectiveType(column)} ${column.inferred_role}`
          .toLowerCase()
          .includes(query),
      ) ?? []
    );
  }, [configQuery.data, effectiveType, search]);

  function updateDraft(next: AnalysisConfigInputT) {
    setDraftOverride(next);
  }

  function addMetric(column: Column) {
    if (!draft) return;
    if (draft.metrics.some((metric) => metric.column_id === column.id)) return;
    if (draft.metrics.length >= 4) return;
    const compatibleAggregations = compatibleAggregationsForType(
      effectiveType(column),
      column.inferred_role,
    );
    const aggregation =
      column.inferred_role === "identifier"
        ? "count_distinct"
        : compatibleAggregations.includes("sum")
          ? "sum"
          : (compatibleAggregations[0] ?? "count");
    updateDraft({
      ...draft,
      metrics: [
        ...draft.metrics,
        {
          column_id: column.id,
          label: column.display_name,
          aggregation,
          display_format: "number",
          position: draft.metrics.length,
          is_primary: draft.metrics.length === 0,
        },
      ],
    });
  }

  function addDimension(column: Column) {
    if (!draft) return;
    if (draft.dimensions.some((dimension) => dimension.column_id === column.id)) return;
    if (draft.dimensions.length >= 6) return;
    updateDraft({
      ...draft,
      dimensions: [
        ...draft.dimensions,
        {
          column_id: column.id,
          label: column.display_name,
          position: draft.dimensions.length,
        },
      ],
    });
  }

  function removeMetric(index: number) {
    if (!draft) return;
    const remaining = draft.metrics
      .filter((_, metricIndex) => metricIndex !== index)
      .map((metric, metricIndex) => ({
        ...metric,
        position: metricIndex,
        is_primary: metricIndex === 0,
      }));
    updateDraft({ ...draft, metrics: remaining });
  }

  function removeDimension(index: number) {
    if (!draft) return;
    const remaining = draft.dimensions
      .filter((_, dimensionIndex) => dimensionIndex !== index)
      .map((dimension, dimensionIndex) => ({
        ...dimension,
        position: dimensionIndex,
      }));
    updateDraft({ ...draft, dimensions: remaining });
  }

  function setColumnType(column: Column, dataType: ColumnType) {
    if (!draft) return;
    const nextOverrides =
      dataType === column.data_type
        ? draft.type_overrides.filter((override) => override.column_id !== column.id)
        : [
            ...draft.type_overrides.filter((override) => override.column_id !== column.id),
            { column_id: column.id, data_type: dataType },
          ];
    const compatibleAggregations = compatibleAggregationsForType(
      dataType,
      column.inferred_role,
    );
    updateDraft({
      ...draft,
      primary_time_column_id:
        draft.primary_time_column_id === column.id && dataType !== "date"
          ? null
          : draft.primary_time_column_id,
      type_overrides: nextOverrides,
      metrics: draft.metrics.map((metric) =>
        metric.column_id !== column.id
          ? metric
          : compatibleAggregations.includes(metric.aggregation)
            ? metric
            : { ...metric, aggregation: compatibleAggregations[0] ?? "count" },
      ),
    });
  }

  function handleDrop(event: DragEvent, target: "metric" | "dimension" | "time") {
    event.preventDefault();
    const columnId = event.dataTransfer.getData("text/column-id");
    const column = columnById.get(columnId);
    if (!column || !draft) return;
    if (target === "metric") {
      addMetric(column);
      return;
    }
    if (target === "dimension") {
      addDimension(column);
      return;
    }
    if (effectiveType(column) === "date") {
      updateDraft({ ...draft, primary_time_column_id: column.id });
    }
  }

  if (!datasetId) {
    return <p role="alert">No dataset was selected for mapping.</p>;
  }

  if (configQuery.isLoading || !draft) {
    return (
      <div className="grid gap-4">
        <Skeleton className="h-28" />
        <Skeleton className="h-[36rem]" />
      </div>
    );
  }

  if (configQuery.error) {
    return (
      <p role="alert" className="text-[var(--danger)]">
        The dataset mapping could not be loaded.
      </p>
    );
  }

  const hasMetric = draft.metrics.length > 0;

  return (
    <div className="mapping-workbench grid gap-6">
      <div className="mapping-summary-grid">
        <div>
          <span>Rows profiled</span>
          <strong>{profileQuery.data?.row_count.toLocaleString() ?? "--"}</strong>
        </div>
        <div>
          <span>Columns found</span>
          <strong>{configQuery.data?.columns.length ?? 0}</strong>
        </div>
        <div>
          <span>Quality score</span>
          <strong>{profileQuery.data ? `${profileQuery.data.quality_score}%` : "--"}</strong>
        </div>
        <div>
          <span>Mapping state</span>
          <strong
            className={
              configQuery.data?.mapping_status === "active"
                ? "text-[var(--marketing-mint)]"
                : "text-[var(--warning)]"
            }
          >
            {configQuery.data?.mapping_status === "active"
              ? `Active v${configQuery.data.active_version}`
              : "Needs review"}
          </strong>
        </div>
      </div>

      <div className="grid min-w-0 gap-4 md:grid-cols-[minmax(0,.9fr)_minmax(0,1.1fr)]">
        <section className="mapping-column-catalog mapping-compact-panel">
          <div className="mapping-panel-heading">
            <div>
              <p>01 / COLUMN CATALOG</p>
              <h2>What did we find?</h2>
            </div>
            <Sparkles size={18} />
          </div>
          <label className="mapping-search">
            <Search size={15} />
            <span className="sr-only">Search columns</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search columns or types..."
            />
          </label>
          <div className="mapping-column-list">
            {filteredColumns.map((column) => {
              const profile = profileByName.get(column.name);
              const completeness = profile
                ? `${(100 - profile.missing_percent).toFixed(0)}% complete`
                : "profiled";
              const samples = column.sample_values.slice(0, 2).map(String).join(" | ");
              const resolvedType = effectiveType(column);
              return (
                <article
                  key={column.id}
                  draggable
                  onDragStart={(event) =>
                    event.dataTransfer.setData("text/column-id", column.id)
                  }
                  className="mapping-column-row"
                >
                  <GripVertical size={14} className="text-white/20" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <strong className="truncate">{column.display_name}</strong>
                      <span className="mapping-type-pill">{resolvedType}</span>
                    </div>
                    <p>
                      {column.inferred_role ?? "unclassified"} |{" "}
                      {Math.round(column.inference_confidence * 100)}% confidence |{" "}
                      {completeness}
                    </p>
                    <small>{samples || "No sample values"}</small>
                    <div className="mt-2 min-w-0">
                      <label className="sr-only" htmlFor={`column-type-${column.id}`}>
                        Column type
                      </label>
                      <select
                        id={`column-type-${column.id}`}
                        value={resolvedType}
                        onChange={(event) =>
                          setColumnType(column, event.target.value as ColumnType)
                        }
                        className="max-w-full rounded-full border border-white/[.1] bg-white/[.04] px-3 py-1 text-xs text-white/80"
                      >
                        <option value="number">Number</option>
                        <option value="date">Date</option>
                        <option value="boolean">Boolean</option>
                        <option value="category">Category</option>
                        <option value="string">String</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <button
                      title="Use as metric"
                      aria-label={`Use ${column.display_name} as metric`}
                      onClick={() => addMetric(column)}
                    >
                      <Activity size={14} />
                    </button>
                    <button
                      title="Use as dimension"
                      aria-label={`Use ${column.display_name} as dimension`}
                      onClick={() => addDimension(column)}
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="mapping-contract-panel mapping-compact-panel">
          <div className="mapping-panel-heading">
            <div>
              <p>02 / ANALYSIS CONTRACT</p>
              <h2>Define what matters.</h2>
            </div>
            <span>{draft.metrics.length}/4 metrics</span>
          </div>

          <div
            className="mapping-drop-zone"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => handleDrop(event, "time")}
          >
            <CalendarDays size={18} />
            <div className="flex-1">
              <p>
                Primary time axis <span>optional</span>
              </p>
              <select
                aria-label="Primary time axis"
                value={draft.primary_time_column_id ?? ""}
                onChange={(event) =>
                  updateDraft({
                    ...draft,
                    primary_time_column_id: event.target.value || null,
                  })
                }
              >
                <option value="">No time axis</option>
                {configQuery.data?.columns
                  .filter((column) => effectiveType(column) === "date")
                  .map((column) => (
                    <option value={column.id} key={column.id}>
                      {column.display_name}
                    </option>
                  ))}
              </select>
            </div>
            {draft.primary_time_column_id && (
              <Check size={16} className="text-[var(--marketing-mint)]" />
            )}
          </div>

          <div className="mt-4">
            <p className="mapping-zone-label">KEY METRICS</p>
            <div
              className="grid gap-2"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => handleDrop(event, "metric")}
            >
              {draft.metrics.map((metric, index) => {
                const column = columnById.get(metric.column_id);
                const compatibleAggregations = column
                  ? compatibleAggregationsForType(effectiveType(column), column.inferred_role)
                  : [];
                return (
                  <div className="mapping-config-row" key={metric.column_id}>
                    <span className="mapping-position">0{index + 1}</span>
                    <input
                      aria-label={`Metric ${index + 1} label`}
                      value={metric.label}
                      onChange={(event) =>
                        updateDraft({
                          ...draft,
                          metrics: draft.metrics.map((entry, metricIndex) =>
                            metricIndex === index
                              ? { ...entry, label: event.target.value }
                              : entry,
                          ),
                        })
                      }
                    />
                    <select
                      aria-label={`${metric.label} aggregation`}
                      value={metric.aggregation}
                      onChange={(event) =>
                        updateDraft({
                          ...draft,
                          metrics: draft.metrics.map((entry, metricIndex) =>
                            metricIndex === index
                              ? {
                                  ...entry,
                                  aggregation: event.target.value as typeof entry.aggregation,
                                }
                              : entry,
                          ),
                        })
                      }
                    >
                      {compatibleAggregations.map((aggregation) => (
                        <option value={aggregation} key={aggregation}>
                          {aggregation.replace("_", " ")}
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label={`${metric.label} format`}
                      value={metric.display_format}
                      onChange={(event) =>
                        updateDraft({
                          ...draft,
                          metrics: draft.metrics.map((entry, metricIndex) =>
                            metricIndex === index
                              ? {
                                  ...entry,
                                  display_format: event.target.value as typeof entry.display_format,
                                }
                              : entry,
                          ),
                        })
                      }
                    >
                      <option value="number">Number</option>
                      <option value="currency">Currency</option>
                      <option value="percent">Percent</option>
                    </select>
                    <button
                      aria-label={`Remove ${metric.label}`}
                      onClick={() => removeMetric(index)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                );
              })}
              {draft.metrics.length < 4 && (
                <div className="mapping-empty-zone mapping-metric-placeholder">
                  <span aria-hidden="true">
                    <Plus size={15} />
                  </span>
                  <div>
                    <strong>Drag &amp; drop a metric</strong>
                    <p>Choose a column from the catalog.</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-5">
            <p className="mapping-zone-label">
              BREAKDOWN DIMENSIONS <span>OPTIONAL</span>
            </p>
            <div
              className="mapping-dimension-zone"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => handleDrop(event, "dimension")}
            >
              {draft.dimensions.length === 0 ? (
                <p>Drop category columns here to enable grouped analysis.</p>
              ) : (
                draft.dimensions.map((dimension, index) => (
                  <span key={dimension.column_id}>
                    {dimension.label}
                    <button
                      aria-label={`Remove ${dimension.label}`}
                      onClick={() => removeDimension(index)}
                    >
                      x
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>
        </section>
      </div>

      <section className="mapping-preview-panel">
        <div className="mapping-panel-heading">
          <div>
            <p>03 / LIVE PREVIEW</p>
            <h2>See the contract in action.</h2>
          </div>
          <Button
            variant="secondary"
            disabled={!hasMetric || preview.isPending}
            onClick={() => {
              setNotice("");
              preview.mutate(draft);
            }}
          >
            {preview.isPending ? "Calculating..." : "Preview mapping"}
          </Button>
        </div>
        {preview.data ? (
          <div className="grid gap-4 lg:grid-cols-[.72fr_1.28fr]">
            <div className="grid grid-cols-2 gap-2">
              {preview.data.kpis.map((kpi) => (
                <div className="mapping-kpi" key={kpi.label}>
                  <span>{kpi.label}</span>
                  <strong>{kpi.formatted_value}</strong>
                  <small>{kpi.aggregation.replace("_", " ")}</small>
                </div>
              ))}
            </div>
            <div className="mapping-chart-preview">
              {preview.data.primary_chart ? (
                <ChartRenderer payload={preview.data.primary_chart} />
              ) : (
                <div className="grid h-full min-h-52 place-items-center text-center text-sm text-white/70">
                  Choose a date column to unlock trend previews.
                  <br />
                  KPI and grouped analysis will still work.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="mapping-preview-empty">
            <Sparkles size={20} />
            <p>
              Generate a safe preview from the stored dataset before activating this
              mapping.
            </p>
          </div>
        )}
      </section>

      {notice && (
        <p role="alert" className="text-sm text-[var(--warning)]">
          {notice}
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-white/[.08] pt-5">
        <p className="max-w-xl text-xs leading-5 text-white/70">
          Activating creates a new immutable mapping version. Existing pinned
          answers remain snapshots of the version that produced them.
        </p>
        <Button disabled={!hasMetric || save.isPending} onClick={() => save.mutate(draft)}>
          {save.isPending
            ? "Activating..."
            : configQuery.data?.mapping_status === "active"
              ? "Activate new version"
              : "Confirm mapping"}
          <ArrowRight size={16} />
        </Button>
      </div>
    </div>
  );
}
