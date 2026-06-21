# Architecture State

Status: backend foundation is implemented across app bootstrap, config, errors, repositories, migrations, and auth scaffolding. The tree snapshot below is historical and no longer an accurate "all files are stubbed" description.

```text
progress/
├── 00-protocol.md (project protocol)
├── 01-architecture-state.md (stubbed, no logic)
├── 02-decisions-log.md (stubbed, no logic)
├── 03-api-contracts.md (stubbed, no logic)
├── 04-schema-state.md (stubbed, no logic)
├── 05-env-config.md (stubbed, no logic)
├── 06-test-log.md (stubbed, no logic)
├── 07-known-issues.md (stubbed, no logic)
├── 08-golden-suite-results.md (stubbed, no logic)
└── phase-checklists/

apps/
└── api/
    ├── requirements.txt (stubbed dependency manifest, no business logic)
    ├── app/
    │   ├── __init__.py (stubbed, no logic)
    │   ├── main.py (stubbed FastAPI bootstrap, no business logic)
    │   ├── core/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── config.py (stubbed, no logic)
    │   │   ├── logging.py (stubbed, no logic)
    │   │   ├── errors.py (stubbed, no logic)
    │   │   └── rate_limit.py (stubbed, no logic)
    │   ├── api/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── routes_auth.py (stubbed, no logic)
    │   │   ├── routes_datasets.py (stubbed, no logic)
    │   │   ├── routes_ask.py (stubbed, no logic)
    │   │   ├── routes_insights.py (stubbed, no logic)
    │   │   ├── routes_anomalies.py (stubbed, no logic)
    │   │   └── routes_widgets.py (stubbed, no logic)
    │   ├── db/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── supabase_client.py (stubbed, no logic)
    │   │   ├── repositories.py (stubbed, no logic)
    │   │   └── models.py (stubbed, no logic)
    │   ├── datasets/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── upload_service.py (stubbed, no logic)
    │   │   ├── profiler.py (stubbed, no logic)
    │   │   ├── schema_inference.py (stubbed, no logic)
    │   │   ├── storage_service.py (stubbed, no logic)
    │   │   └── demo_seed.py (stubbed, no logic)
    │   ├── nlq/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── prompt_builder.py (stubbed, no logic)
    │   │   ├── groq_client.py (stubbed, no logic)
    │   │   ├── schemas.py (stubbed, no logic)
    │   │   ├── intent_validator.py (stubbed, no logic)
    │   │   ├── context_resolver.py (stubbed, no logic)
    │   │   └── safety.py (stubbed, no logic)
    │   ├── analytics/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── duckdb_engine.py (stubbed, no logic)
    │   │   ├── query_compiler.py (stubbed, no logic)
    │   │   ├── chart_recommender.py (stubbed, no logic)
    │   │   ├── result_formatter.py (stubbed, no logic)
    │   │   └── metric_calculator.py (stubbed, no logic)
    │   ├── insights/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── insight_scanner.py (stubbed, no logic)
    │   │   ├── insight_ranker.py (stubbed, no logic)
    │   │   └── insight_writer.py (stubbed, no logic)
    │   ├── anomalies/
    │   │   ├── __init__.py (stubbed, no logic)
    │   │   ├── zscore_detector.py (stubbed, no logic)
    │   │   ├── isolation_forest_detector.py (stubbed, no logic)
    │   │   └── anomaly_explainer.py (stubbed, no logic)
    │   └── security/
    │       ├── __init__.py (stubbed, no logic)
    │       ├── auth_guard.py (stubbed, no logic)
    │       ├── rls_helpers.py (stubbed, no logic)
    │       └── file_guard.py (stubbed, no logic)
    └── tests/
        ├── unit/
        └── integration/
```

