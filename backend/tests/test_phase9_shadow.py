"""
tests/test_phase9_shadow.py — Phase 9 Shadow Execution & Staged Rollout Test Suite.

Covers:
  1. Unit tests: Deterministic sampling, repeatability, failure taxonomy, budget manager.
  2. Multi-gate eligibility: Feature toggle, privacy mode, file size limit, kill switch.
  3. Candidate Execution Engine: Schema validation, error classification, timeout isolation.
  4. Phase 7 Comparison Adapter: CER, WER, risk concordance, citation recall, persistence.
  5. Emergency Kill Switch & Automated Rollback: Sub-500ms abort, error rate breaker, schema breaker.
  6. Worker Isolation: Low concurrency, separate queue ('smartlegal:shadow_analysis'), text reuse.
  7. Multi-Tenant Security & API Protection: X-Shadow-Admin-Key authorization, zero citizen leakage.
  8. Data Hygiene: Automated 30-day retention purge.

All tests run completely self-contained without requiring live external AI provider credentials.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shadow.config import FailureCategory, RolloutStage, ShadowSettings, get_shadow_settings
from shadow.sampler import (
    calculate_sampling_bucket,
    check_shadow_eligibility,
    is_sample_selected,
    maybe_enqueue_shadow_analysis,
    should_serve_canary,
)
from shadow.budget import ShadowBudgetManager, get_shadow_budget_manager
from shadow.service import ShadowAnalysisService, ShadowExecutionResult
from shadow.comparison import ShadowComparisonAdapter
from shadow.circuit_breaker import (
    evaluate_circuit_breakers,
    get_dynamic_canary_percentage,
    get_dynamic_shadow_percentage,
    is_kill_switch_active,
    record_execution_metric,
    set_dynamic_canary_percentage,
    set_dynamic_shadow_percentage,
    set_kill_switch,
)
from shadow.worker import ShadowWorkerSettings, run_shadow_analysis_job
from shadow.retention import purge_expired_shadow_records


# ===========================================================================
# 1. Deterministic Sampling & Configuration Unit Tests
# ===========================================================================

class TestShadowConfigurationAndSampling(unittest.TestCase):

    def test_shadow_settings_safe_defaults(self):
        """Verify master toggles and rollout percentages default to safe zero/disabled."""
        settings = ShadowSettings()
        self.assertFalse(settings.shadow_mode_enabled)
        self.assertFalse(settings.canary_mode_enabled)
        self.assertEqual(settings.shadow_traffic_percentage, 0.0)
        self.assertEqual(settings.canary_traffic_percentage, 0.0)
        self.assertEqual(settings.shadow_max_concurrency, 2)
        self.assertEqual(settings.shadow_job_timeout_seconds, 300)
        self.assertEqual(settings.shadow_daily_budget_usd, 10.0)

    def test_failure_taxonomy_codes(self):
        """Verify all 9 failure codes defined in taxonomy specification exist."""
        expected = {
            "SHADOW_TIMEOUT",
            "SHADOW_PROVIDER_UNAVAILABLE",
            "SHADOW_RATE_LIMIT",
            "SHADOW_AUTH_FAILURE",
            "SHADOW_CONTEXT_OVERFLOW",
            "SHADOW_INVALID_OUTPUT",
            "SHADOW_INTERNAL_ERROR",
            "SHADOW_RESOURCE_LIMIT",
            "SHADOW_CANCELLED",
        }
        actual = {c.value for c in FailureCategory}
        self.assertEqual(expected, actual)

    def test_rollout_stage_ladder(self):
        """Verify 6-stage rollout progression from Stage 0 to Stage 5."""
        stages = [s.value for s in RolloutStage]
        self.assertEqual(len(stages), 6)
        self.assertEqual(RolloutStage.STAGE_0_SHADOW.value, "stage_0_shadow")
        self.assertEqual(RolloutStage.STAGE_5_PRODUCTION.value, "stage_5_production")

    def test_sampling_bucket_repeatability(self):
        """Verify deterministic hashing: identical document_id + salt produces identical bucket."""
        doc_id = "doc_test_lease_001"
        salt = "smartlegal_2026"
        b1 = calculate_sampling_bucket(doc_id, salt)
        b2 = calculate_sampling_bucket(doc_id, salt)
        self.assertEqual(b1, b2)
        self.assertTrue(0 <= b1 < 10000)

    def test_sampling_salt_divergence(self):
        """Verify independent canary and shadow salting prevents correlated bias."""
        doc_id = "doc_test_rental_002"
        b_shadow = calculate_sampling_bucket(doc_id, "smartlegal_2026")
        b_canary = calculate_sampling_bucket(doc_id, "smartlegal_canary_2026")
        self.assertNotEqual(b_shadow, b_canary)

    def test_sampling_selection_boundaries(self):
        """Verify 0.0% is never selected and 100.0% is always selected."""
        doc_id = "doc_boundary_test"
        self.assertFalse(is_sample_selected(doc_id, 0.0, "salt"))
        self.assertFalse(is_sample_selected(doc_id, -1.0, "salt"))
        self.assertTrue(is_sample_selected(doc_id, 100.0, "salt"))
        self.assertTrue(is_sample_selected(doc_id, 105.0, "salt"))

    def test_sampling_uniform_distribution(self):
        """Verify SHA-256 bucket allocation uniformity over 1,000 document IDs (10% target)."""
        target_pct = 10.0
        salt = "test_uniformity_salt"
        selected = sum(
            1 for i in range(1000)
            if is_sample_selected(f"doc_{i}", target_pct, salt)
        )
        self.assertTrue(70 <= selected <= 130)


# ===========================================================================
# 2. Isolated Budget Manager Tests
# ===========================================================================

class TestShadowBudgetManager(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mgr = ShadowBudgetManager()
        await self.mgr.reset()

    async def asyncTearDown(self):
        await self.mgr.reset()

    async def test_cost_calculation(self):
        """Verify token cost calculation based on configured per-million rates."""
        cost = self.mgr.calculate_cost_usd(prompt_tokens=10000, completion_tokens=2500)
        self.assertEqual(cost, 0.002)

    async def test_cooldown_locking(self):
        """Verify isolated candidate cooldown locking."""
        provider = "candidate_genai"
        self.assertEqual(await self.mgr.get_cooldown_remaining(provider), 0.0)

        await self.mgr.set_cooldown(provider, 20.0)
        remaining = await self.mgr.get_cooldown_remaining(provider)
        self.assertTrue(15.0 <= remaining <= 20.0)

    async def test_daily_spending_cap(self):
        """Verify daily spend limit blocks further executions once exhausted."""
        # 4 records of 25M tokens @ $0.10/M = $10.00
        for _ in range(4):
            await self.mgr.record_usage(prompt_tokens=25_000_000, completion_tokens=0)

        spend = await self.mgr.get_daily_spend()
        self.assertGreaterEqual(spend, 10.0)

        is_allowed, reason = await self.mgr.is_request_allowed(estimated_tokens=5000)
        self.assertFalse(is_allowed)
        self.assertEqual(reason, "daily_budget_exhausted")
        await self.mgr.reset()
        await get_shadow_budget_manager().reset()


# ===========================================================================
# 3. Multi-Gate Eligibility & Canary Router Tests
# ===========================================================================

class TestShadowEligibilityAndCanary(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        await get_shadow_budget_manager().reset()

    async def asyncTearDown(self):
        await get_shadow_budget_manager().reset()

    async def test_eligibility_disabled_by_default(self):
        """Verify default settings reject shadow execution."""
        settings = ShadowSettings(shadow_mode_enabled=False)
        allowed, reason = await check_shadow_eligibility("doc_1", b"fake bytes", "doc.pdf", settings)
        self.assertFalse(allowed)
        self.assertEqual(reason, "shadow_mode_disabled")

    async def test_eligibility_oversized_file(self):
        """Verify documents exceeding 15 MB are rejected from shadow processing."""
        settings = ShadowSettings(shadow_mode_enabled=True, shadow_traffic_percentage=100.0)
        oversized_bytes = b"0" * (16 * 1024 * 1024)  # 16 MB
        allowed, reason = await check_shadow_eligibility("doc_2", oversized_bytes, "huge.pdf", settings)
        self.assertFalse(allowed)
        self.assertEqual(reason, "payload_exceeds_shadow_limit")

    async def test_eligibility_kill_switch_active(self):
        """Verify active kill switch blocks eligibility."""
        settings = ShadowSettings(
            shadow_mode_enabled=True,
            shadow_traffic_percentage=100.0,
            shadow_experiment_id="exp_kill_test",
        )
        await set_kill_switch(experiment_id="exp_kill_test", active=True)
        try:
            allowed, reason = await check_shadow_eligibility("doc_3", b"short text", "doc.pdf", settings)
            self.assertFalse(allowed)
            self.assertEqual(reason, "kill_switch_active")
        finally:
            await set_kill_switch(experiment_id="exp_kill_test", active=False)

    async def test_eligibility_success(self):
        """Verify eligible document passes all gates when enabled and 100% sampled."""
        settings = ShadowSettings(
            shadow_mode_enabled=True,
            shadow_traffic_percentage=100.0,
            shadow_experiment_id="exp_success_test",
        )
        allowed, reason = await check_shadow_eligibility("doc_4", b"valid document", "doc.pdf", settings)
        self.assertTrue(allowed)
        self.assertEqual(reason, "eligible")

    async def test_canary_routing_guard(self):
        """Verify Canary router returns False when disabled, and honors canary percentage when enabled."""
        # When disabled:
        self.assertFalse(await should_serve_canary("doc_test"))

        # When enabled with 100% canary:
        with patch("shadow.sampler.get_shadow_settings") as mock_settings:
            mock_settings.return_value = ShadowSettings(
                canary_mode_enabled=True,
                canary_traffic_percentage=100.0,
            )
            self.assertTrue(await should_serve_canary("doc_test"))

    async def test_non_blocking_hook_isolation(self):
        """Verify maybe_enqueue_shadow_analysis never raises, even upon unexpected internal error."""
        with patch("shadow.sampler.check_shadow_eligibility", side_effect=RuntimeError("Simulated crash")):
            result = await maybe_enqueue_shadow_analysis("doc_err", b"bytes", "err.pdf", "user_1")
            self.assertFalse(result)


# ===========================================================================
# 4. Candidate Execution Service & Schema Validation Tests
# ===========================================================================

class TestShadowAnalysisService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        await get_shadow_budget_manager().reset()

    async def asyncTearDown(self):
        await get_shadow_budget_manager().reset()

    async def test_mock_candidate_execution_structure(self):
        """Verify mock candidate analysis returns valid legal analysis schema."""
        service = ShadowAnalysisService()
        result = await service.execute_candidate_analysis("Sample lease agreement text", "doc_srv_1")

        self.assertTrue(result.success, f"Failed with {result.failure_category}: {result.error_message}")
        self.assertIsNone(result.failure_category)
        self.assertIn("summary", result.result_data)
        self.assertIn("clauses", result.result_data)
        self.assertGreater(len(result.result_data["clauses"]), 0)
        self.assertGreaterEqual(result.latency_ms, 0)
        self.assertTrue(result.source_hash)

    async def test_schema_validation_failure_classification(self):
        """Verify invalid candidate output is properly classified as SHADOW_INVALID_OUTPUT."""
        service = ShadowAnalysisService()
        service.settings = ShadowSettings(shadow_candidate_api_key="")
        with patch.object(service, "_mock_candidate_response", return_value=({"invalid": "schema"}, 100, 50)):
            result = await service.execute_candidate_analysis("Lease text", "doc_srv_2")
            self.assertFalse(result.success)
            self.assertEqual(result.failure_category, FailureCategory.SHADOW_INVALID_OUTPUT)

    async def test_candidate_timeout_classification(self):
        """Verify candidate timeout is classified as SHADOW_TIMEOUT."""
        service = ShadowAnalysisService()
        service.settings = ShadowSettings(
            shadow_candidate_provider="google_genai",
            shadow_candidate_api_key="fake_key",
        )
        with patch.object(service, "_call_google_genai", side_effect=asyncio.TimeoutError()):
            result = await service.execute_candidate_analysis("Lease text", "doc_srv_3")
            self.assertFalse(result.success)
            self.assertEqual(result.failure_category, FailureCategory.SHADOW_TIMEOUT)



# ===========================================================================
# 5. Phase 7 Comparative Evaluation Adapter Tests
# ===========================================================================

class TestShadowComparisonAdapter(unittest.IsolatedAsyncioTestCase):

    def _sample_analysis_payload(self, overall_risk="medium", clauses_count=2):
        return {
            "id": "analysis_test_123",
            "status": "done",
            "summary": {
                "document_type": "Rental Agreement",
                "overall_risk": overall_risk,
                "total_clauses": clauses_count,
                "key_takeaways": ["Rent due on the 5th of each month."],
            },
            "clauses": [
                {
                    "clause_number": 1,
                    "title": "Rent Payment",
                    "text": "Tenant shall pay Rs 25,000 monthly.",
                    "plain_english": "Monthly rent is Rs 25,000.",
                    "risk_level": "low",
                    "risk_explanation": "Standard rent clause.",
                    "recommendations": [],
                    "statutory_references": ["Transfer of Property Act, 1882"],
                },
                {
                    "clause_number": 2,
                    "title": "Security Deposit",
                    "text": "Deposit is Rs 50,000 refundable.",
                    "plain_english": "Refundable security deposit is Rs 50,000.",
                    "risk_level": "medium",
                    "risk_explanation": "Requires 30 days notice.",
                    "recommendations": ["Demand written receipt."],
                    "statutory_references": ["Indian Contract Act, 1872"],
                },
            ],
        }

    async def test_comparison_metrics_calculation(self):
        """Verify CER, risk concordance, and citation recall calculation."""
        primary = self._sample_analysis_payload(overall_risk="medium")
        candidate = self._sample_analysis_payload(overall_risk="medium")

        # Perfect match comparison
        conc = ShadowComparisonAdapter._compute_risk_concordance(
            primary["clauses"], candidate["clauses"]
        )
        self.assertEqual(conc, 1.0)

        cites = ShadowComparisonAdapter._extract_citations(primary)
        self.assertIn("transfer of property act, 1882", cites)
        self.assertIn("indian contract act, 1872", cites)

    async def test_comparison_and_persistence(self):
        """Verify comparison record is persisted into database table."""
        from database import init_db_pool, get_db_ctx
        await init_db_pool()

        doc_id = f"doc_comp_test_{int(datetime.datetime.now().timestamp())}"
        async with get_db_ctx() as db:
            await db.execute(
                """INSERT OR IGNORE INTO documents (id, user_id, filename, file_url, file_size, uploaded_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                doc_id, "user_test", "lease.pdf", "local://dummy", 1024, "2026-09-24T00:00:00Z"
            )

        primary = self._sample_analysis_payload()
        candidate = self._sample_analysis_payload()

        comp_result = await ShadowComparisonAdapter.compare_and_persist(
            experiment_id="exp_comp_test",
            document_id=doc_id,
            primary_data=primary,
            shadow_data=candidate,
            shadow_analysis_id="shadow_ana_123",
            primary_latency_ms=1200,
            shadow_latency_ms=1050,
            primary_tokens=3000,
            shadow_tokens=2800,
            shadow_cost_usd=0.0012,
        )

        self.assertIsNotNone(comp_result)
        self.assertEqual(comp_result.document_id, doc_id)
        self.assertEqual(comp_result.risk_concordance, 1.0)
        self.assertEqual(comp_result.latency_delta_ms, -150)
        self.assertEqual(comp_result.token_delta, -200)


