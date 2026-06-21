# API Contracts

- Method: `GET`
  Path: `/health`
  Request shape: no body.
  Response shape: `200 OK` with `{"status": "ok", "environment": "<ENVIRONMENT>"}`.

- Method: `POST`
  Path: `/datasets/upload-url`
  Auth: `Authorization: Bearer <jwt>` required via `auth_guard`.
  Request shape:
  `{"filename": "<original filename>", "file_size_bytes": <positive int>, "description": "<optional text or null>"}`
  Response shape:
  `200 OK` with `{"dataset_id": "<uuid>", "upload_url": "<signed storage url>", "storage_path": "users/<user_id>/datasets/<dataset_id>/raw.csv"}`
  Error shape:
  `400` typed `validation_error` when `file_size_bytes` exceeds `Settings.MAX_UPLOAD_MB`, `filename` sanitization fails, or signed-upload URL generation fails.

- Method: `POST`
  Path: `/datasets/{dataset_id}/profile`
  Auth: `Authorization: Bearer <jwt>` required via `auth_guard`.
  Request shape: no body.
  Response shape:
  `200 OK` with
  `{"dataset_id": "<uuid>", "row_count": <int>, "quality_score": <0-100 int>, "warnings": ["..."], "columns": [{"name": "<safe_internal_name>", "display_name": "<original header>", "data_type": "<string|number|boolean|date|category>", "semantic_role": "<time|metric|dimension|identifier>", "missing_percent": <float>, "unique_count": <int>, "sample_values": [<json values>], "min_value": <json scalar or null>, "max_value": <json scalar or null>}]}`
  Notes:
  profiling downloads `raw.csv` from Supabase Storage, validates it again through `file_guard`, persists `normalized.parquet`, `profile.json`, and `preview.json`, updates `datasets.row_count`, and replaces `dataset_columns` for that dataset/workspace scope.
  Error shape:
  `400` typed `validation_error` when the stored object is missing, not valid CSV, or the profiler returns a structured parse failure.

- Method: `GET`
  Path: `/datasets`
  Auth: `Authorization: Bearer <jwt>` required via `auth_guard`.
  Request shape: no body.
  Response shape:
  `200 OK` with
  `[{"id": "<uuid>", "name": "<dataset name>", "description": "<text or null>", "source_type": "<string>", "storage_bucket": "<bucket>", "storage_path": "<path>", "file_size_bytes": <int>, "row_count": <int>, "created_at": "<iso8601>", "updated_at": "<iso8601>"}]`
  Notes:
  query is always scoped through the resolved current workspace from the repository layer.

- Method: `GET`
  Path: `/datasets/{dataset_id}/schema`
  Auth: `Authorization: Bearer <jwt>` required via `auth_guard`.
  Request shape: no body.
  Response shape:
  `200 OK` with
  `{"dataset_id": "<uuid>", "columns": [{"name": "<safe_internal_name>", "display_name": "<original header>", "data_type": "<string|number|boolean|date|category>", "semantic_role": "<time|metric|dimension|identifier|null>", "missing_percent": <float>}]}`
  Notes:
  this route deliberately exposes both `display_name` and internal `name`; the frontend can ignore `name` in normal UI while future debug tooling can show the mapping. `missing_percent` is read from stored `profile.json`, while the rest of the column metadata comes from `dataset_columns`.

- Method: `POST`
  Path: `/ask`
  Auth: `Authorization: Bearer <jwt>` required via `auth_guard`.
  Request shape:
  `{"dataset_id": "<uuid>", "question": "<string>", "session_id": "<uuid|null>"}`
  Response shape:
  `200 OK` with
  `{"answer_id": "<uuid>", "summary": "<string>", "chart": <ChartPayload dict|null>, "query_plan": <AnalyticsIntent dict|null>, "confidence": "high", "suggested_followups": ["..."], "clarification_required": {"code": "<string>", "message": "<string>"} | null}`
  Notes:
  If the LLM determines the question is vague, or the validator rejects it, `clarification_required` is populated and `chart`/`query_plan` are null.

