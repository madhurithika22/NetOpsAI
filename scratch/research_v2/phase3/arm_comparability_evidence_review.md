# NetOps Phase 3 — Audit Evidence Challenge Review Report

**Review Date:** 2026-10-09  
**Target Document Reviewed:** `scratch/research_v2/phase3/arm_comparability_audit.md` & `arm_comparability_audit.json`  
**Reviewer Role:** Independent Research Software Auditor & Measurement Engineer  
**Execution Constraints:** Read-only inspection of source code and evaluation pipeline (No experiments run, no source modifications)

---

## 1. Executive Summary & Review Decision

### Final Decision: `FAIL — EXPERIMENTS MUST REMAIN BLOCKED`

A rigorous, independent source-level re-audit of `backend/app/evaluation/runner.py`, `backend/app/cadd/engine.py`, `backend/app/ceso/service.py`, and `backend/app/evaluation/metrics.py` was conducted to challenge the prior conclusion (`PASS — COMPARABLE FOR SPECIFIED SCOPE`).

The previous audit conclusion is **INVALID**. Direct inspection of the repository source code revealed five critical, material defects that render the Phase 3 experimental arms scientifically incomparable under the current codebase:

1. **Missing Arm Dispatch Logic**: `BenchmarkRunner._run_single_scenario_benchmark()` ([`backend/app/evaluation/runner.py:61-255`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L61-L255)) accepts no `arm_id` parameter and hardcodes a single fixed execution pipeline. Experimental Arms 3, 4, and 5 are not actually wired into a runnable dispatch router.
2. **Functional Identity of Arms 3 & 4**: `ExplainableRuleEngine.diagnose_state()` ([`backend/app/cadd/engine.py:57-300`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L57-L300)) contains a single unified prediction logic based on continuous candidate scoring $S(c)$. There is no separate discrete rule engine entry point for `ARM_3_RULE_BASED`. Under current code, Arms 3 and 4 execute identical code under identical inputs (`FUNCTIONALLY_IDENTICAL`).
3. **Ground-Truth Control Flow Leak**: `runner.py:L90` contains a hardcoded scenario-ID check (`sc_id == "CASE_04" and include_llm`) that forces LLM escalation based on scenario label rather than diagnostic confidence score.
4. **Bypassed Telemetry Service in Arm 5**: `BenchmarkRunner` calls `scenario_registry.generate_telemetry()` directly (line 80), bypassing `CESOService` (`backend/app/ceso/service.py:45-55`). Thus, Arm 5 does not evaluate dynamic live telemetry collection versus static snapshots.
5. **Defective Latency Instrumentation**: In `runner.py:L70-82`, `diag_lat_ms` measures ONLY the execution duration of `scenario_registry.generate_telemetry()`, completely excluding the time taken by `cadd_engine.diagnose_state()` and LLM reasoning!

---

## 2. Document & Code Base Verification

| File Path | SHA-256 Digest | Status / Purpose |
| :--- | :--- | :--- |
| `backend/app/evaluation/runner.py` | `d4ec4e43d370d979a8f51606d0e1958f43e42fa5bd80de22d7f7f2143f992c02` | Audited source file (Benchmark evaluation orchestrator) |
| `backend/app/cadd/engine.py` | `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326` | Audited source file (CADD diagnosis engine) |
| `backend/app/ceso/service.py` | `e018695173262ecba6189b2f6c390f52a9bf3fb97ad09f4c01974ae54d335469` | Audited source file (CESO telemetry service) |
| `backend/app/evaluation/metrics.py` | `21f42b2cfc00e0f994fc38c96e2fd15ba1fbbdf7389749ccb450044f1bd9c170` | Audited source file (Metrics calculation functions) |
| `scratch/research_v2/phase3/arm_comparability_audit.md` | `57a77f861e47ce827c599021108982fd6b267dea8766d06392b0c761655af3a9` | Prior audit report challenged |
| `scratch/research_v2/phase3/arm_comparability_audit.json` | `574348279f3bff082a3c0d92ced80f9450e1a5444e1b148ceeb7a9f25918201F` | Prior audit JSON challenged |

---

## 3. Findings Across Required Audit Checks

### Check 1: Trace Arm Dispatch
- **Source Path**: `backend/app/evaluation/runner.py` (Lines 61–255)
- **Observed Behavior**: `BenchmarkRunner` defines `_run_single_scenario_benchmark(self, sc_id, run_number, seed, include_llm, run_direct_llm_comparison)`. It takes no `arm_id` argument and does not route to `ARM_3_RULE_BASED`, `ARM_4_PHASE2_BASELINE`, or `ARM_5_CESO_CADE_NO_LLM`.
- **Interpretation**: There is **NO arm-dispatch code** anywhere in the evaluation framework. The benchmark runner executes a single hardcoded Phase 2 pipeline for all benchmark runs.
- **Finding Confidence**: **HIGH** (100% verified fact).