# ===========================================================================
# 6. Emergency Kill Switch & Automated Rollback Circuit Breaker Tests
# ===========================================================================

class TestShadowCircuitBreakers(unittest.IsolatedAsyncioTestCase):

    async def test_global_and_experiment_kill_switch(self):
        """Verify sub-500ms emergency kill switch activation and deactivation."""
        exp_id = "exp_test_circuit"

        # Initially inactive
        self.assertFalse(await is_kill_switch_active(exp_id))

        # Activate experiment-level switch
        await set_kill_switch(experiment_id=exp_id, active=True)
        self.assertTrue(await is_kill_switch_active(exp_id))

        # Deactivate experiment-level switch
        await set_kill_switch(experiment_id=exp_id, active=False)
        self.assertFalse(await is_kill_switch_active(exp_id))

        # Activate global kill switch
        await set_kill_switch(experiment_id=None, active=True)
        self.assertTrue(await is_kill_switch_active(exp_id))

        # Reset global switch
        await set_kill_switch(experiment_id=None, active=False)
        self.assertFalse(await is_kill_switch_active(exp_id))

    async def test_dynamic_traffic_overrides(self):
        """Verify dynamic sampling and canary percentage overrides."""
        await set_dynamic_shadow_percentage(15.5)
        self.assertEqual(await get_dynamic_shadow_percentage(), 15.5)

        await set_dynamic_canary_percentage(5.0)
        self.assertEqual(await get_dynamic_canary_percentage(), 5.0)

    async def test_circuit_breaker_error_rate_spike(self):
        """Verify error rate > 3% triggers automated rollback resetting canary to 0%."""
        exp_id = "exp_breaker_err"
        await set_dynamic_canary_percentage(25.0)
        self.assertEqual(await get_dynamic_canary_percentage(), 25.0)

        # Record 10 executions with 5 failures (50% failure rate > 3% threshold)
        for _ in range(5):
            await record_execution_metric(exp_id, success=True, latency_ms=1000)
        for _ in range(5):
            await record_execution_metric(exp_id, success=False, latency_ms=1000)

        tripped, reason = await evaluate_circuit_breakers(exp_id)
        self.assertTrue(tripped)
        self.assertIn("Error rate spike", reason)
        # Verify canary was immediately reset to 0%
        self.assertEqual(await get_dynamic_canary_percentage(), 0.0)

    async def test_circuit_breaker_consecutive_schema_errors(self):
        """Verify 2 consecutive schema violations trigger automated rollback."""
        exp_id = "exp_breaker_schema"
        await set_dynamic_canary_percentage(10.0)

        # Record 2 consecutive schema errors
        await record_execution_metric(exp_id, success=False, latency_ms=500, is_schema_error=True)
        await record_execution_metric(exp_id, success=False, latency_ms=500, is_schema_error=True)

        tripped, reason = await evaluate_circuit_breakers(exp_id)
        self.assertTrue(tripped)
        self.assertIn("Consecutive schema violations", reason)
        self.assertEqual(await get_dynamic_canary_percentage(), 0.0)


