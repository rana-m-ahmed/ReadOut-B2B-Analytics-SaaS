# Phase 12 Checklist

## React Query and Zustand Implementation
- [x] Create `lib/api/queryKeys.ts` as the single source of truth for all `react-query` keys.
- [x] Implement a single `QueryClientProvider` with deliberate, documented `staleTime` overrides per query type (e.g. ~60s for ask-adjacent data, ~5min for datasets/schema).
- [x] Wrap the Next.js app layout with the `QueryClientProvider`.
- [x] Implement `lib/store/useAppStore.ts` using Zustand.
- [x] Add Zustand state for `sidebarCollapsed`, `activeDatasetId`, `currentAskSessionId`, and `queryPlanDrawer`.
- [x] Add deterministic `categoryColorMap` logic to assign colors from the premium OKLCH chart tokens (`var(--color-chart-1)` through `var(--color-chart-5)`).

## Cold-Start Indicator
- [x] Implement the `ColdStartIndicator` component.
- [x] Use `useIsFetching` and a 2.5s timer to non-blocking display "Waking up the backend — this can take up to a minute on first load".
- [x] Automatically dismiss the indicator on success.
- [x] Add `ColdStartIndicator` to the global layout.

## API Client & Contracts Verification
- [x] Re-read `progress/11-frontend-api-integration-map.md` and `progress/03-api-contracts.md`.
- [x] Verify every contract has a corresponding typed client function with zero drift. *(Fixed `POST /ask` path and payload body drift from `/datasets/{id}/ask`).*
- [x] Verify both anonymous demo auth and real-user auth paths work against the live Supabase project.
- [x] Manually verify the cold-start UX against a sleeping backend instance.

## Testing & State Logging
- [x] Write Vitest coverage for `queryKeys`, `useAppStore` logic, and `ColdStartIndicator` exit/enter timer logic.
- [x] Verify all frontend state tests pass.
- [x] Update `progress/09-frontend-architecture-state.md` with new `lib/api/` and `lib/store/` references.
- [x] Update `progress/10-design-system-state.md` with `categoryColorMap` details.
- [x] Append test results to `progress/06-test-log.md`.
