# NetOps Research V2 — Phase 3 Experimental Protocol (Scope Revision 2.0)

## Status: PRE-REGISTERED EXPERIMENTAL PROTOCOL (EXECUTION NOT AUTHORIZED)

> [!IMPORTANT]
> **Safety & Execution Guard**: Phase 3 HAS NOT YET BEEN AUTHORIZED FOR EXECUTION (`phase3_execution_authorized = false`).
> This protocol is a pre-registered experimental design document. No experiment matrix rows, live network operations, fault injections, or empirical data collection have been performed or authorized by this document.

---

## 1. Scope Revision & Research Objectives

The Phase 3 experimental design has been formally narrowed to evaluate three primary comparison arms (**ARM_3**, **ARM_4**, and **ARM_5**) across four verified research scenarios (**CASE_01**, **CASE_02**, **CASE_03**, and **CASE_04**).

### Primary Research Questions & Hypotheses

- **RQ1 (Diagnostic Accuracy & Effectiveness)**: How does CADE candidate scoring without LLM escalation (Arm 5) compare to un-escalated rule engines (Arm 3) and the frozen Phase 2 baseline engine (Arm 4) in overall diagnostic accuracy, precision, recall, and Macro-F1?
  - *Hypothesis $H_{1a}$*: Arm 5 achieves higher Macro-F1 than Arm 3 and Arm 4 on multi-layer scenarios (`CASE_02`, `CASE_03`, `CASE_04`) by integrating multi-metric context.
- **RQ2 (Diagnostic Observation Latency)**: What is the wall-clock execution latency $T_{\text{mttd}} = t_{\text{diagnosis}} - t_{\text{observe}}$ measured from telemetry input ingestion to diagnosis emission across Arms 3–5?
  - *Hypothesis $H_{2a}$*: Arm 3 and Arm 4 exhibit lower mean observation latency than Arm 5 due to direct pattern matching without candidate graph evaluation.
- **RQ3 (Ground-Truth Isolation Integrity)**: Does the candidate evaluation pipeline maintain zero ground-truth leakage when scenario labels and evaluation targets are strictly isolated from operational input streams?
  - *Hypothesis $H_{3a}$*: Input telemetry snapshots across Arms 3–5 contain zero references to scenario metadata or ground-truth fault definitions.
- **RQ4 (Incremental Diagnostic Value of Candidate Scoring)**: What is the net incremental diagnostic value provided by CADE candidate scoring over traditional rule-engine heuristics prior to LLM escalation?
  - *Hypothesis $H_{4a}$*: CADE candidate scoring improves evidence compression ratio (ECR) while preserving diagnostic accuracy relative to baseline rule matching.
- **RQ6 (Repeated-Run Variance & Seed Reproducibility)**: What is the execution variance across independent repetitions under fixed deterministic seed assignments?

### Excluded Scope & Non-Primary Extensions

- **Arm 2 (Rolling Statistical Detector)**: Kept as a possible future extension using a rolling-window z-score detector; excluded from the primary Phase 3 matrix.
- **Arm 6 (CESO + CADE + Ollama LLM)**: Excluded from primary comparison (requires Ollama service infrastructure).
- **Arm 7 (Closed-Loop NetOps Remediation)**: Deferred to a separate development track for real Linux namespace remediation and independent verification; not included or executed in this primary design.
- **Remediation & Recovery Metrics (RQ5, RSR, Recovery Latency)**: Excluded from primary evaluation as Arms 3–5 do not execute remediation actions.

---

## 2. Pre-Registered Primary Comparison Arms (3 Arms)

The primary experiment matrix consists of exactly 3 arms:

