# NetOps Phase 3 — Focused Experimental-Readiness Audit Report

**Audit Date**: October 9, 2026  
**Auditor**: Independent IEEE Research-Methodology & Software Auditor  
**Audit Scope**: Arms 3 (`ARM_3_RULE_BASED`), 4 (`ARM_4_PHASE2_BASELINE`), and 5 (`ARM_5_CESO_CADE_NO_LLM`)  
**Overall Verdict**: **`NOT READY — CORRECTIONS REQUIRED`**

---

## 1. Executive Verdict

A strict, independent research-software audit was conducted for Phase 3 experimental readiness covering Arms 3, 4, and 5.

The overall verdict is **`NOT READY — CORRECTIONS REQUIRED`**.

While the CADE diagnostic engine v2.0.0-phase2 preserves method-level candidate scoring formulas, tie-breaking rules, and confidence calculations from Phase 2, critical defects block Phase 3 research execution authorization:
1. **Critical Comparability Flaw (Blocker 01)**: The telemetry dispatch path for Arm 5 in `runner.py` calls `ceso_service.load_scenario(sc_id)`, which resets `active_fault` to `"NONE"`. This silently clears the injected fault, delivering un-faulted healthy telemetry to Arm 5 while Arms 3 and 4 receive faulted telemetry.
2. **Metric Implementation Defect (Blocker 02)**: Verification Scope Reduction (VSR) is hardcoded to 66.7% (`metrics.py:150`) and Remediation Success Rate (RSR) defaults to 100.0% (`metrics.py:159`) when zero remediations are executed.
3. **Latency Instrumentation Defect (Blocker 03)**: Total latency `total_elapsed_ms` (`runner.py:185`) is calculated by summing subcomponents rather than measuring true end-to-end wall-clock duration.
4. **Baseline Freeze Hash Discrepancy (Blocker 04)**: `backend/app/cadd/engine.py` SHA256 hash on disk does not match `freeze_manifest.json` due to the Phase 3 addition of `diagnose_rule_based`.

**Safety Attestation**: Zero research experiments were executed, zero network states or namespaces were altered, zero fault injections occurred, and zero rows of the 420-row research matrix were marked completed.

---

## 2. Audited File Hashes and Revision Scope

| File Path | Audited SHA256 Hash | Manifest SHA256 Match | Status |
|---|---|---|---|
| `backend/app/cadd/engine.py` | `07e1bfe7bf26c82447dfe5959f75adcffc963857fba44574278bff3209c23504` | `FAIL` (Recorded: `ea4834...`) | Method-level EQUIVALENT, File SHA DISCREPANT |
| `backend/app/cadd/service.py` | `001eb662130faf773a328b5bf88811613bddbe85cb1dfeee21f22fe9e124c085` | `PASS` | Verified |
| `backend/app/ceso/service.py` | `e018695173262ecba6189b2f6c390f52a9bf3fb97ad09f4c01974ae54d335469` | N/A (Phase 3) | Audited |
| `backend/app/evaluation/runner.py` | `022255ce480fb8fdc7f4da98b971bfa0cde96ff953657f77a9c1afc6c84e0f69` | N/A (Phase 3) | Audited |
| `backend/app/evaluation/metrics.py` | `21f42b2cfc00e0f994fc38c96e2fd15ba1fbbdf7389749ccb450044f1bd9c170` | N/A (Phase 3) | Audited |
| `backend/app/evaluation/models.py` | `b624641f61a4d3cd3b02af92453dba1c4378c205a52f414610ec1ab6e3b524a3` | N/A (Phase 3) | Audited |
| `backend/app/evaluation/recorder.py` | `d91c9dc61c09016d4df6fc24b46f20f62639467c98c995ec249ffc9fe23f3ab5` | N/A (Phase 3) | Audited |
| `backend/app/research_v2/guard.py` | `1a550fa4b75a2f0c28f5223be23fd3fec6e215078535f5343a658e7f90340335` | `PASS` | Verified |
| `scratch/research_v2/phase2/freeze_manifest.json` | `97abaf470754fae34f5362cac8e3c64203a169649a1665ef535d04cabedf95fd` | `PASS` | Verified |
| `scratch/research_v2/phase3/experiment_matrix.csv` | `949817a7efb02d36d213ad6a67b6e90948de72172154b512573ff8d3cae766a9` | N/A (Phase 3) | Audited (420 planned rows) |

