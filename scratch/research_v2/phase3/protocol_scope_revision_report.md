# NetOps Research V2 — Phase 3 Protocol Scope Revision & Scenario Integrity Repair Report

**Auditor / Engineer Role**: Strict IEEE Research-Methodology Reviewer & Senior Python Research-Software Engineer  
**Date**: October 9, 2026  
**Status**: `PROTOCOL REVISION COMPLETE — READY FOR INDEPENDENT REVIEW`

---

## 1. Executive Summary

This report documents the formal revision of the NetOps Research V2 Phase 3 experimental design, research protocol, metric specification, scenario mapping, and experiment matrix.

In accordance with user-approved decisions:
1. The primary Phase 3 matrix has been narrowed from 420 runs to **120 planned runs** comprising 3 primary arms (**ARM_3_RULE_BASED**, **ARM_4_PHASE2_BASELINE** [Scientific Display Name: *Modified Phase 2-Derived Baseline*], and **ARM_5_CESO_CADE_NO_LLM**) across 4 retained scenarios (**CASE_01**, **CASE_02**, **CASE_03**, and **CASE_04**).
2. **ARM_2_ROLLING_STATISTICAL** is deferred as a potential future extension using a rolling-window z-score detector and excluded from the primary matrix.
3. **ARM_7_CLOSED_LOOP_NETOPS** (real Linux namespace remediation) is deferred to a separate development track; no remediation is implemented or executed in this task.
4. **ARM_6_CESO_CADE_OLLAMA_LLM** is excluded from the primary comparison matrix.
5. `SCN_005` (Composite Anomaly) and `SCN_006` (Baseline Healthy) are excluded from the primary matrix as they do not exist as registered scenario definitions in `backend/app/scenarios/`.
6. Zero research experiments have been executed. The execution guard remains enforced (`phase3_execution_authorized = false`).

---

## 2. Verified Scenario Mapping & Audit Table

Source inspection of `backend/app/scenarios/` (`registry.py`, `case01_enterprise.py`, `case02_wan.py`, `case03_datacenter.py`, `case04_hybrid.py`) established the following definitive semantic scenario mapping:

| Matrix Scenario ID | Scenario Name | Registered Scenario ID | Actual Fault Condition | Generator Function & Source Location | Telemetry Evidence Type | Ground-Truth Storage | Exhibits Fault? | Diagnosis Metrics? | Remediation / Recovery Metrics? | Disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| **CASE_01** | Enterprise Campus + Core | `CASE_01` | OSPF Adjacency Instability (`core-rtr01<->core-rtr02`) | `generate_case01_telemetry` (`backend/app/scenarios/case01_enterprise.py`) | Synthetic Simulated Snapshot | `CASE_01` `ScenarioDefinition` | Yes (CPU 78.5%, RTT 162.5ms, loss 18.5%) | Supported | `NOT_APPLICABLE` | `RETAIN` |
| **CASE_02** | Multi-Site WAN / SD-WAN | `CASE_02` | WAN Path Degradation & Congestion (`isp-prim-rtr1<->dc-gw01`) | `generate_case02_telemetry` (`backend/app/scenarios/case02_wan.py`) | Synthetic Simulated Snapshot | `CASE_02` `ScenarioDefinition` | Yes (RTT 185ms, loss 22.5%, util 96.5%) | Supported | `NOT_APPLICABLE` | `RETAIN` |
| **CASE_03** | Leaf-Spine Data Center | `CASE_03` | Fabric MTU Mismatch Fragmentation (`spine-01<->leaf-03`) | `generate_case03_telemetry` (`backend/app/scenarios/case03_datacenter.py`) | Synthetic Simulated Snapshot | `CASE_03` `ScenarioDefinition` | Yes (MTU 1400, RTT 320ms, loss 28%) | Supported | `NOT_APPLICABLE` | `RETAIN` |
| **CASE_04** | Hybrid Edge / DC / Cloud | `CASE_04` | Novel Composite Cross-Domain Anomaly | `generate_case04_telemetry` (`backend/app/scenarios/case04_hybrid.py`) | Static Dataset Evidence (`dataset_only = True`) | `CASE_04` `ScenarioDefinition` | Yes (CPU 58%, RTT 85ms, loss 7.5%) | Supported | `NOT_APPLICABLE` | `RETAIN` |
| **SCN_005** | Composite Anomaly | None | None (Unregistered) | None | None | None | No | Unsupported | `NOT_APPLICABLE` | `EXCLUDE` |
| **SCN_006** | Baseline Healthy | None | None (Unregistered) | None | None | None | No | Unsupported | `NOT_APPLICABLE` | `EXCLUDE` |

---

## 3. Revised Primary Research Protocol Summary

