import { apiFetch } from "./client"
import {
  AskResponse,
  Dataset,
  DatasetProfileResponseSchema,
  DatasetSchemaResponseSchema,
  UploadUrlResponseSchema,
  Widget,
  Insight,
  Anomaly,
  DashboardLayoutResponseSchema
} from "./types"

export async function uploadDatasetUrl(filename: string, fileSizeBytes: number, description?: string) {
  const data = await apiFetch<unknown>("/datasets/upload-url", {
    method: "POST",
    body: JSON.stringify({ filename, file_size_bytes: fileSizeBytes, description }),
  })
  return UploadUrlResponseSchema.parse(data)
}

export async function profileDataset(datasetId: string) {
  const data = await apiFetch<unknown>(`/datasets/${datasetId}/profile`, { method: "POST" })
  return DatasetProfileResponseSchema.parse(data)
}

export async function listDatasets(): Promise<Dataset[]> {
  // Use explicit array check/validation here or assume trust, since array of schema is fine
  const data = await apiFetch<Dataset[]>("/datasets", { method: "GET" })
  return data // Usually we'd map via z.array(DatasetSchema).parse(data), assuming apiFetch types are enough
}

export async function getDatasetSchema(datasetId: string) {
  const data = await apiFetch<unknown>(`/datasets/${datasetId}/schema`, { method: "GET" })
  return DatasetSchemaResponseSchema.parse(data)
}

export async function ask(datasetId: string, question: string, sessionId?: string): Promise<AskResponse> {
  const body: Record<string, string> = { dataset_id: datasetId, question }
  if (sessionId) {
    body.session_id = sessionId
  }
  const data = await apiFetch<AskResponse>(`/ask`, {
    method: "POST",
    body: JSON.stringify(body),
  })
  // Let the zod schema parse through usage if wanted, here we trust the type mapping
  return data
}

export async function listInsights(datasetId: string): Promise<Insight[]> {
  return await apiFetch<Insight[]>(`/datasets/${datasetId}/insights`, { method: "GET" })
}

export async function generateInsights(datasetId: string): Promise<Insight[]> {
  return await apiFetch<Insight[]>(`/datasets/${datasetId}/insights/generate`, { method: "POST" })
}

export async function pinInsight(dashboardId: string, insightId: string, title?: string, position?: number): Promise<Widget> {
  return await createWidget(dashboardId, "insight", insightId, title, position)
}

export async function listAnomalies(datasetId: string): Promise<Anomaly[]> {
  return await apiFetch<Anomaly[]>(`/datasets/${datasetId}/anomalies`, { method: "GET" })
}

export async function scanAnomalies(datasetId: string): Promise<Anomaly[]> {
  return await apiFetch<Anomaly[]>(`/datasets/${datasetId}/anomalies/scan`, { method: "POST" })
}

export async function dismissAnomaly(anomalyId: string): Promise<void> {
  await apiFetch(`/anomalies/${anomalyId}`, { method: "DELETE" })
}

export async function createWidget(
  dashboardId: string,
  sourceType: "ask_message" | "insight" | "anomaly",
  sourceId: string,
  title?: string,
  position?: number
): Promise<Widget> {
  const body: Record<string, unknown> = { dashboard_id: dashboardId, source_type: sourceType, source_id: sourceId }
  if (title) body.title = title
  if (position !== undefined) body.position = position

  return await apiFetch<Widget>("/widgets", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export async function listWidgets(dashboardId: string): Promise<Widget[]> {
  return await apiFetch<Widget[]>(`/dashboards/${dashboardId}/widgets`, { method: "GET" })
}

export async function updateWidget(widgetId: string, title?: string, position?: number): Promise<Widget> {
  const body: Record<string, unknown> = {}
  if (title) body.title = title
  if (position !== undefined) body.position = position

  return await apiFetch<Widget>(`/widgets/${widgetId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
}

export async function deleteWidget(widgetId: string): Promise<void> {
  await apiFetch(`/widgets/${widgetId}`, { method: "DELETE" })
}

export async function reorderWidgets(dashboardId: string, widgets: { widget_id: string; position: number }[]) {
  const data = await apiFetch<unknown>(`/dashboards/${dashboardId}/layout`, {
    method: "PATCH",
    body: JSON.stringify({ widgets }),
  })
  return DashboardLayoutResponseSchema.parse(data)
}
