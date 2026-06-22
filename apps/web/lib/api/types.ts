import { z } from "zod"

// -----------------------------------------------------------------------------
// Core Shared Types
// -----------------------------------------------------------------------------

export const ApiErrorSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
  })
})

// -----------------------------------------------------------------------------
// Dataset Contracts
// -----------------------------------------------------------------------------

export const DatasetSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable(),
  source_type: z.string(),
  storage_bucket: z.string(),
  storage_path: z.string(),
  file_size_bytes: z.number(),
  row_count: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type Dataset = z.infer<typeof DatasetSchema>

export const UploadUrlResponseSchema = z.object({
  dataset_id: z.string().uuid(),
  upload_url: z.string(),
  storage_path: z.string(),
})

export const DatasetColumnSchema = z.object({
  name: z.string(),
  display_name: z.string(),
  data_type: z.string(),
  semantic_role: z.string().nullable(),
  missing_percent: z.number(),
  unique_count: z.number().optional(),
  sample_values: z.array(z.any()).optional(),
  min_value: z.any().nullable().optional(),
  max_value: z.any().nullable().optional(),
})

export const DatasetProfileResponseSchema = z.object({
  dataset_id: z.string().uuid(),
  row_count: z.number(),
  quality_score: z.number(),
  warnings: z.array(z.string()),
  columns: z.array(DatasetColumnSchema),
})

export const DatasetSchemaResponseSchema = z.object({
  dataset_id: z.string().uuid(),
  columns: z.array(DatasetColumnSchema),
})

// -----------------------------------------------------------------------------
// Ask (NLQ) Contracts
// -----------------------------------------------------------------------------

export const ClarificationRequiredSchema = z.object({
  code: z.string(),
  message: z.string(),
})

export const AnalyticsIntentSchema = z.object({
  intent: z.string(),
  metric: z.string().nullable(),
  aggregation: z.string().nullable(),
  group_by: z.array(z.string()),
  date_range: z.record(z.any()).nullable(),
  filters: z.array(z.record(z.any())),
  sort: z.record(z.any()).nullable(),
  limit: z.number().nullable(),
  chart_hint: z.string().nullable(),
})

export const ChartPayloadSchema = z.object({
  chart_type: z.string(),
  data: z.array(z.record(z.any())),
  config: z.record(z.any()),
  meta: z.record(z.any()).optional(),
})

export const AskResponseSchema = z.object({
  answer_id: z.string().uuid(),
  session_id: z.string().uuid(),
  summary: z.string(),
  chart: ChartPayloadSchema.nullable(),
  query_plan: AnalyticsIntentSchema.nullable(),
  confidence: z.string(),
  suggested_followups: z.array(z.string()),
  clarification_required: ClarificationRequiredSchema.nullable(),
  debug_sql: z.string().nullable().optional(),
})
export type AskResponse = z.infer<typeof AskResponseSchema>

// -----------------------------------------------------------------------------
// Widget & Dashboard Contracts
// -----------------------------------------------------------------------------

export const WidgetSchema = z.object({
  id: z.string().uuid(),
  dashboard_id: z.string().uuid(),
  dataset_id: z.string().uuid().nullable(),
  title: z.string(),
  widget_type: z.string(),
  query_text: z.string().nullable(),
  config: z.object({
    chart_payload: ChartPayloadSchema.optional(),
    query_plan: AnalyticsIntentSchema.nullable().optional(),
    source: z.object({
      type: z.string(),
      id: z.string().uuid(),
    }).optional()
  }),
  position: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type Widget = z.infer<typeof WidgetSchema>

export const DashboardLayoutResponseSchema = z.object({
  dashboard_id: z.string().uuid(),
  layout: z.array(z.object({
    widget_id: z.string().uuid(),
    position: z.number(),
  }))
})

// -----------------------------------------------------------------------------
// Insight & Anomaly Contracts
// -----------------------------------------------------------------------------

export const InsightSchema = z.object({
  id: z.string().uuid(),
  dataset_id: z.string().uuid().nullable(),
  title: z.string(),
  body: z.string(),
  insight_type: z.string(),
  severity: z.string(),
  score: z.number().nullable(),
  metadata: z.record(z.any()),
  created_at: z.string(),
})
export type Insight = z.infer<typeof InsightSchema>

export const AnomalySchema = z.object({
  id: z.string().uuid(),
  dataset_id: z.string().uuid().nullable(),
  detector_type: z.string(),
  metric_name: z.string().nullable(),
  severity: z.string(),
  explanation: z.string().nullable(),
  anomaly_payload: z.record(z.any()),
  created_at: z.string(),
})
export type Anomaly = z.infer<typeof AnomalySchema>