- Internal contract: `groq_client` -> `intent_validator`
  Name: analytics intent JSON schema.
  Purpose:
  this is not a public HTTP contract, but it is the strict structured payload the LLM must emit before query validation and compilation. Every column-bearing field below uses the safe internal `dataset_columns.name` value only, never `display_name`.
  Supported `intent` enum values:
  `single_metric`, `time_series`, `grouped_metric`, `comparison`, `proportion`, `top_n`, `bottom_n`, `correlation`, `anomaly_explanation`, `clarification_required`
  Supported `aggregation` enum values:
  `sum`, `avg`, `count`, `min`, `max`
  Supported filter `operator` enum values:
  `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains`, `not_contains`, `starts_with`, `ends_with`, `between`
  Supported sort `direction` enum values:
  `asc`, `desc`
  Shared field shapes:
  `metric`: `<string|null>`
  `group_by`: `["<internal_column_name>", ...]`
  `date_range`: `{"column": "<internal_column_name>", "preset": "<preset>"}` or `{"column": "<internal_column_name>", "start": "<iso/date string>", "end": "<iso/date string>"}`
  `filters`: `[{"column": "<internal_column_name>", "operator": "<enum>", "value": <json value>}]`
  `sort`: `{"column": "<internal_column_name>", "direction": "asc|desc"}`
  `limit`: `<positive int|null>`
  `chart_hint`: `<string|null>`
  Intent-specific shapes:
  `single_metric`: `{"intent":"single_metric","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":[],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `time_series`: `{"intent":"time_series","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":[],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `grouped_metric`: `{"intent":"grouped_metric","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":["<column>",...],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `comparison`: `{"intent":"comparison","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":["<column>",...],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `proportion`: `{"intent":"proportion","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":["<column>",...],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `top_n`: `{"intent":"top_n","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":["<column>",...],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":<positive int>,"chart_hint":null|"<string>"}`
  `bottom_n`: `{"intent":"bottom_n","metric":"<column>","aggregation":"sum|avg|count|min|max","group_by":["<column>",...],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":<positive int>,"chart_hint":null|"<string>"}`
  `correlation`: `{"intent":"correlation","metric":"<column>","aggregation":null,"group_by":["<column>",...],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `anomaly_explanation`: `{"intent":"anomaly_explanation","metric":"<column>","aggregation":null,"group_by":[],"date_range":null|{...},"filters":[],"sort":null|{...},"limit":null,"chart_hint":null|"<string>"}`
  `clarification_required`: `{"intent":"clarification_required","metric":null,"aggregation":null,"group_by":[],"date_range":null,"filters":[],"sort":null,"limit":null,"chart_hint":null|"<string>"}`
  Validation note:
  the Pydantic layer forbids extra unexpected fields and rejects unsupported enum values before semantic validation begins.
  Validator behavior note:
  after schema parsing, `intent_validator` applies semantic checks against the real dataset schema using internal safe column names only.
  Reject rules:
  nonexistent referenced columns, numeric aggregations (`sum`, `avg`, `min`, `max`) over non-numeric metrics, `date_range.column` targeting a non-date column, unsupported date presets, invalid explicit date ranges (bad ISO date or `start > end`), and filter operators outside the validator allow-list (`eq`, `neq`, `gt`, `lt`, `between`, `in`) are rejected and converted into a structured `clarification_required` result.
  if `limit` is above `Settings.MAX_RESULT_ROWS`, it is silently clamped down to `MAX_RESULT_ROWS`; if any `group_by` column is high-cardinality and no `limit` was provided, the validator force-applies a conservative limit instead of rejecting. This distinction is intentional: unanswerable intents are rejected, but over-broad-yet-answerable intents are normalized and allowed to proceed.

## Compiled SQL Patterns

These are the compiled DuckDB parameterized SQL patterns for each validated intent type:

### `single_metric`
```sql
SELECT sum("revenue") AS value
FROM dataset
WHERE "region" = $filter_0
LIMIT $limit
```

### `time_series`
```sql
SELECT CAST(date_trunc('day', "order_date") AS DATE) AS bucket,
       sum("revenue") AS value
FROM dataset
WHERE "order_date" BETWEEN $date_start AND $date_end
GROUP BY 1
ORDER BY 1 ASC
LIMIT $limit
```

### `grouped_metric`
```sql
SELECT "region",
       sum("revenue") AS value
FROM dataset
WHERE 1=1
GROUP BY 1
ORDER BY value DESC
LIMIT $limit
```

### `comparison`
```sql
WITH current_period AS (
    SELECT sum("revenue") AS current_value
    FROM dataset
    WHERE 1=1 AND "order_date" BETWEEN $current_start AND $current_end
),
previous_period AS (
    SELECT sum("revenue") AS previous_value
    FROM dataset
    WHERE 1=1 AND "order_date" BETWEEN $previous_start AND $previous_end
)
SELECT current_value,
       previous_value,
       current_value - previous_value AS delta_value,
       CASE
           WHEN previous_value IS NULL OR previous_value = 0 THEN NULL
           ELSE (current_value - previous_value) * 1.0 / previous_value
       END AS delta_percent
FROM current_period, previous_period
LIMIT $limit
```

### `proportion`
```sql
WITH grouped AS (
    SELECT "region",
           sum("revenue") AS value
    FROM dataset
    WHERE 1=1
    GROUP BY 1
)
SELECT "region",
       value,
       value * 1.0 / SUM(value) OVER () AS proportion
FROM grouped
ORDER BY value DESC
LIMIT $limit
```

### `top_n`
```sql
SELECT "region",
       sum("revenue") AS value
FROM dataset
WHERE 1=1
GROUP BY 1
ORDER BY value DESC
LIMIT $limit
```

### `bottom_n`
```sql
SELECT "region",
       sum("revenue") AS value
FROM dataset
WHERE 1=1
GROUP BY 1
ORDER BY value ASC
LIMIT $limit
```

### `correlation`
```sql
SELECT 'discount_percent' AS comparison_column,
       corr("revenue", "discount_percent") AS correlation
FROM dataset
WHERE 1=1
LIMIT $limit
```

### `anomaly_explanation`
```sql
WITH anomaly_window AS (
    SELECT avg("revenue") AS anomaly_value
    FROM dataset
    WHERE 1=1 AND "order_date" BETWEEN $current_start AND $current_end
),
baseline_window AS (
    SELECT avg("revenue") AS baseline_value
    FROM dataset
    WHERE 1=1 AND "order_date" BETWEEN $previous_start AND $previous_end
)
SELECT anomaly_value,
       baseline_value,
       anomaly_value - baseline_value AS delta_value,
       CASE
           WHEN baseline_value IS NULL OR baseline_value = 0 THEN NULL
           ELSE (anomaly_value - baseline_value) * 1.0 / baseline_value
       END AS delta_percent
FROM anomaly_window, baseline_window
LIMIT $limit
```

### `clarification_required`
```sql
SELECT 'clarification_required' AS intent,
       $chart_hint AS chart_hint
LIMIT $limit
```
