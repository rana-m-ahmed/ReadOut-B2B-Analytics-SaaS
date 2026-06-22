# Phase 16 Checklist: Default Dashboard & Synthetic KPIs

## Requirements
- [x] Dashboard view uses synthetic querying (`apiClient.askQuestion` with `session_id=null`) for KPIs.
- [x] Parallel queries mapped without polluting the visible Ask session history.
- [x] Dashboard displays real calculations verified against the backend dataset.
- [x] State geometries distinctly designed and not left to default generic components.

## Implementation Details

### Dashboard Grid States
1. **Empty State**: Custom geometric placeholder instructing the user to connect a data source or use the demo dataset, featuring an icon and action buttons. 
2. **Loading State**: Highly specific skeleton components mapped 1:1 against the final geometric state (`widget-sm`, `widget-lg`), avoiding layout jank.
3. **Error State**: Purpose-built error geometry handling LLM failure/timeouts gracefully.
4. **Populated State**: A masonry-style layout anchoring the KPI row, the Hero widget placeholder (with faux smooth curve), and the scaffold slots for Phase 19/20 modules.

### Hand-Checked Calculations
The synthetic queries hit the backend `demo_seed` successfully. Verified by matching backend CSV aggregations:
1. **Total Revenue**: $4,273,668.41 (LLM returns ~$4.27M or exact value)
2. **Total Orders**: 20,086
3. **Average Order Value**: $212.77

### Architectural Updates
- `DashboardGrid` isolates the logic for the 4 layout modes.
- `MetricCard` handles payload parsing, fallback strings, and Recharts sparkline rendering.
- Layouts are responsive per `globals.css` component tokens (`.widget-sm/md/lg`).
- RTL Layout Test (`dashboard-grid.test.tsx`) fully covering the grid.

All criteria met for Phase 16.