Update 2026-06-20:
- `apps/api/app/core/config.py`: implemented.
- `apps/api/app/core/errors.py`: implemented.
- `apps/api/app/core/logging.py`: implemented.
- `apps/api/app/main.py`: implemented app factory, CORS wiring, request logging middleware, typed error handler registration, `/health`, and router registration.
- `apps/api/app/api/routes_auth.py`: wired stub router.
- `apps/api/app/api/routes_datasets.py`: implemented authenticated upload-url, profile, list, and schema routes with repository-scoped workspace resolution and Supabase Storage signed-upload/profile artifact flow.
- `apps/api/app/api/routes_ask.py`: wired stub router.
- `apps/api/app/api/routes_insights.py`: wired stub router.
- `apps/api/app/api/routes_anomalies.py`: wired stub router.
- `apps/api/app/api/routes_widgets.py`: wired stub router.
- `apps/api/app/db/supabase_client.py`: implemented single service-role client choke point.
- `apps/api/app/db/models.py`: implemented typed table and repository payload models.
- `apps/api/app/db/repositories.py`: implemented typed repositories with explicit workspace or equivalent scope filters on every method.
- `apps/api/app/security/auth_guard.py`: implemented Supabase JWT verification, typed current-user resolution, and idempotent anonymous workspace provisioning.
- `apps/api/app/security/auth_guard.py`: finalized malformed-subject handling as typed `401 unauthorized` and kept anonymous workspace provisioning idempotent with seeded demo-dataset reference resolution.
- `apps/api/app/security/rls_helpers.py`: implemented repository-to-RLS policy cross-reference notes.
- `apps/api/app/security/file_guard.py`: implemented CSV upload validation, size enforcement, content sniffing, and filename sanitization/path-traversal rejection.
- `apps/api/app/datasets/storage_service.py`: implemented service-role Supabase Storage uploads for raw CSV, normalized Parquet, profile JSON, and preview JSON under the user/dataset artifact path convention.
- `apps/api/app/datasets/schema_inference.py`: implemented `slugify_column_name()` for safe internal dataset column names, including reserved-word handling and deterministic collision suffixes.
- `apps/api/app/datasets/profiler.py`: implemented structured Polars-only CSV profiling, duplicate-safe `name` / raw `display_name` population, quality scoring, warnings, structured malformed-CSV failures, and Polars-native Parquet generation. Polars only, verified no Pandas import.
- `apps/api/app/datasets/upload_service.py`: implemented upload orchestration for file validation, dataset row creation, artifact storage, real Polars profiler integration, and best-effort dataset status updates compatible with the current live schema.
- `apps/api/app/datasets/demo_seed.py`: implemented shared public demo dataset provisioning through the same upload/profiler/storage pipeline used for real CSV uploads.
- `apps/api/app/analytics/duckdb_engine.py`: implemented trusted single-dataset DuckDB execution against the normalized Parquet artifact resolved through the repository/storage layer. Security review note: it uses native parameter binding for query values, a keyword backstop that rejects DDL/DML and extension-loading SQL before execution, and timeout plus result-cap enforcement as runtime backstops.
- `apps/api/app/nlq/schemas.py`: implemented strict analytics-intent Pydantic models as a discriminated union over supported intent types, with closed-world field validation and internal safe column-name references only.
- `apps/api/app/nlq/intent_validator.py`: implemented semantic intent validation against the real dataset schema, with explicit reject-vs-clamp behavior for invalid columns/types/ranges versus recoverable oversize limits and high-cardinality grouping.
- `apps/api/tests/unit/test_config.py`: implemented.
- `apps/api/tests/unit/test_file_guard.py`: implemented.
- `apps/api/tests/unit/test_schema_inference.py`: implemented.
- `apps/api/tests/unit/test_profiler.py`: implemented.
- `apps/api/tests/unit/test_demo_seed.py`: implemented.
- `apps/api/tests/__init__.py`: implemented.
- `apps/api/tests/unit/__init__.py`: implemented.
- `apps/api/tests/integration/__init__.py`: implemented.
- `apps/api/tests/integration/test_health.py`: implemented.
- `apps/api/tests/integration/test_auth_anonymous.py`: implemented.
- `apps/api/tests/integration/test_migrations_sql_smoke.py`: implemented.
- `apps/api/tests/integration/test_repositories.py`: implemented.
- `apps/api/tests/integration/test_upload_service_live_storage.py`: implemented.
- `apps/api/tests/integration/test_demo_seed_live.py`: implemented.
- `apps/api/migrations/0001_init.sql`: implemented.
- `apps/api/migrations/0002_rls.sql`: implemented.
- `apps/api/migrations/0003_cleanup.sql`: implemented.
- `apps/api/.env.example`: implemented.
- `apps/api/scripts/generate-demo-dataset.py`: implemented fixed-seed demo sales CSV generator.
- `apps/api/scripts/demo-dataset-metadata.json`: implemented fixed anomaly metadata record.
- Phase 0 validation: full test suite passed, full module-tree import sweep passed, and `ruff check apps/api` passed.
- DB rule: the service-role Supabase client is created only in `db/supabase_client.py` and consumed by `db/repositories.py` as the single backend choke point.
- Config update: empty values in `.env` are ignored so typed defaults apply instead of failing integer parsing.
- Live DB validation update: the real Supabase project now exposes the repository tables needed for workspace and dataset CRUD, and the live repository round-trip passed in isolation.
- Test hardening update: the live repository integration test injects a temporary `GROQ_API_KEY` placeholder and retries transient Supabase DNS failures before skipping.
- `apps/api/app/analytics/query_compiler.py`: implemented.
- `apps/api/tests/unit/test_query_compiler.py`: implemented.
- `apps/api/app/analytics/chart_recommender.py`: implemented.
- `apps/api/app/analytics/result_formatter.py`: implemented.
- `apps/api/tests/unit/test_chart_recommender.py`: implemented.
- `apps/api/tests/unit/test_result_formatter.py`: implemented.
