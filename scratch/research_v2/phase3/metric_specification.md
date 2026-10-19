# NetOps Research V2 — Phase 3 Metric Specification (Scope Revision 2.0)

## Status: PRE-REGISTERED METRIC SPECIFICATION (NARROWED SCOPE)

---

## 1. Metric Audit & Selection for Arms 3–5

Every metric has been audited against the narrowed primary experimental design (Arms 3, 4, 5 across Scenarios `CASE_01`–`CASE_04`).

| Metric ID | Metric Name | Mathematical Formula | Measurement Unit | Scope & Arm Eligibility | Status Policy & Handling Rules |
|---|---|---|---|---|---|
| **M-01** | Diagnostic Precision ($P_c$) | $P_c = \frac{TP_c}{TP_c + FP_c}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 (All Scenarios) | `NOT_MEASURED` if denominator $= 0$ |
| **M-02** | Diagnostic Recall ($R_c$) | $R_c = \frac{TP_c}{TP_c + FN_c}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 (All Scenarios) | `NOT_MEASURED` if denominator $= 0$ |
| **M-03** | Diagnostic F1-Score ($F1_c$) | $F1_c = \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 (All Scenarios) | `NOT_MEASURED` if $P_c + R_c = 0$ |
| **M-04** | Macro-F1 ($F1_{\text{macro}}$) | $F1_{\text{macro}} = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} F1_c$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 (Global Matrix) | Excludes `NOT_MEASURED` fault classes |
| **M-05** | Diagnostic Accuracy | $\text{Acc} = \frac{\sum TP_c}{N_{\text{total}}}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 (All Scenarios) | `MEASURED` over evaluable runs |
| **M-06** | Evidence Compression Ratio (ECR) | $\text{ECR} = 1 - \frac{N_{\text{selected\_evidence}}}{N_{\text{total\_raw\_telemetry}}}$ | Ratio $[0, 1]$ or $\%$ | Arms 4, 5 (All Scenarios) | `MEASURED` when raw evidence count $> 0$; `NOT_MEASURED` if telemetry count missing |
| **M-07** | Diagnostic Execution Latency (Compatibility Name: MTTD) | $T_{\text{exec}} = t_{\text{diag\_end}} - t_{\text{diag\_start}}$ | Milliseconds (ms) | Arms 3, 4, 5 (All Scenarios) | Measured as wall-clock elapsed time of the diagnostic function call (`diagnosis_latency_ms`). Stored compatibility field name `mttd` does NOT represent end-to-end incident detection or telemetry ingestion time. |
| **M-08** | Verification Scope Reduction (VSR) | $\text{VSR} = 1 - \frac{N_{\text{probes\_active}}}{N_{\text{probes\_total}}}$ | Ratio $[0, 1]$ or $\%$ | All Arms | **Strictly `NOT_MEASURED`** (Reason: `"Verification probe target scope telemetry not recorded"`) |
| **M-09** | Remediation Success Rate (RSR) | $\text{RSR} = \frac{N_{\text{verified\_success}}}{N_{\text{remediations\_executed}}}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 | **Strictly `NOT_APPLICABLE`** (Reason: `"No eligible active remediation actions were executed in this experiment group"`) |
| **M-10** | Recovery Latency ($T_{\text{recover}}$) | $T_{\text{recover}} = t_{\text{verify\_pass}} - t_{\text{action\_start}}$ | Seconds (s) | Arms 3, 4, 5 | **Strictly `NOT_APPLICABLE`** (Reason: `"Remediation not executed by diagnostic-only arms"`) |
| **M-11** | Verification Failure Rate | $V_{\text{fail}} = \frac{N_{\text{verify\_fail}}}{N_{\text{attempts}}}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 | **Strictly `NOT_APPLICABLE`** (Reason: `"Remediation not executed by diagnostic-only arms"`) |
| **M-12** | LLM Invocation Rate (LIR) | $\text{LIR} = \frac{N_{\text{llm\_calls}}}{N_{\text{total\_runs}}}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 | `MEASURED` as $0.0\%$ (No LLM escalation in Arms 3–5) |
| **M-13** | Escalation Efficiency (EE) | $\text{EE} = \text{Acc}_{\text{post\_llm}} - \text{Acc}_{\text{pre\_llm}}$ | Ratio $[0, 1]$ or $\%$ | Arms 3, 4, 5 | **Strictly `NOT_APPLICABLE`** (Reason: `"No diagnostic runs were escalated to LLM reasoning (resolved via rule-engine)"`) |

---

## 2. Key Metric Boundaries & Mathematical Distinction