---

## 3. Detailed Audit Findings

### Audit A — Frozen Phase 2 Baseline Integrity
- **Candidate Score Formulas & Activation**: `backend/app/cadd/engine.py:258-295` preserves the candidate scoring logic $S(c)$, non-linear clipping $\psi(x) = \max(0, \min(1, x))$, and thresholds ($50.0\text{ ms}$ RTT, $10.0\%$ loss).
- **Candidate Ordering & Tie-Breaking**: `engine.py:39-49` and `engine.py:297-301` preserve the 9-element deterministic tie-breaking array (`INTERFACE_FAILURE` down to `HEALTHY`).
- **Confidence Calculation**: `engine.py:310-315` preserves $C = \text{round}(S(\text{best}) \cdot (1.0 - 0.5 \cdot S(\text{second})), 4)$.
- **Escalation Thresholds**: `engine.py:36` and `engine.py:316` maintain the $0.70$ confidence escalation cutoff.
- **Diagnosis Labels & Action Plans**: Preserved across all 8 fault classes.
- **Freeze Manifest Hash Discrepancy**: `engine.py` SHA256 on disk is `07e1bfe7...` vs manifest `ea483491...`. The file modification was caused by adding method `diagnose_rule_based` for Arm 3. Arm 4's method `diagnose_state` remains behaviorally identical. Original frozen run records `exp-phase2-5c538333.json` and `exp-phase2-04052fa5.json` in `scratch/research_v2/phase2/runs/` match manifest hashes 100%.

### Audit B — Matched-Input Comparability for Arms 3–5
- **Call-Path Analysis**:
  - Arm 3 & 4: Entry point `_run_single_scenario_benchmark` (`runner.py:96`) -> calls `scenario_registry.generate_telemetry(sc_id, fault_type)`.
  - Arm 5: Entry point `_run_single_scenario_benchmark` (`runner.py:94`) -> calls `ceso_service.load_scenario(sc_id)`.
- **CRITICAL DEFECT (Fault Erasure)**: Inside `ceso_service.load_scenario(scenario_id)` (`service.py:38`), `scenario_registry.load_scenario(scenario_id)` is invoked, which explicitly resets `self.active_fault = "NONE"` (`registry.py:46`). When `collect_and_normalize()` runs, `generate_telemetry` receives no explicit `fault_type` and defaults to `self.active_fault` (`"NONE"`). Thus, Arm 5 is provided with healthy telemetry while Arms 3 and 4 receive faulted telemetry.
- **Ground-Truth Label Isolation**: Verified. `NetworkState` features do not leak scenario IDs or ground truth labels. Label leakage checks (`CASE_04` forced escalation) were previously removed.

### Audit C — Metric Validity
- **Accuracy, Precision, Recall, F1, Macro-F1**: Correctly implemented in `metrics.py:46-100`. Computable for Arms 3–5.
- **Confidence Characterization**: Confidence values generated by CADE are heuristic margin scores, not calibrated Bayesian probabilities.
- **Latency Measurement Defect**: `total_elapsed_ms` in `runner.py:185` is computed as `telemetry_collection_latency_ms + diagnosis_latency_ms + llm_latency_ms`. This sums subcomponents instead of measuring true wall-clock duration from benchmark entry to exit, omitting serialization, MSVS validation, and logging overhead.
- **Remediation & Safety Metric Flaws**:
  - `metrics["vsr"]` (`metrics.py:150`) is hardcoded to `66.7%` instead of computed from probe ratios.
  - `metrics["rsr"]` (`metrics.py:159`) defaults to `100.0%` when zero remediations are executed (`len(remediated) == 0`).
- **Token Metrics**: For Arms 3–5 (where LLM is not invoked), TRR is reported as `NOT_MEASURED`, which is correct.

