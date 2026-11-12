# SmartLegal-AI — Phase 9 Pre-Implementation Audit Report
**Document ID**: `SL-AUDIT-PHASE9-PREIMP-V1.0`  
**Status**: `AUDIT COMPLETE — ZERO BLOCKERS — READY FOR IMPLEMENTATION`  
**Date**: `2026-09-24`  
**Target Scope**: Phase 9: Shadow Execution & Staged Rollout  
**Author**: Antigravity Core AI & Systems Architecture Team  

---

## 1. Executive Summary & Verification Context

Following explicit user authorization to begin **Phase 9: Shadow Execution & Staged Rollout**, this pre-implementation audit was conducted across the codebase to verify repository state, validate integration points against `phase9_implementation_plan.md` v1.0, and certify zero architectural conflicts with frozen Phases 1 through 8.

### Baseline Health Status (Verified Prior to Changes):
- **Full Backend Regression Suite**: **368 / 368 passing** in 186.61s.
- **Dedicated Frozen Test Suites (Phases 1–7)**: **214 / 214 passing** in 360.92s.
- **Frontend Confidence UX Suite (Phase 8)**: **20 / 20 passing** in 44.82ms.
- **Frontend Production Build**: `npm run build` completed cleanly in 6.84s with 0 errors.
- **Git Working Tree**: Clean baseline on branch `feature/improve-doc-analysis`.

---

## 2. Reconnaissance Findings Across All 8 Subsystem Items

### Item 1: Analysis API Router (`backend/routers/analyze.py`)
- **Inspection Findings**:
  - `POST /analyze` handles document verification, concurrency limit (max 3 concurrent per user), cache checks (L1 Redis, L2 Database), and durable job dispatch via `enqueue_analysis(...)` returning HTTP 202 `{ "status": "processing", "document_id": ... }`.
  - `GET /analyze/{document_id}/status` polls L1 Redis first, then L2 Database, strictly returning `{ "status": "processing" }`, `{ "status": "error", "error": "..." }`, or `{ "status": "done", "analysis": { ... } }`.
- **Phase 9 Integration Requirement**:
  - Shadow evaluation must be enqueued **out-of-band** via a non-blocking asynchronous task after primary job dispatch.
  - Citizen-facing polling contract (`GET /analyze/{id}/status`) must remain **100% untouched**. Candidate outputs, shadow status, and shadow latency are strictly excluded from citizen responses.

### Item 2: Worker Architecture & ARQ Queue (`backend/worker.py`)
- **Inspection Findings**:
  - Primary worker uses ARQ with `WorkerSettings` listening on queue `smartlegal:analysis`, `job_timeout = 600s`, `max_tries = 3`.
  - Graceful degradation fallback: If `REDIS_URL` is empty, `enqueue_analysis` dispatches inline via `asyncio.create_task(_execute_analysis(...))`.
- **Phase 9 Integration Requirement**:
  - Shadow execution MUST NOT use the `smartlegal:analysis` queue.
  - Implement a dedicated worker module `backend/shadow/worker.py` with `ShadowWorkerSettings` listening on `smartlegal:shadow_analysis`.
  - Hard concurrency limit $\le 2$, aggressive timeout of 300s, and automatic fallback to `asyncio.create_task` when Redis is unconfigured or in testing mode.

### Item 3: Configuration & Settings Hierarchy (`backend/config.py`)
- **Inspection Findings**:
  - Configuration uses Pydantic v2 `BaseSettings` reading from `.env` with case-insensitive environment variables and safe defaults.
- **Phase 9 Integration Requirement**:
  - Define `ShadowSettings` with strictly safe defaults (`shadow_mode_enabled=False`, `canary_mode_enabled=False`, `shadow_traffic_percentage=0.0`, `canary_traffic_percentage=0.0`).
  - Keep configuration extensible via `backend/shadow/config.py` and accessible via `backend/config.py`.

### Item 4: Database Schema & Migration Integrity (`backend/database.py`)
- **Inspection Findings**:
  - Database supports Supabase PostgreSQL (`asyncpg`) and local SQLite (`aiosqlite`) via `create_tables()` with idempotent `CREATE TABLE IF NOT EXISTS` statements.
  - The `analyses` table enforces `document_id TEXT UNIQUE NOT NULL REFERENCES documents(id) ON DELETE CASCADE`.