1. **ECR vs. VSR Separation**:
   - **ECR (Evidence Compression Ratio)**: Measures the percentage reduction from raw observations to selected critical telemetry evidence ($1 - \frac{\text{evidence\_count}}{\text{raw\_evidence\_count}}$). Evaluated for diagnostic evidence.
   - **VSR (Verification Scope Reduction)**: Measures reduction in verification probe target scope. Requires active verification probe scope telemetry. Because numerical probe target scope telemetry is not recorded in `ExperimentRun`, VSR always returns `MetricStatus.NOT_MEASURED` with reason `"Verification probe target scope telemetry not recorded"`. VSR MUST NOT be computed from diagnostic evidence counts.
2. **`NOT_APPLICABLE` vs. `NOT_MEASURED` Status Preservation**:
   - `NOT_APPLICABLE`: Assigned when a metric's underlying process was intentionally not executed by design (e.g. RSR, Recovery Latency, EE for Arms 3–5).
   - `NOT_MEASURED`: Assigned when a metric applies in principle but required data field telemetry was not recorded or sample count is 0.
3. **CADE Confidence Characterization**:
   - Heuristic candidate score $S(c) \in [0, 1]$ produced by CADE in Arm 5 represents relative heuristic rank weighting ($w_{\text{topo}} \cdot S_{\text{topo}} + w_{\text{telemetry}} \cdot S_{\text{telemetry}} + w_{\text{history}} \cdot S_{\text{history}}$).
   - $S(c)$ MUST NOT be described or presented as a calibrated statistical probability.
4. **Diagnostic Execution Latency vs. End-to-End MTTD**:
   - In this implementation (`backend/app/evaluation/runner.py`), the recorded latency metric (stored under the compatibility field name `mttd` in `ExperimentRun` and `EvaluationSummary`) measures strictly the **diagnostic execution latency** of the algorithm function call (`diagnosis_latency_ms = (t_diag_end - t_diag_start) * 1000.0`).
   - Telemetry collection latency is timed separately (`telemetry_collection_latency_ms`).
   - The stored `mttd` field is a historical compatibility identifier and does NOT represent end-to-end incident detection time from network fault onset, nor total pipeline latency.
   - Any latency summary must state its execution scope (diagnostic function duration) and host hardware/OS environment.
5. **Arm 4 Baseline Designation & Provenance Boundary**:
   - For all metric evaluations, Arm 4 is scientifically designated as the **Modified Phase 2-Derived Baseline** (internal programmatic compatibility ID: `ARM_4_PHASE2_BASELINE`).
   - Arm 4 evaluates the modified Phase 2-derived engine currently in `backend/app/cadd/engine.py` (SHA-256: `97227c88ee345b53474d11491912f3c960e2a2414f5059f7bf02d4a4c050bad8`, Git baseline commit: `0cc7a40fedea656a486117aa0201210a3dfa4661`).
   - The original frozen Phase 2 engine is preserved separately in `research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py` (SHA-256: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`) and is not imported by the benchmark suite.
   - CASE_04 repetitions remain descriptive-only; identical deterministic repetitions across all arms are reliability checks and must not be treated as independent stochastic observations.
6. **Out-of-Vocabulary Class Accounting & Macro-F1 Set Definition**:
   - Per-class metrics ($P_c, R_c, F1_c$) and Macro-F1 ($F1_{\text{macro}}$) evaluate the union of observed ground-truth and predicted classes: $\mathcal{C} = \mathcal{C}_{\text{ground\_truth}} \cup \mathcal{C}_{\text{predicted}}$.
   - Predicted-only labels (such as `UNKNOWN_COMPOSITE_ANOMALY` predicted against `NOVEL_COMPOSITE_ANOMALY`) are explicitly included in $\mathcal{C}$ and contribute False Positives ($FP$), properly penalizing precision and Macro-F1 rather than being omitted.
   - Diagnostic accuracy is strictly based on literal string equality between the initial pre-LLM prediction and ground truth. `UNKNOWN_COMPOSITE_ANOMALY` is NOT aliased to `NOVEL_COMPOSITE_ANOMALY`.
   - Post-escalation operational LLM results are recorded separately under `post_llm_diagnosis` and do not alter the pre-LLM primary diagnostic scores.

---

## 3. Data Integrity & Reporting Policy

- No zero substitution for missing data.
- Per-run observations (`ExperimentRun`) record raw timing, diagnosis labels, evidence lists, and seed values.
- Summary statistics (`EvaluationSummary`) compute aggregate metrics across runs while excluding invalid or unmeasured runs from denominators.
- **Descriptive Reporting for Deterministic Repetitions**: Primary classification metrics (Accuracy, Precision, Recall, F1, Macro-F1, ECR) are evaluated descriptively per arm-scenario pair. Deterministic repetitions must NOT be treated as independent stochastic samples for inferential hypothesis testing, ANOVA, or Student's $t$ confidence intervals.
