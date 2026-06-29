# Readout

Analytics that answers back. Connect a dataset, ask what changed, and receive a visual answer with the reasoning behind it.

[![Live Demo](https://img.shields.io/badge/Live-Demo-blue.svg)](https://readout-demo.vercel.app/)

![Dashboard Preview](./dashboard-preview.png)
*(Note: Replace with actual screenshot path once deployed)*

## Features

- **Ask naturally:** Turn plain-English questions into traceable analysis.
- **See the signal:** Get the right visual, a concise answer, and useful follow-ups.
- **Stay grounded:** Every answer is constrained by your actual dataset schema.
- **Data sources:** Upload CSV datasets and securely profile them.
- **Insights & Anomalies:** Discover hidden patterns and be notified of anomalies in your data.
- **Demo mode:** Start without an account using a curated dataset.
- **Accessibly Designed:** Full keyboard navigation, `prefers-reduced-motion` support, and zero critical axe-core violations.

## Tech Stack

- **Frontend:** Next.js 16 (React 19), Turbopack
- **Styling:** Tailwind CSS v4, Framer Motion, Vanilla CSS (Design tokens, no shadcn)
- **State Management:** Zustand, React Query
- **Data Visualization:** Recharts
- **Validation:** Zod
- **Testing:** Vitest, Playwright (100% E2E coverage for auth & golden flows), Axe-core
- **Backend/Auth:** Supabase, Python (API)

## Local Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   cd apps/web
   npm install
   ```
3. Configure environment variables in `apps/web/.env`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

## Deployment Notes

- The frontend client defaults to the deployed backend at `https://rana-m-ahmed-readout.hf.space`.
- For local development, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `apps/web/.env`.
- A committed template lives in [apps/web/.env.example](./apps/web/.env.example) for GitHub pushes and hosting setup.

## Vercel Frontend Variables

Set these in Vercel for the frontend project:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE_URL=https://rana-m-ahmed-readout.hf.space`
- `NEXT_PUBLIC_MAX_UPLOAD_MB` (optional, defaults to `25`)

Do not add Supabase service-role or Groq keys to Vercel. Those belong only in the backend deployment.

## Testing & Verification

Readout maintains a strict testing pipeline:
- **Static Checks:** Custom script enforces no stray hex colors, no direct `fetch` outside API clients, and no `TODO`s.
- **Unit/Component:** Vitest coverage for all UI state, motion springs, and auth forms.
- **E2E & Visual QA:** Playwright tests for full auth matrix, anonymous demo flow, and CSV onboarding.
- **Accessibility:** Axe-core integrated in E2E tests for zero critical/serious violations on all public/auth/dashboard routes.

Run the suites locally:
```bash
npm run static-check
npm run typecheck
npm run lint
npm run test
npm run test:e2e
```

## Architecture

Readout is organized as a monorepo (see `progress/09-frontend-architecture-state.md` for full diagram):
- `apps/api`: Python backend for processing data and answering queries.
- `apps/web`: Next.js 16 frontend application using route groups `(auth)`, `(dashboard)`, `(marketing)`.

## Known Limitations & Production Upgrade Path

- **Portfolio project:** This is a portfolio piece, not a fully-fledged commercial SaaS.
- **Single-metric queries only:** The current NLP to SQL engine handles single-metric queries.
- **No real-time:** Updates require manual refresh or interaction.
- **Production Upgrade:** To scale this to production, we would need: PostgreSQL row-level security implementation, Redis rate-limiting on Groq calls, streaming UI for LLM responses, and Playwright sharding across Vercel deployments.
