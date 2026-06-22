# Phase 7 Checklist

Date verified: 2026-06-22

- [x] Widgets survive a refresh / re-fetch after pin, independent of client cache.
  Evidence: `apps/api/tests/integration/test_routes_widgets.py` performs `POST /widgets` for two pinned ask results, then immediately performs a fresh `GET /dashboards/{dashboard_id}/widgets` and asserts the persisted widget IDs are returned in order. `progress/06-test-log.md` records the live Supabase run on 2026-06-22 as passed.

- [x] Widget reordering is persisted server-side.
  Evidence: `apps/api/tests/integration/test_routes_widgets.py` calls `PATCH /dashboards/{dashboard_id}/layout`, then performs another fresh `GET /dashboards/{dashboard_id}/widgets` and also reads the dashboard row through `DashboardRepository.get_by_id(...)` to confirm both widget positions and `dashboards.layout` were saved, not just echoed back in-memory. `progress/06-test-log.md` records this live round trip as passed on 2026-06-22.

- [x] Phase 7.2 payload-hygiene audit was genuinely run and did not get skipped.
  Evidence: `progress/06-test-log.md` records `pytest apps/api/tests/integration/test_payload_hygiene.py -v -rs` against the live Supabase project as passed on 2026-06-22.

- [x] Phase 7.2 audit found and fixed real drift rather than only asserting everything was already fine.
  Evidence: `progress/07-known-issues.md` logs the resolved issue found on 2026-06-22: anomaly detectors were returning `chart_payload=None`, and `/ask` was mutating `meta.intent` after formatter size enforcement. The resolution notes that anomaly scans now route through shared formatter-produced payloads, `/ask` passes metadata into `format_results()` before sizing, and repositories enforce a JSONB-size backstop.

- [x] Widget payload handling still reuses upstream formatted payloads instead of regenerating them.
  Evidence: `progress/06-test-log.md` for the 2026-06-22 widgets test states the pinned widget reused the real `/ask` chart and query payload without regenerating it, which matches the Phase 3.5 single-choke-point rule reaffirmed in `progress/02-decisions-log.md`.