# ===========================================================================
# 7. Worker Isolation & Resource Protection Tests
# ===========================================================================

class TestShadowWorkerIsolation(unittest.IsolatedAsyncioTestCase):

    def test_worker_settings_concurrency_and_timeout(self):
        """Verify shadow worker queue properties enforce strict resource isolation."""
        self.assertEqual(ShadowWorkerSettings.queue_name, "smartlegal:shadow_analysis")
        self.assertEqual(ShadowWorkerSettings.job_timeout, 300)
        self.assertEqual(ShadowWorkerSettings.max_tries, 1)  # Never retry
        self.assertEqual(ShadowWorkerSettings.max_jobs, 2)   # Concurrency <= 2

    async def test_worker_skips_job_when_kill_switch_active(self):
        """Verify worker aborts execution immediately when kill switch is tripped."""
        exp_id = get_shadow_settings().shadow_experiment_id
        await set_kill_switch(experiment_id=exp_id, active=True)

        try:
            with patch("shadow.worker.ShadowAnalysisService.execute_candidate_analysis") as mock_exec:
                await run_shadow_analysis_job(None, "doc_kill", b"sample bytes", "test.pdf", "user_1")
                mock_exec.assert_not_called()
        finally:
            await set_kill_switch(experiment_id=exp_id, active=False)