| Arm ID | Arm Name | Diagnostic Algorithm | Telemetry Input Pipeline | LLM Escalation | Remediation Loop | Execution Status |
|---|---|---|---|---|---|---|
| **ARM_3_RULE_BASED** | Rule-Based Diagnosis | Standard rule matching engine | CESO `NetworkState` snapshot | None | None | `PLANNED_NOT_EXECUTED` |
| **ARM_4_PHASE2_BASELINE** | Phase 2 Frozen Baseline | `ExplainableRuleEngine` v2.0.0-phase2 | CESO `NetworkState` snapshot | None | None | `PLANNED_NOT_EXECUTED` |
| **ARM_5_CESO_CADE_NO_LLM** | CESO + CADE (No LLM) | CADE Candidate Scoring $S(c)$ | CESO `NetworkState` snapshot | None | None | `PLANNED_NOT_EXECUTED` |

### Detailed Algorithm & Treatment Descriptions

1. **ARM_3_RULE_BASED**:
   - *Treatment*: Standard rule-matching logic applied directly to raw interface, link, and route metrics. Evaluates single-metric thresholds (e.g. loss $> 15\%$, RTT $> 100\text{ms}$, MTU mismatch) without multi-variable candidate scoring or topology graph traversal.
   - *Input*: Identical CESO `NetworkState` snapshot.
   - *Output*: Diagnostic label and matched rule string.

2. **ARM_4_PHASE2_BASELINE**:
   - *Treatment*: Preserved `ExplainableRuleEngine` v2.0.0-phase2 implementation. Applies Phase 2 heuristic decision tree and evidence extraction logic.
   - *Input*: Identical CESO `NetworkState` snapshot.
   - *Output*: Diagnostic label, confidence score, and selected evidence list.

3. **ARM_5_CESO_CADE_NO_LLM**:
   - *Treatment*: Context-Aware Diagnosis Engine (CADE) candidate scoring algorithm $S(c) = w_{\text{topo}} \cdot S_{\text{topo}} + w_{\text{telemetry}} \cdot S_{\text{telemetry}} + w_{\text{history}} \cdot S_{\text{history}}$. Evaluates candidate fault graphs over extracted CESO state snapshots without secondary LLM invocation.
   - *Input*: Identical CESO `NetworkState` snapshot.
   - *Output*: Diagnosed fault candidate, CADE confidence score $S(c)$, and compressed evidence set.

---

## 3. Retained Scenario Registry & Semantic Audit (4 Scenarios)

Only scenarios with verified definitions, valid ground-truth labels, and functional telemetry generators are retained:

| Matrix Scenario ID | Scenario Name | Topology Domain | Fault Condition & Target Element | Telemetry Evidence Type | Ground-Truth Storage | Diagnosis Supported? | Remediation Applicable? | Disposition |
|---|---|---|---|---|---|---|---|---|
| **CASE_01** | Enterprise Campus + Core | 20-Node Hierarchical Campus | OSPF adjacency flap (`core-rtr01<->core-rtr02`) | Synthetic Simulated Snapshot | `CASE_01` `ScenarioDefinition` | Yes | `NOT_APPLICABLE` | `RETAIN` |
| **CASE_02** | Multi-Site WAN / SD-WAN | 28-Node Multi-Site WAN | WAN path degradation & congestion (`isp-prim-rtr1<->dc-gw01`) | Synthetic Simulated Snapshot | `CASE_02` `ScenarioDefinition` | Yes | `NOT_APPLICABLE` | `RETAIN` |
| **CASE_03** | Leaf-Spine Data Center | 36-Node Leaf-Spine Fabric | Fabric MTU fragmentation cascade (`spine-01<->leaf-03`) | Synthetic Simulated Snapshot | `CASE_03` `ScenarioDefinition` | Yes | `NOT_APPLICABLE` | `RETAIN` |
| **CASE_04** | Hybrid Edge / DC / Cloud | 48-Node Hybrid Overlay | Composite cross-layer anomaly (`edge-gw-01 + wan-rtr-01 + cloud-gw-01`) | Static Dataset Evidence (`dataset_only = True`) | `CASE_04` `ScenarioDefinition` | Yes | `NOT_APPLICABLE` | `RETAIN` |

### Excluded Scenarios & Rationale

