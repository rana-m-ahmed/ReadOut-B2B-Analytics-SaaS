# Phase 3 Checklist: Core Analytics Engine

## 1. Intent Validation
- [x] Create Pydantic intent schemas for standard analytics queries (time series, comparisons, top-n, correlations, etc.)
- [x] Implement semantic intent validator to map intents against real dataset schema safely
- [x] Handle high-cardinality group by clauses gracefully using limits
- [x] Implement robust filtering rejection (e.g. unsupported operators or fields)

## 2. DuckDB Execution
- [x] Build DuckDB query engine against temporary normalized parquet files
- [x] Parameterize execution variables safely
- [x] Implement runtime row capping (`MAX_RESULT_ROWS`)
- [x] Implement execution timeouts (`QUERY_TIMEOUT_SECONDS`)
- [x] Reject DDL/DML and malicious keyword SQL patterns (`DROP`, `ATTACH`)

## 3. Query Compilation
- [x] Implement `query_compiler.py` translating validated intents into parameterized SQL
- [x] Prevent raw filter values from concatenating directly into SQL strings
- [x] Support time series truncations safely
- [x] Support top/bottom `LIMIT` translations

## 4. Output Formatting & Payload Cap
- [x] Create deterministic shape-to-chart-type mapping (`chart_recommender.py`)
- [x] Apply automatic readability formats (currencies, percentages, integers, etc.)
- [x] Enforce JSON string payload capping (`MAX_CHART_PAYLOAD_KB`) using central single choke point
- [x] Use evenly spaced sampling rather than naive head-cut for time-series payload truncation

## 5. Security & Stability Gates
- [x] Validate malicious filter strings don't cause SQL injection
- [x] Pass comprehensive unit test suite covering above requirements
- [x] Establish full E2E query pipeline test against demo dataset (`test_query_pipeline_e2e.py`)
- [x] Pass `ruff check` on Phase 3 files