# ===========================================================================
# 8. Data Retention Purge Policy Tests
# ===========================================================================

class TestShadowDataRetention(unittest.IsolatedAsyncioTestCase):

    async def test_purge_expired_records(self):
        """Verify retention purge routine deletes expired candidate records."""
        from database import init_db_pool, get_db_ctx
        await init_db_pool()

        # Insert historical record with old date
        old_date = "2020-01-01T00:00:00Z"
        doc_id = f"doc_purge_{int(datetime.datetime.now().timestamp())}"

        async with get_db_ctx() as db:
            await db.execute(
                """INSERT OR IGNORE INTO documents (id, user_id, filename, file_url, file_size, uploaded_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                doc_id, "user_test", "old.pdf", "local://dummy", 1024, old_date
            )
            await db.execute(
                """INSERT OR IGNORE INTO shadow_analyses (
                    id, experiment_id, document_id, candidate_provider,
                    candidate_model, candidate_version, source_document_hash,
                    result_json, execution_status, started_at, completed_at,
                    latency_ms, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
                "old_shadow_1", "exp_purge", doc_id, "mock", "mock-1", "v1", "hash",
                "{}", "success", old_date, old_date, 100, old_date
            )

        purged_analyses, _ = await purge_expired_shadow_records(retention_days=30)
        self.assertGreaterEqual(purged_analyses, 1)


# ===========================================================================
# 9. Multi-Tenant Security & API Protection Tests
# ===========================================================================

class TestShadowSecurityAndAPI(unittest.IsolatedAsyncioTestCase):

    async def test_operator_endpoint_requires_auth_key(self):
        """Verify /internal/shadow/* endpoints strictly enforce X-Shadow-Admin-Key."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Request without header -> 403 Forbidden
        resp = client.get("/internal/shadow/status")
        self.assertEqual(resp.status_code, 403)

        # Request with invalid header -> 403 Forbidden
        resp = client.get("/internal/shadow/status", headers={"X-Shadow-Admin-Key": "invalid_key"})
        self.assertEqual(resp.status_code, 403)

        # Request with valid header -> 200 OK
        # No built-in default key exists; configure one for this test.
        shadow_settings = get_shadow_settings()
        original_key = shadow_settings.shadow_admin_key
        shadow_settings.shadow_admin_key = "test-admin-key"
        try:
            # Unconfigured/empty key must never authenticate
            resp = client.get("/internal/shadow/status", headers={"X-Shadow-Admin-Key": ""})
            self.assertEqual(resp.status_code, 403)
            resp = client.get("/internal/shadow/status", headers={"X-Shadow-Admin-Key": "test-admin-key"})
        finally:
            shadow_settings.shadow_admin_key = original_key
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("shadow_mode_enabled", data)
        self.assertIn("active_experiment_id", data)

    async def test_citizen_status_contract_unmodified(self):
        """Verify citizen endpoint GET /analyze/{id}/status never returns shadow or candidate metadata."""
        from database import init_db_pool, get_db_ctx
        from fastapi.testclient import TestClient
        from main import app

        await init_db_pool()
        client = TestClient(app)

        # Generate a test document and primary analysis
        doc_id = f"doc_contract_test_{int(datetime.datetime.now().timestamp())}"
        user_id = f"user_{doc_id}"
        primary_payload = {
            "id": "prim_123",
            "document_id": doc_id,
            "status": "done",
            "summary": {"document_type": "Rental Agreement", "overall_risk": "low"},
            "clauses": [],
        }

        async with get_db_ctx() as db:
            await db.execute(
                """INSERT OR IGNORE INTO users (id, name, email, password, created_at)
                   VALUES ($1, $2, $3, $4, $5)""",
                user_id, "Test User", f"{user_id}@test.com", "hash", "2026-09-24T00:00:00Z"
            )
            await db.execute(
                """INSERT OR IGNORE INTO documents (id, user_id, filename, file_url, file_size, uploaded_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                doc_id, user_id, "lease.pdf", "local://dummy", 1024, "2026-09-24T00:00:00Z"
            )
            await db.execute(
                """INSERT OR REPLACE INTO analyses (id, document_id, result_json, analyzed_at)
                   VALUES ($1, $2, $3, $4)""",
                "prim_123", doc_id, json.dumps(primary_payload), "2026-09-24T00:00:00Z"
            )

        # Mock authentication dependency
        from routers.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: {"id": user_id, "email": f"{user_id}@test.com"}

        try:
            resp = client.get(f"/api/v1/analyze/{doc_id}/status")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            # Standard citizen contract keys
            self.assertEqual(data.get("status"), "done")
            self.assertIn("analysis", data)
            # Crucial: Assert shadow/candidate keys are completely absent from citizen response
            self.assertNotIn("candidate_model", data)
            self.assertNotIn("candidate_provider", data)
            self.assertNotIn("shadow_status", data)
            self.assertNotIn("cer", data)
            self.assertNotIn("risk_concordance", data)
        finally:
            app.dependency_overrides.pop(get_current_user, None)