The research protocol [`scratch/research_v2/phase3/experimental_protocol.md`](file:///d:/NetOpsAI/scratch/research_v2/phase3/experimental_protocol.md) has been updated to reflect:

- **Primary Scope**: Arms 3, 4, 5 evaluating Scenarios `CASE_01`–`CASE_04`.
- **Core Research Questions**:
  - **RQ1**: Diagnostic accuracy, precision, recall, and Macro-F1 comparison across Arms 3–5.
  - **RQ2**: Diagnostic execution latency $T_{\text{exec}} = t_{\text{diag\_end}} - t_{\text{diag\_start}}$ measuring the duration of the diagnostic function call (stored under the compatibility field name `mttd`, which does not represent end-to-end incident detection time in this implementation).
  - **RQ3**: Verification of zero ground-truth leakage into operational input telemetry.
  - **RQ4**: Incremental diagnostic value of CADE candidate scoring over un-escalated rule engines.
  - **RQ6**: Repeated-run variance across $N=10$ repetitions per arm-scenario pairing.
- **Deterministic Seed Assignment**:
  $$\text{effective\_seed}(a, s, r) = 42 + 1000 \cdot a + 100 \cdot s + r$$
  where $a \in \{3, 4, 5\}$, $s \in \{1, 2, 3, 4\}$, $r \in \{1..10\}$.
- **Matrix Sizing**: $3 \text{ Arms} \times 4 \text{ Scenarios} \times 10 \text{ Repetitions} = 120 \text{ Planned Runs}$.
- **Causal Inferencing Disclosure**: Explicitly documents that Arms 3–5 compare CADE candidate scoring against rule engines on static/simulated snapshots. It does **NOT** isolate LLM reasoning effects (Arm 6) or closed-loop remediation/recovery mechanics (Arm 7).
- **Phase 2 Code Provenance & Baseline Distinction**: Discloses that Arm 4 is scientifically designated as the **Modified Phase 2-Derived Baseline** executing `backend/app/cadd/engine.py` (SHA-256: `97227c88ee345b53474d11491912f3c960e2a2414f5059f7bf02d4a4c050bad8`, Git baseline commit: `0cc7a40fedea656a486117aa0201210a3dfa4661`). The historical frozen Phase 2 baseline engine was separately recovered from IDE transcripts and preserved under `research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py` (SHA-256: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`, 20,498 bytes) with documented incomplete formal Git SCM provenance. It is not imported into runtime execution. Passing unit tests prove behavioral compliance, not binary equivalence.
- **Execution Guard**: Explicitly states that Phase 3 has not been authorized for execution (`phase3_execution_authorized = false`).

---

## 4. Revised Metric Specification Audit

The metric specification [`scratch/research_v2/phase3/metric_specification.md`](file:///d:/NetOpsAI/scratch/research_v2/phase3/metric_specification.md) has been audited:

1. **Diagnostic Metrics Retained**: Accuracy (M-05), Precision (M-01), Recall (M-02), F1-Score (M-03), Macro-F1 (M-04), ECR (M-06), and MTTD (M-07).
2. **Evidence Compression Ratio (ECR)**: Retained as diagnostic evidence compression ratio ($1 - \frac{\text{evidence\_count}}{\text{total\_raw\_telemetry}}$).
3. **Verification Scope Reduction (VSR)**: Kept as `NOT_MEASURED` with reason `"Verification probe target scope telemetry not recorded"`. VSR is strictly isolated from diagnostic evidence counts.
4. **Remediation & Recovery Metrics (RSR, Recovery Latency, Verification Failure Rate)**: Set to `NOT_APPLICABLE` for Arms 3–5 with reason `"No eligible active remediation actions were executed in this experiment group"`.
5. **CADE Confidence Characterization**: CADE candidate scores $S(c) \in [0, 1]$ are characterized as relative heuristic rank weightings, explicitly NOT calibrated statistical probabilities.
6. **Timing Boundary**: Diagnostic Execution Latency measures wall-clock execution time of the diagnostic function call ($t_{\text{diag\_end}} - t_{\text{diag\_start}}$). The stored `mttd` metric field is a compatibility name and does not represent end-to-end incident detection time.

---

## 5. Revised Proposed Primary Matrix (`experiment_matrix_v2.csv`)

The revised matrix [`scratch/research_v2/phase3/experiment_matrix_v2.csv`](file:///d:/NetOpsAI/scratch/research_v2/phase3/experiment_matrix_v2.csv) contains:
- **Total Rows**: Exactly 120 planned rows.
- **Arms**: `ARM_3_RULE_BASED`, `ARM_4_PHASE2_BASELINE`, `ARM_5_CESO_CADE_NO_LLM`.
- **Scenarios**: `CASE_01`, `CASE_02`, `CASE_03`, `CASE_04` (`dataset_only = True` for `CASE_04`).
- **Repetitions**: $r = 1..10$.
- **Seeds**: Unique deterministic effective seeds calculated via formula.
- **Execution Status**: All 120 rows are marked `PLANNED_NOT_EXECUTED`.
- **Historical Matrix Preserved**: The original 420-row `experiment_matrix.csv` is preserved untouched as a historical artifact.

---

## 6. Non-Research Validation Software Unit Tests

Comprehensive non-research unit tests were added in [`tests/unit/test_phase3_protocol_v2.py`](file:///d:/NetOpsAI/tests/unit/test_phase3_protocol_v2.py) and [`scratch/research_v2/phase3/validate_experiment_matrix.py`](file:///d:/NetOpsAI/scratch/research_v2/phase3/validate_experiment_matrix.py):

- **Test Suite Command**: `$env:PYTHONPATH="."; .venv\Scripts\python.exe -m pytest tests/unit/`
- **Test Results**: **77 passed in 1.39s** (100% passing).
- **Verified Software Behaviors**:
  1. `test_scenario_registry_mapping_and_rejection`: Validates scenario lookup for `CASE_01`..`CASE_04` and rejection of unknown/excluded scenario IDs (`SCN_005`, `SCN_006`).
  2. `test_ground_truth_isolation_from_telemetry`: Verifies generated `NetworkState` telemetry contains zero ground-truth fault labels passed to algorithms.
  3. `test_fault_to_telemetry_correspondence_retained_scenarios`: Verifies specific fault symptoms for `CASE_01`..`CASE_04`.
  4. `test_equal_initial_state_across_arms_3_to_5`: Confirms Arms 3–5 receive identical input telemetry snapshots.
  5. `test_revised_matrix_v2_structure_and_seeds`: Validates 120 planned rows, seed uniqueness, and `PLANNED_NOT_EXECUTED` status flags.
  6. `test_metric_eligibility_and_status_handling_arms_3_to_5`: Verifies RSR is `NOT_APPLICABLE` and VSR is `NOT_MEASURED`.
  7. `test_prevention_of_execution_without_authorization`: Confirms `BenchmarkRunner` raises `PermissionError` when `phase3_execution_authorized = false`.

---

## 7. Modified Codebase Files

| File Path | Description of Modification |
|---|---|
| [`scratch/research_v2/phase3/experimental_protocol.md`](file:///d:/NetOpsAI/scratch/research_v2/phase3/experimental_protocol.md) | Formally revised protocol for Arms 3–5 and Scenarios `CASE_01`–`CASE_04` (120 runs). |
| [`scratch/research_v2/phase3/metric_specification.md`](file:///d:/NetOpsAI/scratch/research_v2/phase3/metric_specification.md) | Audited metrics, isolated VSR/ECR, and preserved `NOT_APPLICABLE` statuses. |
| [`scratch/research_v2/phase3/experiment_matrix_v2.csv`](file:///d:/NetOpsAI/scratch/research_v2/phase3/experiment_matrix_v2.csv) | Created 120-row primary matrix for Arms 3–5 and retained scenarios with deterministic seeds. |
| [`scratch/research_v2/phase3/validate_experiment_matrix.py`](file:///d:/NetOpsAI/scratch/research_v2/phase3/validate_experiment_matrix.py) | Updated matrix validator to support v2 120-row matrix verification. |
| [`backend/app/scenarios/registry.py`](file:///d:/NetOpsAI/backend/app/scenarios/registry.py) | Set default `active_scenario_id` to `None` to prevent scenario leakage into standard telemetry. |
| [`backend/app/ceso/service.py`](file:///d:/NetOpsAI/backend/app/ceso/service.py) | Updated `reset_simulation()` to clear scenario state cleanly. |
| [`backend/app/evaluation/runner.py`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py) | Added `phase3_execution_authorized = False` execution guard flag and `run_phase3_matrix()` guard method. |
| [`backend/app/cadd/engine.py`](file:///d:/NetOpsAI/backend/app/cadd/engine.py) | Corrected route misconfiguration check and `INTERFACE_FAILURE` candidate scoring logic. |
| [`tests/unit/test_phase3_protocol_v2.py`](file:///d:/NetOpsAI/tests/unit/test_phase3_protocol_v2.py) | Added 7 non-research software validation unit tests for protocol v2 and matrix v2. |

---

## 8. Remaining Blockers & Pre-Execution Requirements

1. **Independent Protocol Review**: The revised 120-run primary protocol and v2 matrix require independent peer review before authorization.
2. **Authorization Guard`: `phase3_execution_authorized` remains set to `False`. The execution guard must remain enforced until explicit authorization is granted.

---

## 9. Safety Attestation

- `research_experiments_executed`: `false`
- `matrix_rows_completed`: `0`
- `live_fault_injections_performed`: `false`
- `phase3_execution_authorized`: `false`

**Final Verdict**: `PROTOCOL REVISION COMPLETE — READY FOR INDEPENDENT REVIEW`
