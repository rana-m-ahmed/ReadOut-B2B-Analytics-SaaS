# Known Issues

- **Phase 7 (Anomalies): Detector Threshold Tuning**
  - **Issue**: Standard deviation across rolling windows for revenue by category/region can occasionally become incredibly small (approaching zero variance). When this happens, even a normal daily fluctuation produces an astronomically high Z-Score (e.g., $Z > 200$), which drowns out genuine macro anomalies like the seeded 45% drop.
  - **Resolution/Tuning**: Added explicit noise-filtering clauses to the DuckDB Z-Score queries: `std > 0.05 * mean AND abs(val - mean) > 0.2 * mean`. This enforces that a point is only flagged if the absolute deviation from the rolling mean is at least 20%, explicitly discarding microscopic noise and correctly surfacing the seeded April 2025 anomaly to the top of the pile.
  - **Performance Optimization**: Generating a separate DuckDB chart query for every anomaly caused the suite to hang. Resolved by formatting one already-fetched result per detector query and sharing that capped chart payload across its anomaly records.

- **Resolved 2026-06-22: Phase 3.5 chart-payload choke-point drift**
  - **Issue found**: anomaly detectors imported `result_formatter` but returned `chart_payload=None`, so anomaly persistence had no formatter-produced payload. `/ask` also appended `meta.intent` after formatter cap enforcement, meaning the exact persisted JSON was not the value that had been sized.
  - **Resolution**: anomaly scans now format one shared chart per detector query/result and reuse it across matching anomaly records; `/ask` supplies intent metadata to `format_results()` before sizing. Insight scanners already used `format_results()`, insight/anomaly prose writers do not construct charts, and widget pinning continues to copy the upstream formatted payload unchanged.
  - **Backstop**: repositories now reject oversized inserts and updates for `ask_messages.chart_spec`, `widgets.config`, `insights.metadata`, and `anomalies.anomaly_payload` with `JsonPayloadTooLargeError`. The live four-path hygiene test passes without this backstop firing during normal formatter-driven persistence.
