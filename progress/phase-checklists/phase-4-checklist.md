# Phase 4 Checklist: Query Orchestration & Integration

## 1. Intent Generation
- [x] Integrate Groq client for NLQ intent generation.
- [x] Ensure strict usage of `dataset_columns.name` for internal operations and safe identifiers.
- [x] Configure fallback strategy for `llama-3.3-70b-versatile` down to `llama-3.1-8b-instant`.
- [x] Handle rate limits smoothly using `Retry-After` HTTP headers without hardcoded pauses, bounded by a 30s cap.

## 2. Intent Validation & Compilation
- [x] Integrate semantic intent validator to map parsed intents to actual schema features.
- [x] Translate validation rejections correctly into a typed `ClarificationRequired` response for ambiguous requests.
- [x] Compile validated intents down into parameterized duckdb SQL, injecting values safely.
- [x] Ensure all time series, comparison, proportion, grouped, and metric intents generate runnable queries.

## 3. Query Execution & Formatting
- [x] Feed compiled queries directly into the `duckdb_engine` execution environment.
- [x] Map the shapes of executed result sets deterministically into recommended chart types.
- [x] Formatted result values (currency, percent, integers).
- [x] Integrated lightweight one-sentence summary generation via the LLM fallback model.

## 4. End-to-End Live Validation
- [x] Created `test_routes_ask.py` for golden testing of 5 standard intent types plus an ambiguous clarification intent.
- [x] Executed a manual test script of 10 queries observing real-world Groq quota usage and backoff behaviors.

### Manual Quota & Fallback Observations
- **Rate Limit Trigger**: The primary model (`llama-3.3-70b-versatile`) is easily rate-limited on the free tier when answering >3 consecutive questions in quick succession.
- **Header Parsing**: The `x-ratelimit-reset` parsed successfully but generated huge unmanageable sleep windows; applying a `max(delay, 30.0)` cap successfully forces an early exit/fallback when the limit is heavily exceeded.
- **Fallback Reliability**: The fallback model (`llama-3.1-8b-instant`) kicked in reliably on `429` secondary failures. 
- **Schema Adherence (Fallback)**: The 8B model occasionally hallucinates or breaks the strict JSON schema (e.g. returning `aggregation: null` for a `proportion` intent).
- **Graceful Degradation**: When both models fail (or the fallback emits invalid JSON), the API safely short-circuits to the fallback summary: *"I'm having trouble connecting to my analysis engine right now. Please try again in a moment."* instead of throwing `500 Internal Server Error`.
- **Latency**: Queries without rate limits took ~6-8 seconds end-to-end. Queries that triggered the 30s backoff delay and hit the fallback model took ~33-39 seconds.
