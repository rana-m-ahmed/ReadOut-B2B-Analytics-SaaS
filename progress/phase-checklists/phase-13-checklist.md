# Phase 13 Checklist: Responsive App Shell & Navigation Guarding

- [x] Create app directory route tree (`(marketing)`, `(auth)`, `(onboarding)`, `(dashboard)`) per architecture design.
- [x] Stub all pages with placeholder content.
- [x] Implement layout-level guard for `(dashboard)` to redirect unauthenticated traffic to `/`.
- [x] Verify Playwright smoke tests for direct URL access (200 OKs, guards catch).
- [x] Implement `AppShell`, `Sidebar`, `TopBar`, and `MobileNav`.
- [x] Ensure floating dock design matches tokens (`--shadow-dock`, `--radius-card`, detached margins).
- [x] Verify Zustand sidebar toggle functionality via RTL tests.
- [x] Verify viewport width hide/show logic via RTL tests.
- [x] Verify in-app click navigation reaches all `(dashboard)` routes correctly.
- [x] Validate cross-breakpoint visual constraints to ensure the shell reads as floating, not edge-to-edge.
- [x] Run full frontend E2E & unit suite successfully.
