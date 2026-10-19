# NetOps Research V2 — Phase 2 Final Consistency Audit

## Role & Executive Summary
This document records the strict research-software audit, network measurement engineering review, and mathematical reproducibility verification of NetOps V2 Phase 2.

- **Phase 2 Audit Status**: **PASS**
- **Phase 3 Authorization Status**: **NOT AUTHORIZED** (Phase 3 remains un-authorized per prompt directives until audit review).

---

## 1. Environment Verification

Command executed in Ubuntu WSL2:
```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/d/NetOpsAI && source .venv-linux/bin/activate && python -c 'import sys; print(sys.platform, sys.executable)'"
```
Output:
```text
linux /mnt/d/NetOpsAI/.venv-linux/bin/python
```
**Environment Status**: **VERIFIED** (Linux platform and interpreter under `/mnt/d/NetOpsAI/.venv-linux/`).

---

## 2. Inspected Files & Source Paths

1. [`backend/app/cadd/engine.py`](file:///d:/NetOpsAI/backend/app/cadd/engine.py): CADE diagnosis rule engine implementation (`VERSION = "2.0.0-phase2"`).
2. [`backend/app/research_v2/testbed/telemetry.py`](file:///d:/NetOpsAI/backend/app/research_v2/testbed/telemetry.py): Real telemetry collector & ICMP ping parser (`parse_ping_output`).
3. [`scratch/run_phase2_experiment.py`](file:///d:/NetOpsAI/scratch/run_phase2_experiment.py): Phase 2 real testbed experiment runner.
4. [`scratch/research_v2/phase2/algorithm_spec.md`](file:///d:/NetOpsAI/scratch/research_v2/phase2/algorithm_spec.md): CADE algorithm specification.
5. [`scratch/research_v2/phase2/runs/exp-phase2-5c538333.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/runs/exp-phase2-5c538333.json): Newly persisted immutable experiment record ($N=30/50$, detailed `tc -s qdisc` counters, remediation & verification).
6. [`scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json): Historical experiment record ($N=5$, preserved untouched).
7. [`tests/unit/test_phase2_formula_and_isolation.py`](file:///d:/NetOpsAI/tests/unit/test_phase2_formula_and_isolation.py): Unit tests for formula precision, tie-breaking, non-interference, and discrepancy regression.
8. [`scratch/research_v2/phase2/correction_report.md`](file:///d:/NetOpsAI/scratch/research_v2/phase2/correction_report.md): Phase 2 correction report.

---

## 3. Exact Formulas Found in Implementation & Specification

### Feature Normalization ($\psi(x)$)
$$\psi(x) = \max(0.0, \min(1.0, \text{safe\_float}(x)))$$

### Feature Extractions
- **Latency Score** ($f_{\text{lat}}$):
  $$f_{\text{lat}} = \max_{l \in L} \psi\left(\frac{l.\text{rtt\_ms} - 50.0}{50.0}\right)$$
- **Packet Loss Score** ($f_{\text{loss}}$):
  $$f_{\text{loss}} = \max_{l \in L} \psi\left(\frac{l.\text{packet\_loss\_pct} - 10.0}{30.0}\right)$$

### Candidate Score Equations ($S(c)$)
- **`HIGH_LATENCY_CONGESTION`**:
  $$S(\text{HIGH\_LATENCY\_CONGESTION}) = \begin{cases} \text{round}(0.7 \cdot f_{\text{lat}} + 0.3 \cdot f_{\text{loss}}, 4) & \text{if } |\text{down\_ifaces}| = 0 \land f_{\text{lat}} > f_{\text{loss}} \land f_{\text{lat}} > 0 \\ 0.0 & \text{otherwise} \end{cases}$$
- **`PACKET_LOSS`**:
  $$S(\text{PACKET\_LOSS}) = \begin{cases} \text{round}(0.8 \cdot f_{\text{loss}} + 0.2 \cdot f_{\text{lat}}, 4) & \text{if } |\text{down\_ifaces}| = 0 \land f_{\text{loss}} \ge f_{\text{lat}} \land f_{\text{loss}} > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

### Heuristic Confidence Score ($C$)
$$C = \begin{cases} 1.0 & \text{if } c^* = \text{HEALTHY} \land S(\text{HEALTHY}) = 1.0 \\ \text{round}\left(S(c^*) \cdot (1.0 - 0.5 \cdot S(c^{(2)})), 4\right) & \text{otherwise} \end{cases}$$

### Escalation Decision
$$\text{escalation\_required} = (C < 0.70) \lor (c^* = \text{UNKNOWN\_COMPOSITE\_ANOMALY})$$

---

## 4. Audit A — Independent Recomputation & Intermediate Arithmetic

### 4.1 Recorded Inputs in `exp-phase2-5c538333.json`
- **Degraded Snapshot Latency Probe** ($N=50$): RTT = $150.326\text{ms}$, Packets Tx = 50, Packets Rx = 41, Packets Lost = 9, Loss Pct = $18.0\%$

### 4.2 Intermediate Arithmetic
1. **$f_{\text{lat}}$ calculation**:
   $$\frac{150.326 - 50.0}{50.0} = \frac{100.326}{50.0} = 2.00652 \implies f_{\text{lat}} = \psi(2.00652) = 1.0000$$
2. **$f_{\text{loss}}$ calculation**:
   $$\frac{18.0 - 10.0}{30.0} = \frac{8.0}{30.0} = 0.266666666... \implies f_{\text{loss}} = \psi(0.2666667) = 0.2666667$$
3. **Candidate Score $S(\text{HIGH\_LATENCY\_CONGESTION})$**:
   $$S = 0.7 \cdot (1.0000) + 0.3 \cdot (0.2666667) = 0.7000 + 0.08000 = 0.78000 \implies \text{round}(0.78000, 4) = 0.7800$$
4. **Second-Highest Score $S^{(2)}$**:
   - $S(\text{PACKET\_LOSS}) = 0.0$ (since $f_{\text{loss}} < f_{\text{lat}}$)
   - All other candidates = $0.0$
   - $S^{(2)} = 0.0000$
5. **Confidence Score $C$**:
   $$C = \text{round}(0.7800 \cdot (1.0 - 0.5 \times 0.0), 4) = 0.7800$$
6. **Escalation Flag**:
   $$\text{escalation\_required} = (0.7800 < 0.70) \lor \text{False} = \text{False}$$

### 4.3 Audit Comparison Table

| Quantity | Specification | Implementation | Persisted Record (`exp-phase2-5c538333.json`) | Independent Recalculation | Status |
|---|---|---|---|---|---|
| `f_lat` | $1.0000$ | `1.0` | $1.0$ (derived) | $1.0000$ | **AGREE** |
| `f_loss` | $0.2667$ | `0.2667` | $0.2667$ (derived from 18.0%) | $0.2667$ | **AGREE** |
| `S(HIGH_LATENCY_CONGESTION)` | $0.7800$ | `0.78` | `0.78` | $0.7800$ | **AGREE** |
| Second Highest Candidate ($S^{(2)}$) | $0.0000$ | `0.0` | `0.0` | $0.0000$ | **AGREE** |
| Confidence Score ($C$) | $0.7800$ | `0.78` | `0.78` | $0.7800$ | **AGREE** |
| Escalation Required | `False` | `False` | `false` | `False` | **AGREE** |
| Algorithm Version | `2.0.0-phase2` | `2.0.0-phase2` | `2.0.0-phase2` | `2.0.0-phase2` | **AGREE** |

---

## 5. Audit B — Packet-Loss Numerator, Denominator, and Source Analysis

| State / Record | Source | Sent ($N$) | Received | Lost | Exact Formula | Reported % | Rounding | Direction & Namespace | Qdisc Observed |
|---|---|---|---|---|---|---|---|---|---|
| **Baseline** (`exp-phase2-5c538333.json`) | ICMP ping stdout | 30 | 30 | 0 | $\frac{30-30}{30} \times 100$ | `0.0%` | None | `rns-host-a` -> `10.0.3.10` | `noqueue 0: dev veth-r1-r2 root` |
| **Fault Verification** (`exp-phase2-5c538333.json`) | ICMP ping stdout | 30 | 22 | 8 | $\frac{30-22}{30} \times 100$ | `26.6667%` | Round to 2 decimals (`26.67%`) | `rns-host-a` -> `10.0.3.10` via `veth-r1-r2` | `netem 8001: dev veth-r1-r2 root delay 150ms loss 20%` |
| **Degraded State** (`exp-phase2-5c538333.json`) | ICMP ping stdout | 50 | 41 | 9 | $\frac{50-41}{50} \times 100$ | `18.0%` | Exact | `rns-host-a` -> `10.0.3.10` via `veth-r1-r2` | `netem 8001: dev veth-r1-r2 root delay 150ms loss 20%` |
| **Post-Recovery** (`exp-phase2-5c538333.json`) | ICMP ping stdout | 30 | 30 | 0 | $\frac{30-30}{30} \times 100$ | `0.0%` | None | `rns-host-a` -> `10.0.3.10` | `noqueue 0: dev veth-r1-r2 root` (netem absent) |

### Explanation of Probe Count Variation & Loss Percentages
- In $N=30$ probe run: 8 packets lost out of 30 $\implies \frac{8}{30} = 26.6667\% \approx 26.67\%$.
- In $N=50$ probe run: 9 packets lost out of 50 $\implies \frac{9}{50} = 18.0\%$.
- Both percentages derive directly from integer ICMP probe transmit/receive counts ($30-22=8$ and $50-41=9$). Both sample loss percentages are statistically compatible with Bernoulli random sampling under the active `netem loss 20%` qdisc.

---

## 6. Audit C — Measurement and Recovery Evidence

1. **Baseline Measurement**: Recorded in `baseline_snapshot` ($N=30$, RTT avg = 0.071 ms, loss = 0.0%).
2. **Fault Installation & Confirmation**: `tc qdisc add dev veth-r1-r2 root netem delay 150ms loss 20%` executed in `rns-router-1` (return code 0). Active `netem` qdisc confirmed.
3. **Degraded Measurements**: Collected post-fault ($N=30$, RTT = 150.325 ms, Loss = 26.67%; $N=50$, Loss = 18.0%).
4. **Operational CADE Input**: Constructed exclusively from observed `NetworkState` metrics.
5. **Prediction & Candidate Scores Persisted**: Recorded in `diagnosis_record` prior to joining evaluation labels.
6. **Remediation Command**: `tc qdisc del dev veth-r1-r2 root` executed in `rns-router-1` (return code 0).
7. **Independent Post-Remediation Probes**: fresh ICMP ping ($N=30$, RTT = 0.068 ms, loss = 0.0%).
8. **Independent Qdisc Absence Check**: `tc qdisc show dev veth-r1-r2` confirmed `qdisc noqueue 0: dev veth-r1-r2 root` (`qdisc_netem_absent: true`).
9. **Resource Cleanup**: `ResearchTopology.destroy_topology()` executed cleanly in `finally` block.

---

## 7. Audit D — Test Suite Verification

### Unit Test Execution Output
Command executed in Ubuntu WSL2:
```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/d/NetOpsAI && source .venv-linux/bin/activate && pytest -v tests/unit/test_phase2_formula_and_isolation.py tests/unit/test_phase2_guard.py"
```
Output:
```text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.1.1, pluggy-1.6.0 -- /mnt/d/NetOpsAI/.venv-linux/bin/python
cachedir: .pytest_cache
rootdir: /mnt/d/NetOpsAI
configfile: pytest.ini
plugins: anyio-4.15.1
collecting ... collected 18 items

tests/unit/test_phase2_formula_and_isolation.py::test_01_hand_calculable_exact_scores PASSED [  5%]
tests/unit/test_phase2_formula_and_isolation.py::test_02_normalization_and_weight_handling PASSED [ 11%]
tests/unit/test_phase2_formula_and_isolation.py::test_03_missing_feature_behavior PASSED [ 16%]
tests/unit/test_phase2_formula_and_isolation.py::test_04_invalid_numeric_and_non_finite_input PASSED [ 22%]
tests/unit/test_phase2_formula_and_isolation.py::test_05_zero_denominator_safety PASSED [ 27%]
tests/unit/test_phase2_formula_and_isolation.py::test_06_candidate_ties_and_deterministic_tie_breaking PASSED [ 33%]
tests/unit/test_phase2_formula_and_isolation.py::test_07_unknown_fault_handling PASSED [ 38%]
tests/unit/test_phase2_formula_and_isolation.py::test_08_confidence_changes_with_relevant_evidence PASSED [ 44%]
tests/unit/test_phase2_formula_and_isolation.py::test_09_no_change_in_prediction_when_evaluation_label_changes PASSED [ 50%]
tests/unit/test_phase2_formula_and_isolation.py::test_10_no_access_to_expected_diagnoses_in_operational_pipeline PASSED [ 55%]
tests/unit/test_phase2_formula_and_isolation.py::test_11_no_hardcoded_confidence_or_label_derived_paths PASSED [ 61%]
tests/unit/test_phase2_formula_and_isolation.py::test_12_deterministic_repeated_execution PASSED [ 66%]
tests/unit/test_phase2_formula_and_isolation.py::test_13_escalation_threshold_boundary_behavior PASSED [ 72%]
tests/unit/test_phase2_formula_and_isolation.py::test_14_independent_score_recomputation_discrepancy PASSED [ 77%]
tests/unit/test_phase2_guard.py::test_phase2_validator_linux_check PASSED [ 83%]
tests/unit/test_phase2_guard.py::test_phase2_validator_unit_test_rejection PASSED [ 88%]
tests/unit/test_phase2_guard.py::test_phase2_validator_ground_truth_leakage_rejection PASSED [ 94%]
tests/unit/test_phase2_guard.py::test_phase2_validator_missing_raw_evidence_rejection PASSED [100%]

============================== 18 passed in 0.90s ==============================
```

---

## 8. Historical Experiment Record Provenance & Immutable Records

1. **Historical Record**: [`scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json) (Preserved untouched as historical evidence).
2. **Corrected Record**: [`scratch/research_v2/phase2/runs/exp-phase2-5c538333.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/runs/exp-phase2-5c538333.json) (New immutable record).

---

## 9. Final Decision & Authorization Status

- **Phase 2 Final Consistency Audit Decision**: **PASS**
- **Phase 3 Authorization**: **NOT AUTHORIZED** (Phase 3 remains un-authorized per prompt directives until audit review).
