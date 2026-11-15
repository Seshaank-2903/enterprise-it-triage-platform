## Enterprise Architectural Review Checklist

### 1. Database & Schema Migrations
- [ ] Alembic migration scripts are provided and tested with both SQLite (batch mode) and PostgreSQL.
- [ ] Schema additions to `tickets` or `ticket_history` include explicit indices on search keys.
- [ ] No migrations perform destructive operations without fallback rollbacks.

### 2. AI Safety, Determinism, & Guardrails
- [ ] Mistral structured JSON generation is strictly governed by a Pydantic schema.
- [ ] Verified that high-priority tickets or sensitive categories (`Access`) cannot be auto-resolved.
- [ ] Vector search (ChromaDB) attaches canonical URL/title citations to the response payload.
- [ ] Fallbacks are tested: Timeout/Malformatted JSON flags `ai_review_status = Failed` without crashing.

### 3. Observability & Telemetry
- [ ] Requests propagate the `X-Request-ID` header.
- [ ] JSON logging formats latency dimensions independently:
  - `api_latency`
  - `db_latency`
  - `rag_latency`
  - `llm_latency`

### 4. Performance & Frontend Bundle Safety
- [ ] Recharts and resource-intensive analytical views are imported using `React.lazy` wrapped in `<Suspense>`.
- [ ] CSV streams utilize chunked, buffered generators to prevent high RAM consumption.

### 5. Testing & CI Pipeline
- [ ] All external AI/Vector calls are isolated using `unittest.mock` (no live API keys in CI).
- [ ] Code passes `flake8`, `eslint`, `pytest`, and `vitest`.