### Audit D — Failure Handling and Reproducibility
- **Error Handling**: `runner.py:81-82` enforces a fail-closed check that rejects unauthorized or unimplemented arms with `ValueError`.
- **Numeric Robustness**: `engine.py:8-18` coerces `None`, `NaN`, and `Inf` to default float `0.0`.
- **Deterministic Seed Formula**: `effective_seed(a, s, r) = 42 + 1000*a + 100*s + r`. Matrix validation confirmed 420 unique `run_id`s and 420 unique `effective_seed`s.
- **Completed Rows**: Zero completed rows. No experimental observations were written.

---

## 4. Arms 3–5 Comparison Table

| Attribute / Feature | Arm 3 (`ARM_3_RULE_BASED`) | Arm 4 (`ARM_4_PHASE2_BASELINE`) | Arm 5 (`ARM_5_CESO_CADE_NO_LLM`) |
|---|---|---|---|
| **Telemetry Provider Mode** | `SimulatedTelemetryProvider` / `ScenarioRegistry` | `SimulatedTelemetryProvider` / `ScenarioRegistry` | `CESOService` / `ScenarioRegistry` |
| **Telemetry Dispatch Path** | `scenario_registry.generate_telemetry(sc_id, fault_type)` | `scenario_registry.generate_telemetry(sc_id, fault_type)` | `ceso_service.load_scenario(sc_id)` [CRITICAL BUG: Erases Fault] |
| **Input Fields Available** | `NetworkState` (interfaces, links, routes, nodes) | `NetworkState` (interfaces, links, routes, nodes) | `NetworkState` (interfaces, links, routes, nodes) |
| **Diagnostic Method** | Discrete Boolean rule priority matching | Continuous Candidate Scoring $S(c)$ | Continuous Candidate Scoring $S(c)$ |
| **Algorithm Version** | `1.0.0-arm3-rule-based` | `2.0.0-phase2` | `2.0.0-phase2` |
| **Confidence Formula** | Fixed $1.0$ (matching rule) / $0.0$ | Margin $S(\text{best}) \cdot (1 - 0.5 S(\text{second}))$ | Margin $S(\text{best}) \cdot (1 - 0.5 S(\text{second}))$ |
| **LLM Escalation Allowed?** | No (`allow_llm = False`) | No (`allow_llm = False` for Arms 3–5 benchmark) | No (`allow_llm = False`) |
| **Matched Telemetry Input?** | Yes (Faulted) | Yes (Faulted) | **NO (Healthy Baseline Telemetry Received)** |
| **Ground-Truth Label Leakage?** | None | None | None |
| **Implementation Readiness** | `PLANNED_READY` | `PLANNED_READY` | `BLOCKED_TELEMETRY_DISPATCH_BUG` |

---

## 5. Metric-Validity Table

