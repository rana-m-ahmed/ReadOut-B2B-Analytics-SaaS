# Phase 0 Checklist

- Done: `pytest apps/api/tests -v` passed from repo root with required env vars set (`4 passed`).
- Done: `ruff check apps/api` passed from repo root (`All checks passed!`).
- Done: Zero import errors across the current module tree, verified by importing all discovered `app.*` modules from repo root (`imported_modules=48`).
- Done: All Phase 0 tests pass. Reason: config unit tests and `/health` integration test both passed in the full suite.
