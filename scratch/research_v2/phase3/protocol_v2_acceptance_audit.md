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
1. **Audit A (Phase 2 Baseline Integrity)**: **`UNVERIFIED / MODIFIED`**. Source code SHA-256 hash of `backend/app/cadd/engine.py` (`07e1bfe7...`) differs from the Phase 2 freeze manifest (`ea483491...`). Method-level unit tests pass 100%, proving functional spec compliance, but byte-for-byte binary source equivalence cannot be claimed.
2. **Audit B (CASE_04 Eligibility)**: **`RETAIN — DESCRIPTIVE EVALUATION ONLY`**. `CASE_04` provides a valid static hybrid composite anomaly snapshot. However, because telemetry generation for `CASE_04` is non-stochastic, repetitions 1–10 yield identical static snapshots. `CASE_04` is valid for descriptive offline evaluation but MUST NOT be pooled as $N=10$ independent samples for inferential statistical hypothesis testing.
3. **Audit C (Three-Arm Comparability)**: **`VERIFIED`**. Arms 3, 4, and 5 evaluate identical input telemetry snapshots without ground-truth leakage. The 3-arm matrix can establish relative diagnostic accuracy, ECR, and diagnostic latency between rule matching and CADE candidate scoring. It cannot establish LLM causal effects (Arm 6) or remediation safety (Arm 7).
4. **Audit D (Ground Truth & Diagnostic Metrics)**: **`VERIFIED`**. TP, FP, FN, precision, recall, F1, and Macro-F1 use consistent denominators. Unobserved classes do not distort Macro-F1. VSR is correctly set to `NOT_MEASURED` (`"Verification probe target scope telemetry not recorded"`) and RSR is correctly set to `NOT_APPLICABLE` for non-remediating arms.
5. **Audit E (ECR, MTTD & Repetition Validity)**: **`VERIFIED WITH STIPULATION`**. ECR is computed cleanly from evidence counts. MTTD accurately measures wall-clock diagnostic execution latency. Because telemetry generators are deterministic, $N=10$ repetitions reflect software reliability checks rather than independent stochastic samples.

---

## 1. Audit A — Frozen Phase 2 Baseline Integrity

### Inspection Findings
- **Freeze Manifest Target Hash**: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`
- **Current `backend/app/cadd/engine.py` Hash**: `07e1bfe7bf26c82447dfe5959f75adcffc963857fba44574278bff3209c23504`
- **Identified Code Changes**:
  1. Route misconfiguration check in `diagnose_rule_based` and `diagnose_state` updated to exclude connected LAN routes on `rtr1-eth0` (`r.destination != "10.0.1.0/24"`).
  2. `INTERFACE_FAILURE` candidate score set to `1.0` when down interfaces exist.
  3. `HEALTHY` state evidence chain kept empty (`pass`).

### Methodological Classification
- **Source Hash Verification**: `FAIL` (Hash mismatch against freeze manifest).
- **Behavioral Unit Test Equivalence**: `PASS` (77/77 unit tests pass).
- **Formal Provenance Classification**: **`UNVERIFIED / MODIFIED`**. Arm 4 executes a functionally corrected implementation of `ExplainableRuleEngine` v2.0.0-phase2, not the exact byte-for-byte binary source file frozen in Phase 2.

---

## 2. Audit B — CASE_04 Dataset-Only Eligibility

### Inspection Findings
- **Source Code**: `backend/app/scenarios/case04_hybrid.py` (`generate_case04_telemetry`).
- **Observation Characteristics**: Returns a 48-node hybrid edge/DC/cloud overlay telemetry snapshot. Active fault `NOVEL_COMPOSITE_ANOMALY` induces `edge-gw-01` CPU 58%, RTT 85ms, loss 7.5%, and route metric 150.
- **Seed Dependence**: `generate_case04_telemetry` does NOT consume the `seed` parameter. Repetitions $r=1..10$ generate identical `NetworkState` objects.
- **Fault Taxonomy Mapping**: `NOVEL_COMPOSITE_ANOMALY` evaluates `UNKNOWN_COMPOSITE_ANOMALY` in CADE when candidate scores $< 0.70$ and anomalies are detected. It represents a valid multi-layer overlay anomaly class.

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