| Metric Name | Formula / Formal Definition | Implementation Location | Provenance & Inputs | Denominator / Invalid Handling | Computable Arms 3–5? | Appropriateness & Validity |
|---|---|---|---|---|---|---|
| **Diagnostic Accuracy** | $\frac{N_{\text{correct}}}{N_{\text{evaluable}}} \times 100$ | `backend/app/evaluation/metrics.py:63` | `predicted_fault_label`, `ground_truth_fault_label` | Evaluable completed runs | Yes | Valid |
| **Precision / Recall / F1** | Standard multi-class F1 / Macro-F1 | `backend/app/evaluation/metrics.py:75-99` | Confusion matrix across classes | Evaluable completed runs | Yes | Valid |
| **Evidence Compression Ratio (ECR)** | $\left(1 - \frac{N_{\text{selected}}}{N_{\text{raw}}}\right) \times 100$ | `backend/app/evaluation/metrics.py:102` | `evidence_count`, `total_raw_evidence_count` | Completed runs with raw telemetry | Yes | Valid |
| **Token Reduction Ratio (TRR)** | $\left(1 - \frac{T_{\text{pipeline}}}{T_{\text{raw}}}\right) \times 100$ | `backend/app/evaluation/metrics.py:109` | LLM token count metrics | Completed LLM runs | No (Arms 3–5) | Correctly returned as `NOT_MEASURED` |
| **Mean Time to Diagnosis (MTTD)** | $\text{Mean}(T_{\text{diagnosis\_ms}})$ | `backend/app/evaluation/metrics.py:124` | `diagnosis_latency_ms` | Valid latency runs | Yes | Valid for diagnosis stage |
| **LLM Invocation Rate (LIR)** | $\frac{N_{\text{escalated}}}{N_{\text{total}}} \times 100$ | `backend/app/evaluation/metrics.py:131` | `llm_escalated`, `llm_invocation_count` | Total completed runs | Yes | Valid ($0.0\%$ for Arms 3–5) |
| **Total Latency ($T_{\text{total}}$)** | Sum of subcomponents | `backend/app/evaluation/runner.py:185` | `t_col`, `t_diag`, `t_llm` | All runs | No | **INVALID**: Ignores serialization/logging overhead |
| **Verification Scope Reduction (VSR)** | Probed vs excluded interface ratio | `backend/app/evaluation/metrics.py:150` | Interface probe telemetry | All runs | No | **INVALID**: Hardcoded to `66.7%` |
| **Remediation Success Rate (RSR)** | $\frac{N_{\text{verified\_healthy}}}{N_{\text{remediated}}} \times 100$ | `backend/app/evaluation/metrics.py:159` | `remediation_status`, `verification_result` | Executed remediations | No | **INVALID**: Defaults to `100.0%` when $N_{\text{remediated}} = 0$ |

---

## 6. Failure-Handling and Reproducibility Table

| Failure / Constraint Category | Target Path / Feature | Expected Behavior | Observed Behavior | Verdict & Impact |
|---|---|---|---|---|
| **Unauthorized Arm Dispatch** | `runner.py:80-82` | Fail closed with `ValueError` | Raises `ValueError` for Arm 1, 2, 6, 7 | `PASS` (Strict control flow) |
| **Null / NaN / Inf Telemetry** | `engine.py:8-18` | Safe float coercion to default `0.0` | Coerces `None`, `NaN`, `Inf` to `0.0` | `PASS` (No uncaught exceptions) |
| **Seed Assignment & Mapping** | `experiment_matrix.csv` | Unique mapping for 420 runs | 420 unique `run_id`s & `effective_seed`s | `PASS` (100% reproducible) |
| **Arm 5 Telemetry Fault Isolation** | `runner.py:94` & `service.py:38` | Pass scenario fault to telemetry generator | Resets `active_fault` to `"NONE"` | **`FAIL` (Critical comparability bug)** |
| **Wall-Clock Latency Measurement** | `runner.py:185` | Measure end-to-end duration | Sums subcomponent latencies | **`FAIL` (Under-reports wall-clock latency)** |
| **Un-remediated Metric Reporting** | `metrics.py:159` | Report `NOT_APPLICABLE` when $N_{\text{remediated}}=0$ | Defaults to `100.0%` success | **`FAIL` (Falsely claims 100% RSR)** |

---

## 7. Exact Source Evidence with Line Ranges

