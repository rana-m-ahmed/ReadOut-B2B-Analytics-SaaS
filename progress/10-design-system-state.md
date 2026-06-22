# Design System State

Token spec defined.

  Color: --canvas #F7F9FA, --surface #FFFFFF, --surface-subtle #EEF1F2,
  --ink #111827, --ink-secondary #5B6472, --accent #2A2FED (Ultramarine),
  --accent-on #FFFFFF, --warning #F2A93B (amber — anomalies/alerts only, never red),
  --success #1E9E6E, --danger #D64B3F (destructive confirmations only, never
  anomaly UI), --hairline #E3E8E6.

  Geometry: --radius-control 12px, --radius-card 20px, --radius-modal 24px,
  --radius-pill 999px. Shadows: --shadow-float, --shadow-lift, --shadow-dock per
  the exact rgba values in this document's §0.5.

  Typography: font stack 'Geist', 'Inter Tight', system-ui, sans-serif via
  next/font. Metric style (40-56px desktop, weight 700, tracking -0.02em,
  tabular-nums), Label style (11-12px, weight 600, uppercase, tracking 0.08em,
  ink-secondary), Body style (14-16px, weight 400-500). Tabular figures mandatory
  everywhere a number renders.

  Motion: SPRING_DEFAULT {stiffness:220, damping:26, mass:1}, SPRING_SNAPPY
  {stiffness:320, damping:30, mass:0.9}, HOVER_LIFT (translateY(-3px) +
  shadow-lift), MODAL_OPEN (canvas scale 0.98 + backdrop-blur(8px)).

  Widget Layout Geometries:
  - `.widget-sm`: `col-span-1 row-span-1 min-h-[300px]`
  - `.widget-md`: `col-span-1 md:col-span-2 row-span-1 min-h-[300px]`
  - `.widget-lg`: `col-span-1 md:col-span-2 lg:col-span-3 row-span-2 min-h-[400px]`

  Colors (State): The `categoryColorMap` in Zustand assigns colors dynamically derived from the tailwind CSS variables `var(--color-chart-1)` through `var(--color-chart-5)`, ensuring charts align with the premium global OKLCH theme and dark mode logic.

## Primitives State

- Card: implemented, matches tokens.
- Button: implemented, matches tokens.
- Modal/Drawer wrapper: implemented, matches tokens.
- Tooltip: implemented, matches tokens.
- Skeleton: implemented, matches tokens.
- Metric/Label text: implemented, matches tokens.
- Layout Docks: AppShell Sidebar, TopBar, and MobileNav implemented as true floating docks, detached with margins, matching `--shadow-dock` and `--radius-card`.
- Charts: implemented via `ChartRenderer` and Recharts. Axis borders and gridlines stripped. Smooth sweeping curves used for Line/Area charts in `--accent` or `categoryColorMap`. Smooth `framer-motion` layout animations imported from `lib/motion.ts`.
