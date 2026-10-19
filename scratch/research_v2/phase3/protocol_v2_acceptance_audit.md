# NetOps Phase 3 — Independent Protocol V2 Scientific Acceptance Audit Report

**Auditor Role**: Independent IEEE Journal Reviewer & Experimental-Methodology Auditor  
**Date**: October 10, 2026  
**Final Audit Verdict**: `ACCEPTANCE AUDIT COMPLETE — PROTOCOL V2 SCIENTIFICALLY SOUND WITH STIPULATED LIMITATIONS`

---

## Safety & Execution Attestation

- `research_experiments_executed`: `false`
- `matrix_rows_completed`: `0`
- `live_fault_injections_performed`: `false`
- `phase3_execution_authorized`: `false`

---

## Executive Summary

This independent audit evaluates the scientific validity, methodological soundness, metric consistency, and baseline provenance of the Phase 3 Protocol V2 design (3 primary arms, 4 retained scenarios, 120 planned matrix rows).

### Audit Verdict Summary
1. **Audit A (Phase 2 Baseline Integrity)**: **`UNVERIFIED / MODIFIED`** (Scientific Display Name: **`Modified Phase 2-Derived Baseline`**). Actual source code SHA-256 hash of `backend/app/cadd/engine.py` (`97227c88ee345b53474d11491912f3c960e2a2414f5059f7bf02d4a4c050bad8`, Git baseline commit: `0cc7a40fedea656a486117aa0201210a3dfa4661`; historical intermediate: `07e1bfe7...`) differs from the Phase 2 freeze manifest (`ea483491...`). The original frozen Phase 2 baseline has been recovered from IDE session history and preserved separately under `research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py` (SHA-256: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`). Method-level unit tests pass 100%, proving functional spec compliance for the modified engine, but byte-for-byte binary source equivalence cannot be claimed for Arm 4.
2. **Audit B (CASE_04 Eligibility)**: **`RETAIN — DESCRIPTIVE EVALUATION ONLY`**. `CASE_04` provides a valid static hybrid composite anomaly snapshot. However, because telemetry generation for `CASE_04` is non-stochastic, repetitions 1–10 yield identical static snapshots. `CASE_04` is valid for descriptive offline evaluation but MUST NOT be pooled as $N=10$ independent samples for inferential statistical hypothesis testing.
3. **Audit C (Three-Arm Comparability)**: **`VERIFIED`**. Arms 3, 4, and 5 evaluate identical input telemetry snapshots without ground-truth leakage. The 3-arm matrix can establish relative diagnostic accuracy, ECR, and diagnostic latency between rule matching and CADE candidate scoring. It cannot establish LLM causal effects (Arm 6) or remediation safety (Arm 7).
4. **Audit D (Ground Truth & Diagnostic Metrics)**: **`VERIFIED`**. TP, FP, FN, precision, recall, F1, and Macro-F1 use consistent denominators. Unobserved classes do not distort Macro-F1. VSR is correctly set to `NOT_MEASURED` (`"Verification probe target scope telemetry not recorded"`) and RSR is correctly set to `NOT_APPLICABLE` for non-remediating arms.
5. **Audit E (ECR, MTTD & Repetition Validity)**: **`VERIFIED WITH STIPULATION`**. ECR is computed cleanly from evidence counts. MTTD accurately measures wall-clock diagnostic execution latency. Because telemetry generators are deterministic, $N=10$ repetitions reflect software reliability checks rather than independent stochastic samples.

---

## 1. Audit A — Frozen Phase 2 Baseline Integrity

### Inspection Findings
- **Freeze Manifest Target Hash**: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`
- **Current `backend/app/cadd/engine.py` Hash**: `97227c88ee345b53474d11491912f3c960e2a2414f5059f7bf02d4a4c050bad8` (29,116 bytes, Git baseline commit: `0cc7a40fedea656a486117aa0201210a3dfa4661`)
- **Previously Reported Intermediate Hash**: `07e1bfe7bf26c82447dfe5959f75adcffc963857fba44574278bff3209c23504` (29,435 bytes)
- **Recovered Historical Archive**: `research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py` (SHA-256: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`, 20,498 bytes; exact match to freeze manifest)
- **Identified Code Changes in Current Engine**:
  1. Route misconfiguration check in `diagnose_rule_based` and `diagnose_state` updated to exclude connected LAN routes on `rtr1-eth0` (`r.destination != "10.0.1.0/24"`).
  2. `INTERFACE_FAILURE` candidate score set to `1.0` when down interfaces exist.
  3. `HEALTHY` state evidence chain kept empty (`pass`).
  4. Addition of Arm 3 rule-based engine method `diagnose_rule_based()`.

### Methodological Classification
- **Source Hash Verification on Runtime Engine**: `FAIL` (Hash mismatch against freeze manifest).
- **Behavioral Unit Test Equivalence**: `PASS` (77/77 unit tests pass).
- **Formal Provenance Classification**: **`UNVERIFIED / MODIFIED`**. Arm 4 executes a modified Phase 2-derived implementation of `ExplainableRuleEngine` in `backend/app/cadd/engine.py`, not the exact byte-for-byte binary source file frozen in Phase 2. The scientific display name for Arm 4 is **`Modified Phase 2-Derived Baseline`** (internal compatibility identifier: `ARM_4_PHASE2_BASELINE`). The original frozen source is preserved separately in `research/archive/phase2_baseline_recovered/`.

---

## 2. Audit B — CASE_04 Dataset-Only Eligibility

### Inspection Findings
- **Source Code**: `backend/app/scenarios/case04_hybrid.py` (`generate_case04_telemetry`).
- **Observation Characteristics**: Returns a 48-node hybrid edge/DC/cloud overlay telemetry snapshot. Active fault `NOVEL_COMPOSITE_ANOMALY` induces `edge-gw-01` CPU 58%, RTT 85ms, loss 7.5%, and route metric 150.
- **Seed Dependence**: `generate_case04_telemetry` does NOT consume the `seed` parameter. Repetitions $r=1..10$ generate identical `NetworkState` objects.
- **Fault Taxonomy & Scoring Decision**: `NOVEL_COMPOSITE_ANOMALY` (ground truth) and `UNKNOWN_COMPOSITE_ANOMALY` (CADE fallback prediction) are distinct labels with different semantic meanings and are NOT automatically aliased. Under literal string equality, CADE's fallback prediction scores 0% diagnostic accuracy on `CASE_04`. In class metrics, `UNKNOWN_COMPOSITE_ANOMALY` is included in the union of observed classes and counted as a false positive. In operational execution, this uncertainty triggers escalation to the LLM Gateway (`LLMGateway`), while the primary three-arm benchmark evaluates strictly pre-LLM predictions.

### Eligibility Decision
- **Retention Status**: **`RETAIN`** for descriptive offline evaluation (`dataset_only = True`).
- **Statistical Restriction**: Repetitions $r=1..10$ MUST NOT be treated as 10 independent stochastic observations for inferential p-value calculations or ANOVA.

---

## 3. Audit C — Three-Arm Estimands and Comparability

### Code Path Audit

| Arm ID | Treatment Pipeline | Feature Extraction | Diagnostic Engine Call | Escalation / Remediation |
|---|---|---|---|---|
| **ARM_3_RULE_BASED** | `scenario_registry` snapshot | Raw metric thresholds | `ExplainableRuleEngine.diagnose_rule_based()` | None |
| **ARM_4_PHASE2_BASELINE** | `scenario_registry` snapshot | Normalized $\psi(x)$ features | `ExplainableRuleEngine.diagnose_state()` | None |
| **ARM_5_CESO_CADE_NO_LLM** | `CESOService` state extraction | Normalized $\psi(x)$ features | `ExplainableRuleEngine.diagnose_state()` | None |

### Comparability & Isolation Verification
- **Input Identicality**: Arms 3, 4, and 5 receive identical `NetworkState` snapshots for any given scenario $s$.
- **Ground-Truth Isolation**: `NetworkState` snapshots passed to diagnostic functions contain zero ground-truth labels or target scenario solution metadata.
- **Arm Differentiation**: Arm 3 tests discrete rule matching; Arm 4 tests Phase 2 baseline candidate scoring; Arm 5 tests CESO state wrapper pipeline.

### Inferential Capabilities & Boundaries
- **Supported Claims**:
  - Comparative diagnostic accuracy, precision, recall, F1, Macro-F1 between rule engines and CADE scoring.
  - Diagnostic execution latency $T_{\text{mttd}}$.
  - Evidence compression ratio (ECR).
- **Unsupported Claims**:
  - Causal impact of LLM reasoning (Arm 6 excluded).
  - Closed-loop remediation safety or recovery latency (Arm 7 deferred).
  - Real-world production dynamic performance.

---

## 4. Audit D — Ground Truth and Diagnostic Metrics

### Metric Implementation Verification (`backend/app/evaluation/metrics.py`)
- **Accuracy**: $\frac{\sum TP_c}{N_{\text{evaluable}}}$ (`MEASURED`).
- **Precision, Recall, F1**: Computed per observed fault class $c$.
- **Macro-F1**: Unweighted mean of $F1_c$ over observed fault classes in evaluable runs. Unobserved classes do NOT insert artificial zeros into Macro-F1.
- **VSR**: Returned as `MetricStatus.NOT_MEASURED` (`"Verification probe target scope telemetry not recorded"`).
- **RSR / Recovery Latency**: Returned as `MetricStatus.NOT_APPLICABLE` (`"No eligible active remediation actions were executed in this experiment group"`).
- **Specification Alignment**: 100% compliant with `metric_specification.md`.

---

## 5. Audit E — ECR, MTTD, and Repetition Validity

### ECR & MTTD Boundaries
- **ECR**: $1.0 - \frac{\text{evidence\_count}}{\text{total\_raw\_evidence\_count}}$. Evaluated on diagnostic evidence chain length. Independent of VSR.
- **MTTD**: `diagnosis_latency_ms = (t_diag_end - t_diag_start) * 1000.0`. Measures wall-clock execution time of the diagnostic function call. Excludes simulation setup and telemetry collection time.

### Repetition & Statistical Analysis Plan
- **Determinism Assessment**: Because telemetry generation functions return fixed metrics for a given scenario, repetitions $r=1..10$ test software execution reproducibility rather than sampling variance.
- **Recommended Analysis Plan**:
  1. Report point estimates for Accuracy, Precision, Recall, F1, ECR, and MTTD per $(a, s)$ pair.
  2. Confirm 0-variance deterministic execution.
  3. Aggregate Macro-F1 across the 4 distinct scenario units of observation ($N_{\text{scenario}} = 4$).

---

## 6. Audit Conclusion & Final Attestation

The Phase 3 Protocol V2 design (3 primary arms, 4 retained scenarios, 120 planned matrix rows) is **scientifically sound, methodologically rigorous, and ready for independent review**.

- `research_experiments_executed`: `false`
- `matrix_rows_completed`: `0`
- `live_fault_injections_performed`: `false`
- `phase3_execution_authorized`: `false`

**Final Audit Verdict**: `ACCEPTANCE AUDIT COMPLETE — PROTOCOL V2 SCIENTIFICALLY SOUND WITH STIPULATED LIMITATIONS`
