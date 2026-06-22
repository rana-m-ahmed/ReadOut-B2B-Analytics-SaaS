# Phase 17 & 18 Checklist

## Ask UI & Chart Integration
- [x] AskBar renders correctly with frontend-only staged loading sequences.
- [x] AskThread maintains a persistent, never-auto-clearing conversation history.
- [x] Charts render correctly for standard questions:
  - Line charts for trends
  - Bar/Donut charts for distributions
  - Scatter plots for correlations
  - Metric cards for single values
- [x] Data formatting applied consistently across all charts via `lib/format.ts`.
- [x] `meta.truncated: true` is honored with honest "Showing N of M data points" messages.
- [x] Category colors (`categoryColorMap`) are stable across the session.
- [x] Deliberately ambiguous questions trigger the structured Clarification UI cleanly.
- [x] Backend failures or `UpstreamLLMError` gracefully degrade to calm try-again messages (never blank screens or crashes).

## Query Plan Drawer
- [x] Connected to Zustand `queryPlanDrawer` state.
- [x] Renders as a full-height right-side drawer via framer-motion.
- [x] Applies `MODAL_OPEN` spatial transition rule (canvas scale-back and backdrop blur).
- [x] Extracts and renders the correct `query_plan` JSON from the clicked message.
- [x] Extracts and renders the executed `debug_sql` correctly.
- [x] Preserves thread scroll state when opening/closing.

## Code Quality & CI
- [x] Vitest suites pass for `AskBar`, `AskThread`, and `QueryPlanDrawer`.
- [x] Framer-motion animation presets used appropriately.