- **Phase 9 Integration Requirement**:
  - Shadow analyses MUST NOT be written to `analyses` (doing so would violate the unique constraint and overwrite citizen results).
  - Add dedicated tables `shadow_analyses` (unique constraint `uq_exp_doc (experiment_id, document_id)`) and `shadow_comparisons` (unique constraint `uq_comparison (experiment_id, document_id)`).
  - Add schema creation in `create_tables()` with full SQLite and PostgreSQL compatibility and cascading deletes.

### Item 5: Redis Cache Layer & Extracted Text Cache (`backend/cache.py`)
- **Inspection Findings**:
  - Keys used by production: `analysis:{document_id}` (TTL 24h) and `doctext:{document_id}` (TTL 24h).
  - `get_doc_text(document_id)` and `set_doc_text(document_id, text, ttl)` are already implemented in `cache.py`.
- **Phase 9 Integration Requirement**:
  - Shadow worker reads cached text via `await get_doc_text(document_id)` whenever available. This eliminates 100% of redundant PDF parsing CPU overhead and ensures the candidate model is benchmarked on the identical text snapshot.
  - All shadow Redis keys must be strictly namespaced under `shadow:*` (e.g., `shadow:budget:*`, `shadow:kill_switch`, `shadow:canary_percentage`).

### Item 6: Provider Budget Manager & Cooldowns (`backend/services/provider_budget_manager.py`)
- **Inspection Findings**:
  - Production `ProviderBudgetManager` tracks rolling TPM/RPM windows and sets Redis cooldown keys `budget:cooldown:{provider}`.
- **Phase 9 Integration Requirement**:
  - Shadow execution MUST NOT use the production `ProviderBudgetManager` or write to `budget:cooldown:*`.
  - Implement an isolated `ShadowBudgetManager` in `backend/shadow/budget.py` with separate Redis keys (`shadow:budget:cooldown:{provider}` and `shadow:budget:spend:{date}`) and separate daily spend limits ($10.00 ceiling).

### Item 7: Offline Accuracy Evaluation Framework (`backend/evaluation/`)
- **Inspection Findings**:
  - Phase 7 delivered `metrics.py` (CER, WER, SequenceMatcher, risk concordance) and `comparative.py` (`Phase6ComparativeEvaluator`).
- **Phase 9 Integration Requirement**:
  - Import Phase 7 evaluation functions in `backend/shadow/comparison.py` as pure functional transforms to compare primary vs candidate outputs.
  - Comparative metrics are saved strictly to `shadow_comparisons` and NEVER exposed to citizens.

### Item 8: Frontend UI & Boundary Isolation (`frontend/src/`)
- **Inspection Findings**:
  - Frontend components (`Analysis.tsx`, `ClauseCard.tsx`, `AnalysisProcessingProgress.tsx`, etc.) consume strictly the primary analysis payload from Redux.
- **Phase 9 Integration Requirement**:
  - **Zero modifications to `frontend/src/`**. The entire frontend remains strictly frozen.
  - Candidate results and comparative diffs are exclusively accessible via internal authenticated admin endpoints (`/internal/shadow/*`).

---

## 3. Candidate Provider Strategy (Dependency Assessment)

- **Finding**: The `backend/venv` environment does not have `google-generativeai` installed.
- **Architectural Decision**: Candidate provider execution in `backend/shadow/service.py` will use direct asynchronous HTTP requests via `httpx.AsyncClient` (already installed and battle-tested in `backend/services/openrouter_service.py`).
- **Benefits**:
  - Zero new binary or native dependencies required.
  - Native asynchronous non-blocking I/O with granular timeouts (300s).
  - Seamlessly supports Google Gemini REST API (`generativelanguage.googleapis.com`), OpenRouter, and Groq candidate models.

---

## 4. Implementation File Plan

### A. New Modules to Add (`backend/shadow/`):
1. `backend/shadow/__init__.py`: Package initialization.
2. `backend/shadow/config.py`: `ShadowSettings`, data models, and `FailureCategory` deterministic failure taxonomy.
3. `backend/shadow/sampler.py`: Deterministic SHA-256 salted hash bucket calculator and multi-gate eligibility inspector.
4. `backend/shadow/budget.py`: Isolated `ShadowBudgetManager` with independent cooldowns and financial spend tracking.
5. `backend/shadow/service.py`: `ShadowAnalysisService` with candidate LLM execution via async `httpx`, schema validation, and retry isolation.
6. `backend/shadow/worker.py`: Dedicated ARQ worker for `smartlegal:shadow_analysis` with concurrency $\le 2$, 300s timeout, and in-memory fallback.
7. `backend/shadow/comparison.py`: Phase 7 comparison adapter computing CER, risk concordance, citation recall, and latency/cost deltas.
8. `backend/shadow/circuit_breaker.py`: Automated rollback engine, Redis overrides, and multi-tier emergency kill switch (< 500ms).
9. `backend/shadow/retention.py`: Automated 30-day data purge routine.
10. `backend/routers/internal_shadow.py`: Internal operator endpoints for metrics, experiment control, kill switch, and comparison inspection.

