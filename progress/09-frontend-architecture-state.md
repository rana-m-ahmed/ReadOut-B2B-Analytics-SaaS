# Frontend Architecture State

- `apps/web/app/`: Route tree implemented per §7.2. `(marketing)` page fully implemented. Layout guard for `(dashboard)` implemented.
- `apps/web/app/`: Route tree implemented per §7.2 and fully stubbed. Layout guard for (dashboard) implemented.
- `apps/web/components/data/`: Data ingestion primitives. `CsvUploader` handles client-side validation, drag-and-drop, and the 3-step upload API sequence. `SchemaPreview` renders the `ProfileResponse` summary and columns (explicitly omitting internal `name`). `DatasetList` and `DatasetCard` render the dashboard data sources list, quality badges, and expandable column profiles.
- `apps/web/components/charts/`: Data visualization factory. `ChartRenderer` dynamically loads `LineChartCard`, `BarChartCard`, `DonutChartCard`, etc., based on backend `chart.type`. Handles `meta.truncated` enforcement and unsupported fallbacks via `ChartEmptyState`.
- `apps/web/components/ask/`: Ask conversational UI primitives. `AskBar` manages the NLQ input and frontend-only staged loading sequence. `AskThread` manages the persistent, scrollable chat history. `AskMessage` renders individual questions, chart payloads, tables, and handles graceful degradation for LLM timeouts/errors. It also renders suggested follow-up chips that share the same `useAppStore.submitAskQuestion` path as `AskBar`. `QueryPlanDrawer` implements a debug surface to review the internal LLM intent and executed SQL safely without polluting the thread.
- `apps/web/components/dashboard/`: Dashboard primitives. `DashboardGrid` handles the masonry layout, widget sizing tokens, and the 4 data states (empty/loading/error/populated). `MetricCard` handles the display of a synthetic `AskResponse` or raw `ChartPayload`, conditionally rendering the delta-trend UI, a Recharts sparkline, and LLM-summary tooltips.
- `apps/web/components/layout/`: AppShell, Sidebar, TopBar, and MobileNav implemented.
- `apps/web/components/onboarding/`: Onboarding workflows. `WalkthroughStepper` manages the persistent dismissible 3-step feature tour via `localStorage`.
- `apps/web/features/`: stubbed, no logic
- `apps/web/lib/`: `api/` client/types/queryKeys implemented. `supabase/` client implemented. `store/` Zustand implemented. `auth/` hooks implemented. `dashboard/` handles `useKpiMetrics` caching layer and `kpiQuestions.ts` definitions. `format.ts` implements explicit value formatters. `motion.ts` implements reusable Framer Motion primitives.
- `apps/web/stores/`: Deprecated in favor of `lib/store/useAppStore.ts`
- `apps/web/styles/`: stubbed, no logic
- `apps/web/tests/`: RTL tests added for primitives