- **`SCN_005` (Composite Anomaly)**: Excluded from primary matrix. Not present in `backend/app/scenarios/` registry; `CASE_04` provides the validated composite anomaly definition.
- **`SCN_006` (Baseline Healthy State)**: Excluded from primary matrix. Not present as a registered scenario definition in `backend/app/scenarios/`.

---

## 4. Proposed Matrix Design & Seed Formula (120 Runs)

### Deterministic Effective Seed Formula

To guarantee mathematical reproducibility across repeated execution runs while maintaining run independence, every planned run uses a deterministic effective seed calculated as:

$$\text{effective\_seed}(a, s, r) = 42 + 1000 \cdot a + 100 \cdot s + r$$

where:
- Base Seed $= 42$
- Arm Index $a \in \{3, 4, 5\}$
- Scenario Index $s \in \{1, 2, 3, 4\}$ (mapped from `CASE_01`..`CASE_04`)
- Repetition Index $r \in \{1..10\}$

### Primary Execution Matrix Size

$$\text{Total Planned Runs} = 3 \text{ Arms} \times 4 \text{ Scenarios} \times 10 \text{ Repetitions} = 120 \text{ Runs}$$

All 120 planned rows are recorded in `scratch/research_v2/phase3/experiment_matrix_v2.csv` with status `PLANNED_NOT_EXECUTED`.

### Repetition Policy Notice

The choice of $N=10$ repetitions per arm-scenario pair is a **proposed design parameter** to measure empirical run variance. It is **not** presented as a proof of statistical power prior to empirical data collection. Following authorized execution, sample variance $s^2$ will be evaluated to verify sample size adequacy.

---

## 5. Experimental Controls & Fault Equivalence

1. **Input Identicality Across Arms**: For any given scenario $s$ and repetition $r$, Arms 3, 4, and 5 receive identical `NetworkState` telemetry snapshots generated with the exact same fault parameters and seed assignment.
2. **Initial State & Severity Matching**: All arms evaluate the exact same initial network state snapshot, observation window, and telemetry attribute availability.
3. **Ground-Truth Isolation**: Scenario ground-truth labels (`fault_definition`, target location) are stored in `ScenarioDefinition` objects and evaluation records, and are strictly withheld from diagnostic algorithm inputs (`ARM_3`, `ARM_4`, `ARM_5`).

---

## 6. Statistical Analysis & Limitations

### Analysis Plan

- Primary metrics (Accuracy, Precision, Recall, F1, Macro-F1, ECR, MTTD) will be reported per arm as sample mean $\bar{x} \pm 95\%\text{ CI}$.
- 95% Confidence Intervals calculated via Student's $t$-distribution ($t_{0.025, 9} = 2.262$ for $N=10$).

### Methodological Scope & Causal Inferencing Limitations

- **What the Arms 3–5 Comparison CAN Establish**:
  - The relative diagnostic accuracy and evidence compression of CADE candidate scoring vs. rule-engine baselines on identical telemetry inputs.
  - The computational observation latency difference between candidate graph evaluation and static rule matching.
- **What the Arms 3–5 Comparison CANNOT Establish**:
  - Does **NOT** isolate the causal contribution of LLM reasoning (Arm 6 excluded).
  - Does **NOT** evaluate closed-loop remediation safety, recovery latency, or verification success (Arm 7 deferred).
  - Does **NOT** prove real-time live network dynamic response (evaluated on synthetic snapshots and static dataset evidence).

---

## 7. Provenance & Phase 2 Freeze Disclosure

> [!WARNING]
> **Phase 2 Code Preserved via Parity, Not Hash**: Method-level and integration unit tests confirm functional parity for the Phase 2 baseline engine (`ExplainableRuleEngine` v2.0.0-phase2). However, the source file hash does not match the original freeze manifest hash byte-for-byte. Method-level tests prove functional output preservation, not binary file identity.

---

## 8. Authorization Pre-Condition

Execution of the 120-run primary matrix remains strictly blocked until:
1. Independent peer review of this revised protocol and matrix.
2. Formal toggle of `phase3_execution_authorized` from `false` to `true`.
