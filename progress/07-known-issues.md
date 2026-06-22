# Known Issues

- **Phase 7 (Anomalies):### 11.2 Design Verification
1.  **Metric alignment:** The `--font-sans` numbers vs tabulated numeric presentation across multiple metric cards should be verified once real dataset digits replace the `10,000` stubs.
2.  **Marketing Asset Placeholder:** The "canned demo sequence" asset on the marketing page is currently implemented entirely via CSS/HTML/Framer Motion. If a pixel-perfect recorded GIF/Video asset is provided later, it can replace the `<HeroDemoSequence />` component.
  - **Issue**: Standard deviation across rolling windows for revenue by category/region can occasionally become incredibly small (approaching zero variance). When this happens, even a normal daily fluctuation produces an astronomically high Z-Score (e.g., $Z > 200$), which drowns out genuine macro anomalies like the seeded 45% drop.
  - **Resolution/Tuning**: Added explicit noise-filtering clauses to the DuckDB Z-Score queries: `std > 0.05 * mean AND abs(val - mean) > 0.2 * mean`. This enforces that a point is only flagged if the absolute deviation from the rolling mean is at least 20%, explicitly discarding microscopic noise and correctly surfacing the seeded April 2025 anomaly to the top of the pile.
  - **Performance Optimization**: Generating a separate DuckDB chart query for every anomaly caused the suite to hang. Resolved by formatting one already-fetched result per detector query and sharing that capped chart payload across its anomaly records.

- **Resolved 2026-06-22: Phase 3.5 chart-payload choke-point drift**
  - **Issue found**: anomaly detectors imported `result_formatter` but returned `chart_payload=None`, so anomaly persistence had no formatter-produced payload. `/ask` also appended `meta.intent` after formatter cap enforcement, meaning the exact persisted JSON was not the value that had been sized.
  - **Resolution**: anomaly scans now format one shared chart per detector query/result and reuse it across matching anomaly records; `/ask` supplies intent metadata to `format_results()` before sizing. Insight scanners already used `format_results()`, insight/anomaly prose writers do not construct charts, and widget pinning continues to copy the upstream formatted payload unchanged.
  - **Backstop**: repositories now reject oversized inserts and updates for `ask_messages.chart_spec`, `widgets.config`, `insights.metadata`, and `anomalies.anomaly_payload` with `JsonPayloadTooLargeError`. The live four-path hygiene test passes without this backstop firing during normal formatter-driven persistence.

- **Security audit 2026-06-22: confirmed already fine**
  - **Service-role key leakage**: app code does not log request headers or config values; `SUPABASE_SERVICE_ROLE_KEY` is only consumed in `app/db/supabase_client.py`, request logging emits only method/path/status/duration/request_id, and the stray `/ask` debug prints were removed. The only real key found during grep was in local `apps/api/.env`, which is ignored by root `.gitignore` and is not tracked by git.
  - **Dataset upload validation coverage**: every CSV-ingest path still invokes `validate_csv_upload()` from `security/file_guard.py`. Verified callers are `datasets/upload_service.py` for real uploads and `api/routes_datasets.py` when profiling stored raw CSV bytes.
  - **Groq data minimization**: full datasets are not sent to Groq. `nlq/prompt_builder.py` sends only schema metadata plus escaped display-name hints, and `/ask` calls `generate_summary()` with `chart_payload.data[:10]`, not the full query result or dataframe.
  - **DuckDB safety inheritance**: only `analytics/duckdb_engine.py` opens DuckDB connections. Later-added insight/anomaly modules execute through `execute_dataset_query()` rather than opening their own connection paths, so they inherit the existing keyword backstop, parameter binding, timeout, and row-cap controls.
  - **CORS strictness**: `main.py` uses `allow_origins=resolved_settings.ALLOWED_ORIGINS` with no wildcard fallback, `config.py` parses only an explicit allowlist, and no committed config file in git sets `ALLOWED_ORIGINS=*`.

- **Resolved in repo 2026-06-22, still requires live migration application: anonymous TTL expiry RLS gap**
  - **Issue found**: the live Supabase project still allowed an anonymous user to read their own expired workspace and child dataset until cleanup ran. This violated the intended guarantee that expiry immediately revokes access.
  - **Resolution in repo**: added `apps/api/migrations/0005_anon_expiry_rls.sql` so `owns_workspace()` denies expired anonymous workspaces and `workspaces.workspace_owner_access` enforces the same `expires_at > now()` rule directly on workspace rows.
  - **Verification**: the new live test `apps/api/tests/integration/test_anon_workspace_expiry.py` fails against the current live project before `0005` is applied, proving the gap was real. After the migration is applied to the live database, this test should pass and the issue can be considered fully closed in deployment as well as in code.

- **Resolved 2026-06-22: `/ask` trusted monkeypatched/raw LLM payloads too much**
  - **Issue found**: the new adversarial suite showed that `/ask` assumed `get_intent()` always returned an already-valid typed `AnalyticsIntent`. A malformed dict from a patched or future-regressed LLM boundary could therefore crash before reaching validator/compiler safety checks.
  - **Resolution**: `routes_ask.py` now re-validates any returned payload through `analytics_intent_adapter.validate_python()` and degrades malformed payloads into a clean `clarification_required` response. Nonexistent-column payloads still flow into `intent_validator`, which rejects them before DuckDB execution.
  - **Verification**: `apps/api/tests/integration/test_adversarial.py` now passes its malformed-payload, prompt-injection, cross-workspace dataset, and SQL-adversarial cases end to end.

- **Accepted golden-suite misses as of 2026-06-22 (`23/25` pass)**
  - **Q17: "Which weekday has the most orders?"**
  - **Why it still misses**: the current analytics intent contract has only safe internal column references; it does not yet have a first-class `time_grain` / derived-dimension field for transformations like weekday extraction from `order_date`. Treating this as "orders by order_date" would be a misleading fake fix, so it remains an intentional miss until the schema/compiler are extended honestly.
  - **Q24: "Show revenue and orders together."**
  - **Why it still misses**: the current contract is single-metric by design. A faithful answer needs a multi-metric intent plus chart/formatter support for paired series, not a disguised one-metric fallback that only mentions one side of the request.
  - **Status**: acceptable for this phase because the live golden suite now exceeds the pass bar at `23/25`, and both misses are traceable contract gaps rather than random reliability failures.

- **Phase 8 (Primitives): Full Visual QA Required**
  - **Issue**: RTL tests verify that token CSS variables (e.g., `var(--shadow-float)`, `var(--surface)`) are applied to the generated DOM elements, but cannot guarantee the actual visual rendering output in the browser (e.g., how the Framer Motion scale-back effect interacts with z-index in practice).
  - **Status**: Full visual QA for these primitives is a manual step at this phase's validation gate, not something CI can verify.