- **Telemetry Dispatch Discrepancy**: [`backend/app/evaluation/runner.py:92-97`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L92-L97) vs [`backend/app/ceso/service.py:37-40`](file:///d:/NetOpsAI/backend/app/ceso/service.py#L37-L40) vs [`backend/app/scenarios/registry.py:42-47`](file:///d:/NetOpsAI/backend/app/scenarios/registry.py#L42-L47).
- **Candidate Scoring Preservation**: [`backend/app/cadd/engine.py:258-295`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L258-L295).
- **Tie-Breaking Priority Array**: [`backend/app/cadd/engine.py:39-49`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L39-L49).
- **Confidence Formula Implementation**: [`backend/app/cadd/engine.py:310-315`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L310-L315).
- **Fail-Closed Arm Guard**: [`backend/app/evaluation/runner.py:80-82`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L80-L82).
- **Hardcoded VSR Metric**: [`backend/app/evaluation/metrics.py:150`](file:///d:/NetOpsAI/backend/app/evaluation/metrics.py#L150).
- **Default 100% RSR Metric Flaw**: [`backend/app/evaluation/metrics.py:159`](file:///d:/NetOpsAI/backend/app/evaluation/metrics.py#L159).
- **Subcomponent Latency Summation Defect**: [`backend/app/evaluation/runner.py:185`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L185).

---

## 8. Blocking Issues, Severity, and Precise Corrective Actions

### Blocker 01: Arm 5 Telemetry Fault Erasure Bug
- **Severity**: `CRITICAL`
- **Location**: `backend/app/evaluation/runner.py:94` and `backend/app/ceso/service.py:37-40`.
- **Root Cause**: `ceso_service.load_scenario(sc_id)` calls `scenario_registry.load_scenario(sc_id)`, which sets `self.active_fault = "NONE"`.
- **Corrective Action**: Update `load_scenario` in `ceso_service` to accept `fault_type` parameter (or avoid resetting `active_fault` when called during benchmark execution), ensuring Arm 5 receives the exact same faulted telemetry as Arms 3 and 4.

### Blocker 02: Hardcoded VSR & Default 100% RSR Metric Implementation Flaws
- **Severity**: `HIGH`
- **Location**: `backend/app/evaluation/metrics.py:150, 159`.
- **Root Cause**: `metrics["vsr"]` is hardcoded to `66.7%`. `metrics["rsr"]` defaults to `100.0%` when `len(remediated) == 0`.
- **Corrective Action**: Compute VSR dynamically based on probed vs excluded interfaces. Update RSR to set `status = MetricStatus.NOT_APPLICABLE` when `len(remediated) == 0`.

### Blocker 03: Total Latency Summation Defect
- **Severity**: `MEDIUM`
- **Location**: `backend/app/evaluation/runner.py:185`.
- **Root Cause**: `total_elapsed_ms` is computed as `telemetry_collection_latency_ms + diagnosis_latency_ms + llm_latency_ms`, omitting overall function wall-clock duration and overhead.
- **Corrective Action**: Record `overall_start = time.perf_counter()` at function entry and compute `total_elapsed_ms = (time.perf_counter() - overall_start) * 1000.0`.

### Blocker 04: Freeze Manifest File SHA256 Discrepancy for engine.py
- **Severity**: `MEDIUM`
- **Location**: `scratch/research_v2/phase2/freeze_manifest.json:59`.
- **Root Cause**: `engine.py` SHA256 hash changed due to adding `diagnose_rule_based` for Arm 3.
- **Corrective Action**: Update documentation to clarify method-level equivalence of `diagnose_state` and update freeze manifest notes regarding Phase 3 extensions.

---

## 9. Safe Tests Executed and Their Limitations

1. **Unit Test Suite Run 1**:
   - **Command**: `.venv\Scripts\python.exe -m pytest tests/unit/test_phase2_formula_and_isolation.py tests/unit/test_phase3_arm_corrections.py tests/unit/test_evaluation_metrics.py`
   - **Outcome**: **`PASSED`** (23 / 23 unit tests passed in 3.28s).
   - **Limitations**: Verifies isolated Python functions and rule engine logic. Does NOT run benchmark scenarios or touch network namespaces.
2. **Matrix Validation Test Run 2**:
   - **Command**: `$env:PYTHONPATH="."; .venv\Scripts\python.exe -m pytest tests/unit/test_phase3_matrix_validation.py`
   - **Outcome**: **`PASSED`** (2 / 2 tests passed in 0.04s).
   - **Limitations**: Verifies CSV file structure, row counts, and seed uniqueness. Does NOT execute matrix rows.

---

## 10. Audit Confirmation and Safety Attestation

I hereby certify and confirm:
1. **Zero research experiments were executed** during this audit.
2. **Zero matrix rows** of the 420-row Phase 3 matrix were marked completed or modified.
3. **Zero network changes, fault injections, or remediation commands** were executed on the system or testbed namespaces.
4. **Phase 3 execution remains BLOCKED and UNAUTHORIZED** until all critical and high-severity blocking issues are resolved.
