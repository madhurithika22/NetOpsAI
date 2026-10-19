# NetOps Research V2 — Phase 3 Experimental Design and Arm-Readiness Audit Report

**Audit Date**: October 9, 2026  
**Auditor Role**: Independent IEEE Journal/Conference Reviewer, Experimental-Methodology Specialist, Network AIOps Researcher & Senior Python Test Engineer  
**Audit Scope**: Phase 3 Experimental Design, 7 Comparison Arms, 6 Scenarios, Metric Specifications & 420-Run Matrix Plan  
**Overall Audit Verdict**: **`NOT READY — DESIGN OR IMPLEMENTATION BLOCKERS REMAIN`**

---

## 1. Executive Verdict

A comprehensive scientific, methodological, and software readiness audit was conducted for the proposed Phase 3 research benchmark (420 planned runs: 7 arms $\times$ 6 scenarios $\times$ 10 repetitions).

The overall audit verdict is **`NOT READY — DESIGN OR IMPLEMENTATION BLOCKERS REMAIN`**.

While the CADE v2.0.0-phase2 diagnostic engine logic is methodologically sound and Arms 3, 4, and 5 have achieved matched-input telemetry parity and end-to-end latency timing accuracy, critical design and implementation blockers prevent formal research execution authorization:
1. **Scenario Registry ID Mismatch & Missing Definitions (Critical Blocker 01)**: `ScenarioRegistry` ([`backend/app/scenarios/registry.py:26-34`](file:///d:/NetOpsAI/backend/app/scenarios/registry.py#L26-L34)) registers only `CASE_01` through `CASE_04`. The scenario IDs in `experiment_matrix.csv` (`SCN_001` through `SCN_006`) are unmapped in the registry and fail at runtime with `ValueError`. Furthermore, `SCN_005_COMPOSITE_ANOMALY` and `SCN_006_BASELINE_HEALTHY` have no scenario definitions or generator functions in `backend/app/scenarios/`.
2. **Missing Baseline Research Arms 1 & 2 (Critical Blocker 02)**: Baseline Arms 1 (`ARM_1_STATIC_THRESHOLD`) and 2 (`ARM_2_ROLLING_STATISTICAL`) do not exist in the codebase. Dispatched runs in `runner.py:81-82` fail closed with `ValueError`.
3. **Blocked LLM & Closed-Loop Remediation Arms 6 & 7 (High Blockers 03 & 04)**: Local Ollama daemon is offline (Arm 6 blocked). Live Linux network namespace automated remediation execution and active probe verification hooks are not implemented (Arm 7 blocked).

**Safety Attestation**: Zero research experiments were executed, zero network namespaces or states were modified, zero live fault injections were performed, and zero rows of the 420-row research matrix were completed (`phase3_execution_authorized: false`).

---

## 2. Seven-Arm Readiness Audit Table

| Arm ID & Name | Implementation Status | Responsible Source Files & Functions | Runner Dispatchable? | Algorithmic Distinction | Required Dependencies | Evaluated Metrics | Primary Blockers & Evidence Needed |
|---|---|---|---|---|---|---|---|
| **ARM_1** Static Threshold | `MISSING` | None (`backend/app/` missing) | No (`runner.py:81` raises `ValueError`) | Discrete SLA single-metric rules | Python 3.12, `pydantic` | Accuracy, MTTD | Blocker 02: Implement `StaticThresholdDetector` class. |
| **ARM_2** Rolling Statistical | `MISSING` | None (`backend/app/` missing) | No (`runner.py:81` raises `ValueError`) | Rolling window z-score detector | Python 3.12, `pydantic` | Accuracy, MTTD | Blocker 02: Implement `RollingStatisticalDetector` class. |
| **ARM_3** Rule-Based Diagnosis | `IMPLEMENTED` | `ExplainableRuleEngine.diagnose_rule_based` ([`engine.py:58`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L58)) | Yes (`runner.py:106`) | Discrete Boolean priority condition matching | Python 3.12, `pydantic` | Accuracy, P/R/F1, MTTD, LIR ($0\%$), ECR | None. Ready for eligible scenarios. |
| **ARM_4** Frozen Phase 2 Baseline | `IMPLEMENTED` | `ExplainableRuleEngine.diagnose_state` ([`engine.py:219`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L219)) | Yes (`runner.py:109`) | Continuous candidate scoring $S(c)$ with margin discounting | Python 3.12, `pydantic` | Accuracy, P/R/F1, MTTD, LIR ($0\%$), ECR | File SHA256 unverified against manifest. Method pass. |
| **ARM_5** CESO + CADE (No LLM) | `IMPLEMENTED` | `CESOService.load_scenario` ([`service.py:37`](file:///d:/NetOpsAI/backend/app/ceso/service.py#L37)) & `engine.py:219` | Yes (`runner.py:94,109`) | CESO normalized `NetworkState` + CADE continuous scoring | Python 3.12, `pydantic` | Accuracy, P/R/F1, MTTD, LIR ($0\%$), ECR | Telemetry fault propagation patched. Ready. |
| **ARM_6** CESO + CADE + LLM | `BLOCKED` | `LLMGateway.analyze_netops_context` ([`gateway.py:1-120`](file:///d:/NetOpsAI/backend/app/llm/gateway.py)) | No (`runner.py:81` blocks Arm 6) | CADE + Local Ollama LLM secondary escalation | Ollama service, model `llama3.2:3b` | Accuracy, P/R/F1, MTTD, LIR, TRR, EE | Blocker 03: Start Ollama daemon and pull `llama3.2:3b`. |
| **ARM_7** Closed-Loop NetOps | `BLOCKED` | `msvs_service.execute_action_plan` ([`msvs/service.py:70`](file:///d:/NetOpsAI/backend/app/msvs/service.py#L70)) | No (`runner.py:81` blocks Arm 7) | CADE + LLM + Live MSVS remediation + Active Probing | Linux netns, `ip`, `tc`, root privileges | Accuracy, MTTD, LIR, TRR, RSR, URR, NESS | Blocker 04: Implement Phase 4 netns execution hooks. |

---

## 3. Six-Scenario Suitability and Ground-Truth Audit Table

| Scenario ID & Name | Fault Condition & Representation | Ground-Truth Storage & Timing | Expected Telemetry Effect | Ground-Truth Leakage Check | Supported Evaluation Scope | Dataset-Only Flag |
|---|---|---|---|---|---|---|
| **SCN_001** High Latency Congestion | RTT delay injection ($150\text{ ms}$, loss $20\%$). Simulated/Testbed netem. | Stored in `sc_def.fault_definition` prior to prediction. | Link RTT $> 50\text{ ms}$, loss $> 10\%$. Triggers `HIGH_LATENCY_CONGESTION`. | `PASS`: Isolated from `NetworkState` inputs. | Diagnosis evaluation. Live remediation in Arm 7. | `False` |
| **SCN_002** Interface Hard Failure | Admin link down state (`is_up = False`). Simulated/Testbed `ip link`. | Stored in `sc_def.fault_definition` prior to prediction. | `is_up = False` on target interface. Triggers `INTERFACE_FAILURE`. | `PASS`: Isolated from `NetworkState` inputs. | Diagnosis evaluation. Live remediation in Arm 7. | `False` |
| **SCN_003** Route Metric Blackhole | Route egress metric set to $999$. Simulated/Testbed `ip route`. | Stored in `sc_def.fault_definition` prior to prediction. | Metric $\ge 999$ on route. Triggers `ROUTING_MISCONFIGURATION`. | `PASS`: Isolated from `NetworkState` inputs. | Diagnosis evaluation. Live remediation in Arm 7. | `False` |
| **SCN_004** Fabric MTU Mismatch | MTU $1400$ on $9000$-byte jumbo topology. Simulated/Dataset. | Stored in `sc_def.fault_definition` prior to prediction. | `mtu = 1400`, `rx_drops > 100`. Triggers `DC_MTU_MISMATCH`. | `PASS`: Isolated from `NetworkState` inputs. | Diagnosis evaluation ONLY. Remediation `False`. | `True` |
| **SCN_005** Composite Anomaly | Sub-threshold latency ($60\text{ ms}$), loss ($12\%$), errors ($15$). | `MISSING` in registry. No generator code exists. | Sub-threshold metrics across multiple links/interfaces. | `UNVERIFIED` (Missing scenario code). | Diagnosis evaluation ONLY. | `True` |
| **SCN_006** Baseline Healthy State | Unfaulted baseline SLA operation. | `MISSING` in registry. No generator code exists. | All metrics within normal SLA ranges. | `UNVERIFIED` (Missing scenario code). | Diagnosis evaluation ONLY. | `False` |

---

## 4. Matched-Input and Confounding Analysis

- **Matched-Input Parity for Implemented Arms (3, 4, 5)**:
  Patched [`backend/app/ceso/service.py:37-41`](file:///d:/NetOpsAI/backend/app/ceso/service.py#L37-L41) re-injects `fault_type` prior to telemetry normalization. Verified via unit test `test_arm5_telemetry_fault_propagation_and_matching` that Arms 3, 4, and 5 receive 100% identical `NetworkState` snapshots across all fields (`interfaces`, `links`, `routes`, `nodes`, `anomalies_detected`, `topology_id`).
- **Inter-Run Contamination**: `scenario_registry.load_scenario(sc_id)` explicitly resets `self.active_fault = "NONE"` at the start of every run, preventing fault state leakage from previous runs.
- **Scenario Registry ID Mismatch (CRITICAL)**: `ScenarioRegistry` ([`registry.py:26-34`](file:///d:/NetOpsAI/backend/app/scenarios/registry.py#L26-L34)) registers scenario IDs as `CASE_01`, `CASE_02`, `CASE_03`, `CASE_04`. `experiment_matrix.csv` uses `SCN_001_HIGH_LATENCY_CONGESTION` through `SCN_006_BASELINE_HEALTHY`. Running the matrix scenarios in `runner.py` throws `ValueError: Scenario 'SCN_001_...' not found`.
- **Intended Treatments vs Unintended Confounders**:
  - *Intended*: Diagnostic algorithm choice (Arm 3 rules vs Arm 4 candidate scoring vs Arm 5 CESO normalization vs Arm 6 LLM reasoning).
  - *Unintended Confounders*: Platform timing drift (Windows host vs Linux netns), local Ollama latency variance, and un-mapped scenario registry IDs.

---

## 5. Metric Validity and Statistical Design Findings

### Audit of 15 Pre-Registered Metrics

1. **Diagnostic Accuracy (M-01)**: $\frac{N_{\text{correct}}}{N_{\text{evaluable}}} \times 100$. Valid for Arms 3–5. Evaluated over completed runs.
2. **Precision, Recall, F1, Macro-F1 (M-02 to M-04)**: Standard multi-class confusion matrix metrics. Valid for evaluable fault classes.
3. **Detection Latency (M-05 / MTTD)**: Monotonic wall-clock $t_{\text{diagnosis}} - t_{\text{start}}$. Valid for Arms 3–5.
4. **Remediation Success Rate (RSR / M-06)**: Reported as `MetricStatus.NOT_APPLICABLE` when $N_{\text{remediated}} = 0$ ([`metrics.py:192`](file:///d:/NetOpsAI/backend/app/evaluation/metrics.py#L192)). Valid only for Arm 7 live remediations.
5. **Recovery Latency (M-07)**: `MetricStatus.NOT_MEASURED` for Arms 1–6 and dataset-only scenarios. Valid for Arm 7 live remediations.
6. **Verification Failure Rate (M-08)**: `MetricStatus.NOT_MEASURED` for offline/unremediated runs. Valid for Arm 7.
7. **Safety Violation Rate (M-09)**: Evaluates MSVS policy rejections. Valid when MSVS safety rules are executed.
8. **LLM Token Count (M-10 / TRR)**: Reported as `MetricStatus.NOT_MEASURED` for Arms 3–5 (where LLM is not invoked). Valid for Arms 6 & 7.
9. **Evidence Compression Ratio (ECR)**: Evaluates $1.0 - \frac{N_{\text{selected}}}{N_{\text{raw}}}$. Valid diagnostic evidence filtering metric for Arms 3–5 ($80.0\%$ in unit tests).
10. **Verification Scope Reduction (VSR)**: Returned as `MetricStatus.NOT_MEASURED` with reason `"Verification probe target scope telemetry not recorded"` ([`metrics.py:150-156`](file:///d:/NetOpsAI/backend/app/evaluation/metrics.py#L150-L156)). Conflation with ECR resolved.
11. **Total Elapsed Latency**: Monotonic wall-clock timing captured via `overall_wall_start` and `overall_wall_end` ([`runner.py:78, 237`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L78)).

### Statistical Sample Size Rationale ($N=10$)
$N=10$ repetitions per arm-scenario pair is pre-registered as a **proposed design parameter**. For empirical research claims, sample variance $s^2$ must be calculated from pilot runs to construct 95% Confidence Intervals ($\text{CI}_{95\%} = \bar{x} \pm t_{0.025, 9} \cdot \frac{s}{\sqrt{10}}$, where $t_{0.025, 9} = 2.262$). Non-parametric Kruskal-Wallis tests should be used for latency distributions.

---

## 6. Matrix Integrity and Reproducibility

- **Matrix Structure**: [`scratch/research_v2/phase3/experiment_matrix.csv`](file:///d:/NetOpsAI/scratch/research_v2/phase3/experiment_matrix.csv) contains 420 planned rows ($7\text{ arms} \times 6\text{ scenarios} \times 10\text{ repetitions}$).
- **Unique Identifiers & Seeds**: `validate_experiment_matrix.py` confirmed 420 unique `run_id`s and 420 unique `effective_seed`s using formula $\text{effective\_seed}(a, s, r) = 42 + 1000\cdot a + 100\cdot s + r$.
- **Row Breakdown**:
  - Implemented & Eligible Rows: 180 rows (Arms 3, 4, 5 $\times$ 6 scenarios $\times$ 10 reps).
  - Unimplemented Rows: 120 rows (Arms 1, 2).
  - Blocked Rows: 120 rows (Arms 6, 7).
  - Completed Rows: **0 rows**.
- **Phase 2 Source Integrity Disclosure**: `backend/app/cadd/engine.py` SHA256 (`07e1bfe7...`) differs from `freeze_manifest.json` (`ea483491...`). File preservation remains `UNVERIFIED` while method-level behavioral equivalence passes.

---

## 7. Blockers Ranked by Severity

### Critical Blockers
1. **BLOCKER-01 (Scenario Registry Mismatch & Missing Definitions)**:
   - *Location*: [`backend/app/scenarios/registry.py:26-34`](file:///d:/NetOpsAI/backend/app/scenarios/registry.py#L26-L34).
   - *Impact*: `ScenarioRegistry` only registers `CASE_01..04`. Matrix IDs `SCN_001..006` fail at runtime. `SCN_005` (Composite Anomaly) and `SCN_006` (Baseline Healthy) lack scenario generator code.
2. **BLOCKER-02 (Unimplemented Baseline Research Arms 1 & 2)**:
   - *Location*: [`backend/app/evaluation/runner.py:81-82`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L81-L82).
   - *Impact*: 120 planned matrix rows for Arm 1 (`StaticThreshold`) and Arm 2 (`RollingStatistical`) cannot execute and fail closed with `ValueError`.

### High Blockers
3. **BLOCKER-03 (Blocked Local LLM Service for Arm 6)**:
   - *Location*: `backend/app/llm/gateway.py`.
   - *Impact*: 60 planned matrix rows for Arm 6 cannot execute due to missing Ollama daemon (`http://localhost:11434` connection refused).
4. **BLOCKER-04 (Missing Live Remediation & Probe Verification Hooks for Arm 7)**:
   - *Location*: `backend/app/msvs/service.py`.
   - *Impact*: 60 planned matrix rows for Arm 7 cannot execute live Linux netns remediation or active probe recovery verification.

### Medium Blockers
5. **BLOCKER-05 (Phase 2 Baseline File Hash Discrepancy)**:
   - *Location*: `scratch/research_v2/phase2/freeze_manifest.json:59`.
   - *Impact*: File-level SHA256 match fails. Method-level behavioral equivalence passes. Requires formal disclosure.

---

## 8. Prioritized Corrective-Action Plan

1. **Fix Scenario Registry Mappings & Add Missing Scenarios (Target: `backend/app/scenarios/`)**:
   - Update `ScenarioRegistry._register_defaults()` in `registry.py` to register aliases for `SCN_001_HIGH_LATENCY_CONGESTION` through `SCN_004_FABRIC_MTU_MISMATCH`.
   - Implement `generate_case05_telemetry` (`SCN_005_COMPOSITE_ANOMALY`) and `generate_case06_telemetry` (`SCN_006_BASELINE_HEALTHY`) in `backend/app/scenarios/`.
2. **Implement Baseline Arms 1 and 2 (Target: `backend/app/cadd/baselines.py` & `runner.py`)**:
   - Implement `StaticThresholdDetector` (Arm 1) and `RollingStatisticalDetector` (Arm 2).
   - Add `"ARM_1_STATIC_THRESHOLD"` and `"ARM_2_ROLLING_STATISTICAL"` to `AUTHORIZED_ARMS` in `runner.py`.
3. **Configure Ollama Service (Target: Local WSL Environment & `gateway.py`)**:
   - Start Ollama daemon service on port 11434 and load model `llama3.2:3b`.
   - Add `"ARM_6_CESO_CADE_OLLAMA_LLM"` to `AUTHORIZED_ARMS` in `runner.py`.
4. **Implement Phase 4 Live Remediation & Verification Hooks (Target: `backend/app/msvs/` & testbed)**:
   - Implement live Linux netns execution hooks (`ip link set`, `tc qdisc`, `ip route`) and active probe verification suite.
   - Add `"ARM_7_CLOSED_LOOP_NETOPS"` to `AUTHORIZED_ARMS` in `runner.py`.

---

## 9. Evidence Citations

- **Arm Dispatch Guard**: [`backend/app/evaluation/runner.py:80-82`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L80-L82).
- **Arm 3 Rule Engine Implementation**: [`backend/app/cadd/engine.py:58-217`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L58-L217).
- **Arm 4 Candidate Scoring Implementation**: [`backend/app/cadd/engine.py:219-462`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L219-L462).
- **Arm 5 Telemetry Fault Propagation Fix**: [`backend/app/ceso/service.py:37-41`](file:///d:/NetOpsAI/backend/app/ceso/service.py#L37-L41) & [`backend/app/evaluation/runner.py:94`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L94).
- **Scenario Registry Mismatch**: [`backend/app/scenarios/registry.py:26-34`](file:///d:/NetOpsAI/backend/app/scenarios/registry.py#L26-L34).
- **VSR NOT_MEASURED Implementation**: [`backend/app/evaluation/metrics.py:150-156`](file:///d:/NetOpsAI/backend/app/evaluation/metrics.py#L150-L156).
- **RSR NOT_APPLICABLE Implementation**: [`backend/app/evaluation/metrics.py:192-198`](file:///d:/NetOpsAI/backend/app/evaluation/metrics.py#L192-L198).
- **End-to-End Latency Instrumentation**: [`backend/app/evaluation/runner.py:78, 237`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L78).

---

## 10. Safety Attestation & Execution Status

- `research_experiments_executed`: `false`
- `matrix_rows_completed`: `0`
- `live_fault_injections_performed`: `false`
- `phase3_execution_authorized`: `false`

Zero research matrix rows were executed, zero research observations were written, and zero live network changes were performed during this audit.

---

## 11. Final Audit Verdict

**`NOT READY — DESIGN OR IMPLEMENTATION BLOCKERS REMAIN`**
