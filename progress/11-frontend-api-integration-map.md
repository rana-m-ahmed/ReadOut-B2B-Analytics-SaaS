# Frontend API Integration Map

## Backend to Frontend Mappings

| Backend Endpoint | Frontend Typed Function | Zod Schema |
| --- | --- | --- |
| `POST /datasets/upload-url` | `uploadDatasetUrl` | `UploadUrlResponseSchema` |
| `POST /datasets/{id}/profile` | `profileDataset` | `DatasetProfileResponseSchema` |
| `GET /datasets` | `listDatasets` | `DatasetSchema` |
| `GET /datasets/{id}/schema` | `getDatasetSchema` | `DatasetSchemaResponseSchema` |
| `POST /datasets/{id}/ask` | `ask` | `AskResponseSchema` |
| `GET /datasets/{id}/insights` | `listInsights` | `InsightSchema` |
| `POST /datasets/{id}/insights/generate` | `generateInsights` | `InsightSchema` |
| `GET /datasets/{id}/anomalies` | `listAnomalies` | `AnomalySchema` |
| `POST /datasets/{id}/anomalies/scan` | `scanAnomalies` | `AnomalySchema` |
| `DELETE /anomalies/{id}` | `dismissAnomaly` | `void` |
| `POST /widgets` | `createWidget`, `pinInsight` | `WidgetSchema` |
| `GET /dashboards/{id}/widgets` | `listWidgets` | `WidgetSchema` |
| `PATCH /widgets/{id}` | `updateWidget` | `WidgetSchema` |
| `DELETE /widgets/{id}` | `deleteWidget` | `void` |
| `PATCH /dashboards/{id}/layout` | `reorderWidgets` | `DashboardLayoutResponseSchema` |

## Components
- `lib/api/types.ts`: Holds Zod schemas and inferred types matching `03-api-contracts.md`.
- `lib/api/client.ts`: Exposes `apiFetch` using `@supabase/ssr` to dynamically attach the JWT `Authorization: Bearer` and handles 503 Render cold start retries plus typed error extraction.
- `lib/api/index.ts`: Exposes all fully-typed API methods for React Server Components or Client-side hooks.

### 11.1 Phase 14 / Data Ingestion API Integration
- **`POST /datasets/upload-url`**: Validated. `CsvUploader` pre-validates CSV extension and size (<= 50MB) client-side before calling this to avoid quota burns. Receives `upload_url` and `dataset_id`.
- **`PUT <upload_url>`**: Validated. `CsvUploader` executes a direct binary upload via `XMLHttpRequest` to the signed Supabase storage URL, enabling progress tracking.
- **`POST /datasets/{dataset_id}/profile`**: Validated. Called immediately after upload completes to trigger the backend DuckDB profiling pipeline. The response is passed to `SchemaPreview` for rendering.
- **Error Mapping**: `CsvUploader` maps 413s directly to readable size limits and generic catches to "Server error", hiding raw backend validation tracebacks from the UI.

### 11.2 Phase 15 / Data Sources Dashboard
- **`GET /datasets`**: Validated. Populates the `DatasetList` overview.
- **`GET /datasets/{dataset_id}/profile`**: Validated. Extracted from the backend's persistent JSON store to power the `DatasetCard` quality badge and expandable column table on demand without triggering a heavy DuckDB run.
### 11.3 Phase 16 / Synthetic KPI Queries
- **`POST /ask` (Synthetic)**: Validated. `useKpiMetrics` invokes a parallel battery of canonical questions. We explicitly send `session_id: null` (Shape: `{ query_plan: AnalyticsIntent | null; confidence: "high" | "medium" | "low"; suggested_followups: string[]; clarification_required: { code: string; message: string } | null; debug_sql?: string | null; }`), leveraging backend session-generation behavior to sandbox these queries into isolated orphan sessions, guaranteeing they do not appear in the user's conversational thread history. Results are cached heavily via `useQueries` (5m `staleTime`).

### 11.4 Phase 17 / Chart Payload Integration
The backend's `chart_recommender.py` emits specific chart types based on query result shape. The frontend `ChartRenderer` factory handles them as follows:

| Backend `chart.type` | Frontend Component | Status | Notes |
| :--- | :--- | :--- | :--- |
| `line` | `LineChartCard.tsx` | Supported | Used for single numeric / single date. Smooth curves. |
| `multi_line` | `AreaChartCard.tsx` | Supported | Area chart with overlapping gradients. |
| `bar` | `BarChartCard.tsx` | Supported | Radius tops. |
| `stacked_bar` | `StackedBarChartCard.tsx` | Supported | Stacked dimensions. |
| `donut` | `DonutChartCard.tsx` | Supported | Used for `proportion` intents. Inner radius 60%. |
| `scatter` | `ScatterChartCard.tsx` | Supported | Used for correlations / 2 metrics. |
| `metric_card` | `MetricCard.tsx` | Supported | Wraps ChartPayload natively into the Phase 16 component. |
| `table` | *Unhandled* | Unhandled | Not yet implemented in ChartRenderer. |
| `line_with_highlighted_point` | *Unhandled* | Unhandled | Used for `anomaly_explanation`. Not yet implemented. |

- **Truncation Honesty**: Frontend explicitly renders "Showing N of M data points" via `ChartRenderer` if `meta.truncated` is true.
- **Formatting**: Raw values are formatted purely on the frontend via `lib/format.ts`.
