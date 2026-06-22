# Phase 15 Verification Checklist: Data Sources & Internal State Safety

## 1. Upload & Onboarding Pipeline
- [x] **CSV Upload Works**: The `CsvUploader` drag-and-drop mechanism accepts files, accurately displays progress, and sequentially fires `POST /upload-url`, `PUT <signed_url>`, and `POST /profile`.
- [x] **Schema Preview Works**: Upon successful upload, the user is navigated to `/schema-preview` where the newly inferred dataset profile renders its metrics and column definitions flawlessly.
- [x] **Readable Errors for Bad CSVs**: If a file exceeds `MAX_UPLOAD_MB` (50MB), the client preemptively intercepts it and renders a clean, user-friendly error without triggering backend tracebacks.

## 2. Data Sources Dashboard Rendering
- [x] **Dataset List Rendering**: `DatasetList` successfully pulls from `GET /datasets` to populate cards for all available datasets.
- [x] **Empty State Grace**: If no datasets exist (e.g. brand new user), the page renders a polite empty state with CTAs to upload or use a demo dataset.
- [x] **Dynamic Quality Score**: Opening a dataset card gracefully fires `GET /datasets/{id}/profile` (directly off storage, bypassing DuckDB) to render the `quality_score` badge and the column details table.

## 3. The "No Internal Leakage" Privacy Rule
- [x] **`SchemaPreview` Verification**: Test `tests/schema-preview.test.tsx` strictly validates that when fed a column with internal `name: "internal_col_1"`, the resulting DOM `<SchemaPreview />` outputs `display_name` but guarantees `internal_col_1` is absent from `.innerHTML`. (Test: PASS)
- [x] **`DatasetCard` Verification**: Test `tests/data-sources.test.tsx` identically affirms that expanding the dataset profile table prevents the internal string from being printed anywhere in the card's DOM. (Test: PASS)

## 4. Destructive Actions
- [x] **Delete Guardrails**: Clicking the trash icon invokes an inline confirmation flow styled with the `--danger` token. 
- [x] **State Reversion**: Canceling the deletion reverts the state without any network requests hitting the backend `DELETE` endpoint. Confirming correctly deletes the item and pops it out of the React local state list.

## Conclusion
Phase 15 is fully verified. Data ingestion and visualization pipelines are stable, safely handling edge cases while fiercely adhering to the Phase 14 privacy constraint regarding internal schema metadata.
