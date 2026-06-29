import { z } from "zod";
const uuid = z.string().uuid();
const json = z.record(z.string(), z.unknown());
export const ApiErrorBody = z.object({
  error: z.object({ code: z.string(), message: z.string() }),
});
export const Dataset = z.object({
  id: uuid,
  name: z.string(),
  description: z.string().nullable(),
  source_type: z.string(),
  storage_bucket: z.string(),
  storage_path: z.string(),
  file_size_bytes: z.number().int(),
  row_count: z.number().int(),
  created_at: z.string(),
  updated_at: z.string(),
  mapping_status: z.enum(["mapping_required", "active"]).optional(),
  active_mapping_version: z.number().int().nonnegative().optional(),
});
export const Column = z.object({
  name: z.string(),
  display_name: z.string(),
  data_type: z.enum(["string", "number", "boolean", "date", "category"]),
  semantic_role: z
    .enum(["time", "metric", "dimension", "identifier"])
    .nullable(),
  missing_percent: z.number(),
  unique_count: z.number().int().optional(),
  sample_values: z.array(z.unknown()).optional(),
  min_value: z.unknown().nullable().optional(),
  max_value: z.unknown().nullable().optional(),
  inference_confidence: z.number().min(0).max(1).optional(),
  inference_reasons: z.array(z.string()).optional(),
  compatible_aggregations: z.array(z.enum(["sum", "avg", "count", "count_distinct", "min", "max"])).optional(),
});
export const Profile = z.object({
  dataset_id: uuid,
  row_count: z.number().int(),
  quality_score: z.number().min(0).max(100),
  warnings: z.array(z.string()),
  columns: z.array(Column),
});
export const Schema = z.object({ dataset_id: uuid, columns: z.array(Column) });
export const UploadUrl = z.object({
  dataset_id: uuid,
  upload_url: z.string().url(),
  storage_path: z.string(),
});
export const Aggregation = z.enum(["sum", "avg", "count", "count_distinct", "min", "max"]);
export const DisplayFormat = z.enum(["number", "currency", "percent"]);
export const MetricMapping = z.object({column_id:uuid,label:z.string(),aggregation:Aggregation,display_format:DisplayFormat,position:z.number().int(),is_primary:z.boolean()});
export const DimensionMapping = z.object({column_id:uuid,label:z.string(),position:z.number().int()});
export const TypeOverride = z.object({column_id:uuid,data_type:z.enum(["number","date","boolean","category","string"])});
export const AnalysisConfigInput = z.object({base_version:z.number().int().nonnegative(),primary_time_column_id:uuid.nullable(),metrics:z.array(MetricMapping).min(1).max(4),dimensions:z.array(DimensionMapping).max(6),type_overrides:z.array(TypeOverride).default([])});
export const AnalysisColumn = z.object({id:uuid,name:z.string(),display_name:z.string(),data_type:z.string(),inferred_role:z.string().nullable(),inference_confidence:z.number(),inference_reasons:z.array(z.string()),compatible_aggregations:z.array(Aggregation),sample_values:z.array(z.unknown())});
export const Capabilities = z.object({can_render_kpis:z.boolean(),can_render_trends:z.boolean(),can_group:z.boolean(),can_scan_anomalies:z.boolean()});
export const AnalysisConfig = z.object({dataset_id:uuid,mapping_status:z.enum(["mapping_required","active"]),active_version:z.number().int(),primary_time_column_id:uuid.nullable(),metrics:z.array(MetricMapping),dimensions:z.array(DimensionMapping),suggestions:AnalysisConfigInput.nullable(),columns:z.array(AnalysisColumn),capabilities:Capabilities});
export const Intent = z.object({
  intent: z.enum([
    "single_metric",
    "time_series",
    "grouped_metric",
    "comparison",
    "proportion",
    "top_n",
    "bottom_n",
    "correlation",
    "anomaly_explanation",
    "clarification_required",
  ]),
  metric: z.string().nullable(),
  aggregation: z.enum(["sum", "avg", "count", "count_distinct", "min", "max"]).nullable(),
  group_by: z.array(z.string()),
  date_range: json.nullable(),
  filters: z.array(json),
  sort: json.nullable(),
  limit: z.number().int().positive().nullable(),
  chart_hint: z.string().nullable(),
});
export const Chart = z.object({
  type: z.string(),
  title: z.string(),
  description: z.string(),
  x_key: z.string().nullable(),
  y_keys: z.array(z.string()),
  series: z.array(json).nullable(),
  data: z.array(json),
  meta: json,
});
export const OverviewKpi = z.object({label:z.string(),value:z.number().nullable(),formatted_value:z.string(),aggregation:Aggregation,display_format:DisplayFormat,column_name:z.string()});
export const DatasetOverview = z.object({dataset_id:uuid,mapping_version:z.number().int(),kpis:z.array(OverviewKpi),primary_chart:Chart.nullable(),capabilities:Capabilities});
export const Ask = z.object({
  answer_id: uuid.nullable(),
  session_id: uuid.nullable(),
  summary: z.string().nullable(),
  chart: Chart.nullable(),
  query_plan: Intent.nullable(),
  confidence: z.literal("high").nullable(),
  suggested_followups: z.array(z.string()),
  clarification_required: z
    .object({ code: z.string(), message: z.string() })
    .nullable(),
  debug_sql: z.string().nullable(),
  mapping_version: z.number().int().nullable().optional(),
});
export const Widget = z.object({
  id: uuid,
  dashboard_id: uuid,
  dataset_id: uuid.nullable(),
  title: z.string(),
  widget_type: z.enum([
    "metric",
    "table",
    "bar",
    "line",
    "pie",
    "area",
    "scatter",
  ]),
  query_text: z.string().nullable(),
  config: z.object({
    chart_payload: Chart.optional(),
    query_plan: Intent.nullable().optional(),
    source: z
      .object({ type: z.enum(["ask_message", "insight", "anomaly"]), id: uuid })
      .optional(),
  }),
  position: z.number().int(),
  mapping_version: z.number().int().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export const Layout = z.object({
  dashboard_id: uuid,
  layout: z.array(
    z.object({ widget_id: uuid, position: z.number().int().nonnegative() }),
  ),
});
export const Insight = z.object({
  id: uuid,
  dataset_id: uuid.nullable(),
  title: z.string(),
  body: z.string(),
  insight_type: z.string(),
  severity: z.string(),
  score: z.number().nullable(),
  metadata: json,
  created_at: z.string(),
  mapping_version: z.number().int().nullable().optional(),
});
export const Anomaly = z.object({
  id: uuid,
  dataset_id: uuid.nullable(),
  detector_type: z.string(),
  metric_name: z.string().nullable(),
  severity: z.string(),
  explanation: z.string().nullable(),
  anomaly_payload: json,
  created_at: z.string(),
  mapping_version: z.number().int().nullable().optional(),
});
export type DatasetT = z.infer<typeof Dataset>;
export type ProfileT = z.infer<typeof Profile>;
export type AnalysisConfigInputT = z.infer<typeof AnalysisConfigInput>;
export type AnalysisConfigT = z.infer<typeof AnalysisConfig>;
export type DatasetOverviewT = z.infer<typeof DatasetOverview>;
export type ChartT = z.infer<typeof Chart>;
export type AskT = z.infer<typeof Ask>;
export type WidgetT = z.infer<typeof Widget>;
export type InsightT = z.infer<typeof Insight>;
export type AnomalyT = z.infer<typeof Anomaly>;
