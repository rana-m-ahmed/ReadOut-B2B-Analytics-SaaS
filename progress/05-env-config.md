# Env Config

- `SUPABASE_URL`: Base Supabase project URL. Default: see `.env.example`.
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service-role credential for backend-only operations. Default: see `.env.example`.
- `SUPABASE_JWT_SECRET`: Supabase JWT verification secret. Default: see `.env.example`.
- `SUPABASE_ANON_KEY`: Supabase anonymous key for flows that need it server-side. Default: see `.env.example`.
- `GROQ_API_KEY`: Groq API credential. Default: see `.env.example`.
- `GROQ_PRIMARY_MODEL`: Primary Groq model name for NLQ workloads. Default: `llama-3.3-70b-versatile`.
- `GROQ_FALLBACK_MODEL`: Fallback Groq model name when primary handling needs a fallback path. Default: `llama-3.1-8b-instant`.
- `ALLOWED_ORIGINS`: Comma-separated CORS origin allowlist. Default: empty list.
- `ENVIRONMENT`: Runtime environment label. Default: `development`.
- `MAX_UPLOAD_MB`: Max dataset upload size in megabytes. Default: `25`.
- `QUERY_TIMEOUT_SECONDS`: Max query execution time budget in seconds. Default: `10`.
- `MAX_RESULT_ROWS`: Max rows returned from analytics queries. Default: `500`.
- `MAX_CHART_PAYLOAD_KB`: Max serialized chart payload size in kilobytes. Default: `50`.
- `ANON_SESSION_TTL_HOURS`: Anonymous/demo session lifetime in hours. Default: `72`.
- `ASK_CONTEXT_TURN_LIMIT`: Max prior turns carried into ask-context resolution. Default: `4`.
- Note: Groq rate limits are NOT a config value — see `groq_client` design note in Phase 4, decisions-log entry.
