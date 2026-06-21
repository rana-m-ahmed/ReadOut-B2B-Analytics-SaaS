# Known Issues

- **Phase 7 (Anomalies): Detector Threshold Tuning**
  - **Issue**: Standard deviation across rolling windows for revenue by category/region can occasionally become incredibly small (approaching zero variance). When this happens, even a normal daily fluctuation produces an astronomically high Z-Score (e.g., $Z > 200$), which drowns out genuine macro anomalies like the seeded 45% drop.
  - **Resolution/Tuning**: Added explicit noise-filtering clauses to the DuckDB Z-Score queries: `std > 0.05 * mean AND abs(val - mean) > 0.2 * mean`. This enforces that a point is only flagged if the absolute deviation from the rolling mean is at least 20%, explicitly discarding microscopic noise and correctly surfacing the seeded April 2025 anomaly to the top of the pile.
  - **Performance Optimization**: Generating charts via DuckDB for every single anomaly detected across all queries caused the suite to hang. Chart generation was deferred, allowing detection to scan 14,000+ points across all dimensions in under 1 second.