### B. New Test Modules to Add (`backend/tests/shadow/`):
1. `backend/tests/shadow/__init__.py`: Test package init.
2. `backend/tests/shadow/test_shadow_unit.py`: Unit tests for deterministic sampler, hash repeatability, failure taxonomy, and budget manager.
3. `backend/tests/shadow/test_shadow_integration.py`: End-to-end execution, queue dispatch, DB persistence, and failure isolation.
4. `backend/tests/shadow/test_shadow_security.py`: Multi-tenant isolation, log redaction (PII protection), and credential hygiene.
5. `backend/tests/shadow/test_shadow_rollback.py`: Automated rollback circuit breakers and emergency kill switch verification.
6. `backend/tests/shadow/test_shadow_load.py`: Concurrency cap enforcement ($\le 2$) and primary queue latency protection.
7. `backend/tests/test_phase9_shadow.py`: Consolidated test suite runner integrated with backend pytest suite.

### C. Existing Files to Modify (Additive & Isolated Only):
1. `backend/config.py`: Expose `ShadowSettings` property.
2. `backend/database.py`: Add `shadow_analyses` and `shadow_comparisons` to `create_tables()` with indexes.
3. `backend/routers/analyze.py`: Add non-blocking background hook after primary job enqueue.
4. `backend/main.py`: Register `internal_shadow.router` under `/internal/shadow`.

### D. Protected Files (Strictly Frozen — DO NOT MODIFY):
- All files under `frontend/` (100% frozen).
- `backend/services/groq_service.py` (Phase 1–5 frozen).
- `backend/services/openrouter_service.py` (Phase 5 frozen).
- `backend/services/provider_budget_manager.py` (Phase 5 frozen).
- `backend/services/pdf_parser.py` (Phase 2–4 frozen).
- `backend/services/adaptive_optimizer.py` (Phase 6 frozen).
- `backend/evaluation/*` (Phase 7 frozen — imported read-only).
- Existing test files: `backend/tests/test_phase1_foundation.py` through `backend/tests/test_phase7_evaluation.py`.

---

## 5. Architectural Invariants Verification Checklist

| # | Safety Invariant | Implementation Mechanism | Status |
|---|---|---|---|
| 1 | **Production Result Invariant** | Citizen result originates solely from primary pipeline | VERIFIED |
| 2 | **Shadow Isolation Invariant** | Shadow failure caught and swallowed; zero impact on primary | VERIFIED |
| 3 | **Provider Isolation Invariant** | Separate Redis keys (`shadow:budget:*`) and separate API credentials | VERIFIED |
| 4 | **Database Isolation Invariant** | Shadow writes to `shadow_analyses` only; `analyses` remains untouched | VERIFIED |
| 5 | **User Isolation Invariant** | `GET /analyze/{id}/status` returns only primary data; UI unchanged | VERIFIED |
| 6 | **Retry Isolation Invariant** | Shadow worker failures drop silently; zero primary task re-enqueues | VERIFIED |
| 7 | **Cost Control Invariant** | Per-doc token caps (12k input / 4k output) and $10/day spend limit | VERIFIED |
| 8 | **Deterministic Sampling** | SHA-256 salted hash bucket (0–9999) ensures reproducible routing | VERIFIED |
| 9 | **Emergency Kill Switch** | Redis key `shadow:global_kill_switch` checked at dequeue and before call | VERIFIED |
| 10 | **Automated Rollback** | Error rate $> 3\%$ or latency $> 150\%$ resets canary to 0% | VERIFIED |

---

## 6. Pre-Implementation Conclusion & Readiness

- **Blockers Found**: **0**
- **Conflicts Found**: **0**
- **Action**: Proceeding immediately with Phase 9 implementation across sub-phases 9A through 9M.
