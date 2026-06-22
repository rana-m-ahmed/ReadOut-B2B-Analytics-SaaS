# Env Config

Cross-check source of truth: `apps/api/app/core/config.py::Settings`

Required in every real deployment:

- `SUPABASE_URL`: Supabase project base URL. Required because `Settings` has no default.
- `SUPABASE_SERVICE_ROLE_KEY`: Backend-only Supabase credential used by repositories and Storage service. Required.
- `SUPABASE_JWT_SECRET`: Secret used by `security/auth_guard.py` to verify Supabase JWTs. Required.
- `SUPABASE_ANON_KEY`: Supabase anonymous key retained for server-side flows that may need it. Required.
- `GROQ_API_KEY`: Groq API key for NLQ intent generation and summaries. Required.

Optional with code defaults:

- `GROQ_PRIMARY_MODEL`: Default `llama-3.3-70b-versatile`.
- `GROQ_FALLBACK_MODEL`: Default `llama-3.1-8b-instant`.
- `ALLOWED_ORIGINS`: Comma-separated CORS allowlist. Default empty list. Example: `https://app.example.com,https://staging.example.com`
- `ENVIRONMENT`: Default `development`.
- `MAX_UPLOAD_MB`: Default `25`.
- `QUERY_TIMEOUT_SECONDS`: Default `10`.
- `MAX_RESULT_ROWS`: Default `500`.
- `MAX_CHART_PAYLOAD_KB`: Default `50`.
- `ANON_SESSION_TTL_HOURS`: Default `72`.
- `ASK_CONTEXT_TURN_LIMIT`: Default `4`.
- `ASK_RATE_LIMIT_REQUESTS`: Default `20`.
- `ASK_RATE_LIMIT_WINDOW_SECONDS`: Default `60`.
- `UPLOAD_URL_RATE_LIMIT_REQUESTS`: Default `10`.
- `UPLOAD_URL_RATE_LIMIT_WINDOW_SECONDS`: Default `60`.

Deployment notes:

- Render needs exactly the variables above. There is no additional hidden config path outside `Settings`.
- Hugging Face Spaces is not maintained as a verified deployment target in the current repo state, so there is no separately-supported Spaces-only env set.
- `/health` makes no outbound Supabase or Groq call; however, `uvicorn app.main:app` still requires the five mandatory settings above because `Settings` validates them during app import.
- `ALLOWED_ORIGINS` is parsed from a comma-separated string into a list. Empty or unset means no browser origins are allowed by CORS.
- Groq provider-side rate limits are intentionally not modeled as env vars; backoff is reactive in `nlq/groq_client.py`.

Field-by-field drift check against `Settings` on 2026-06-22:

- No missing env vars in this document relative to `core/config.py`.
- No extra documented env vars that `core/config.py` does not read.