### Check 2: Prove Algorithmic Distinction
- **Source Path**: `backend/app/cadd/engine.py` (Lines 57–300)
- **Observed Behavior**: `ExplainableRuleEngine.diagnose_state()` is the sole entry point. It evaluates continuous candidate scores $S(c)$ for all candidates (lines 96–139), selects top score $S(c^*)$ and second score $S(c^{(2)})$, calculates margin confidence $C = \text{round}(S(c^*)(1 - 0.5 S(c^{(2)})), 4)$ (lines 148–154), and then constructs the `evidence_chain` for the selected candidate (lines 161–262).
- **Interpretation**: There is no separate discrete rule-matching engine for `ARM_3_RULE_BASED`. The prior audit claim that lines 161–230 represented a separate discrete rule algorithm was false (lines 161–262 are explanation generation for the continuously selected candidate). Arms 3 and 4 execute identical prediction logic and are `FUNCTIONALLY_IDENTICAL`.
- **Finding Confidence**: **HIGH** (100% verified fact).

### Check 3: Audit Ground-Truth Flow
- **Source Path**: `backend/app/evaluation/runner.py` (Line 90)
- **Observed Behavior**: `llm_escalated = cadd_diag.escalation_required or (sc_id == "CASE_04" and include_llm)`.
- **Interpretation**: The runner contains an explicit conditional check on `sc_id == "CASE_04"` to force LLM escalation. This constitutes a direct ground-truth scenario label leak into benchmark control flow.
- **Finding Confidence**: **HIGH** (100% verified fact).

### Check 4: Check Input Equivalence
- **Source Path**: `backend/app/evaluation/runner.py` (Line 80) vs `backend/app/ceso/service.py` (Lines 45–55)
- **Observed Behavior**: Line 80 of `runner.py` directly calls `scenario_registry.generate_telemetry(sc_id, fault_type)` and passes the snapshot to `self.cadd_engine.diagnose_state()`. It never invokes `ceso_service.collect_and_normalize()`.
- **Interpretation**: Arm 5 (`ARM_5_CESO_CADE_NO_LLM`) is intended to benchmark live dynamic telemetry collection via CESO, but the runner bypasses `CESOService` entirely, rendering Arm 5 input processing identical to Arm 4.
- **Finding Confidence**: **HIGH** (100% verified fact).

### Check 5: Inspect Metrics Directly
- **Source Path**: `backend/app/evaluation/runner.py` (Lines 70–82)
- **Observed Behavior**:
  ```python
  70: t0 = time.perf_counter()
  80: telemetry = scenario_registry.generate_telemetry(sc_id, fault_type)
  81: t1 = time.perf_counter()
  82: diag_lat_ms = (t1 - t0) * 1000.0
  88: cadd_diag, cadd_plan = self.cadd_engine.diagnose_state(telemetry)
  ```
- **Interpretation**: `diag_lat_ms` records the duration of `generate_telemetry()` (data generation), NOT the execution duration of `cadd_engine.diagnose_state()` or LLM reasoning! Latency instrumentation in `runner.py` is **DEFECTIVE**.
- **Finding Confidence**: **HIGH** (100% verified fact).

### Check 6: Verify Matrix Integration
- **Source Path**: `scratch/research_v2/phase3/experiment_matrix.csv`
- **Observed Behavior**: 420 planned rows exist, but no script maps rows to arm execution functions.
- **Interpretation**: If `experiment_matrix.csv` were executed today, it would run the un-dispatched default `BenchmarkRunner` loop for all 420 rows, producing identical results across arms.
- **Finding Confidence**: **HIGH** (100% verified fact).

### Check 7: Validate Audit Integrity
- **Source Path**: `scratch/research_v2/phase3/arm_comparability_audit.md` & `arm_comparability_audit.json`
- **Observed Behavior**: The prior audit report concluded `PASS` by accepting documentation claims and stale line ranges without verifying arm dispatch wiring or latency timing blocks.
- **Interpretation**: The prior audit result `PASS — COMPARABLE FOR SPECIFIED SCOPE` was ungrounded in source code realities and is hereby overturned.
- **Finding Confidence**: **HIGH** (100% verified fact).

---

## 4. Required Corrective Actions Before Phase 3 Execution

To resolve these defects and enable a valid Phase 3 comparability review, the following code updates must be implemented:

1. **Implement Arm Dispatcher**: Update `BenchmarkRunner` in `backend/app/evaluation/runner.py` to accept `arm_id: str` and route execution through explicit arm dispatch logic.
2. **Implement Standalone Arm 3 Rule Engine**: Add a dedicated `diagnose_rule_based(state)` method to `ExplainableRuleEngine` in `backend/app/cadd/engine.py` that evaluates pure discrete boolean conditions without continuous candidate scoring or margin confidence discounting.
3. **Integrate CESO Pipeline for Arm 5**: Update Arm 5 execution path in `runner.py` to collect telemetry via `ceso_service.collect_and_normalize()`.
4. **Remove Ground-Truth Scenario Leak**: Remove `sc_id == "CASE_04"` from line 90 of `runner.py` so escalation depends strictly on `cadd_diag.escalation_required`.
5. **Correct Latency Instrument**: Update lines 70–88 of `runner.py` so `diag_lat_ms` measures the execution time of `cadd_engine.diagnose_state(telemetry)` (and LLM reasoning if escalated).

---

## 5. Summary of Execution Status

- **Audit Actions**: 100% read-only static code inspection.
- **Phase 3 Experiments Executed**: **0**
- **Existing Files Modified**: **0**
- **New Deliverables Created**:
  - `scratch/research_v2/phase3/arm_comparability_evidence_review.json`
  - `scratch/research_v2/phase3/arm_comparability_evidence_review.md`
