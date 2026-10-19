# NetOps Research V2 — Read-Only Experimental Arm Comparability Audit Report

**Audit Date:** 2026-10-09  
**Audit Scope:** Source-level comparability audit of provisionally authorized Phase 3 experimental arms (`ARM_3_RULE_BASED`, `ARM_4_PHASE2_BASELINE`, `ARM_5_CESO_CADE_NO_LLM`).  
**Auditor Role:** Independent Research Software Auditor & Measurement Engineer  
**Execution Status:** Read-Only Static Code & Call-Graph Audit (No research experiments executed)

---

## 1. Executive Summary & Audit Decision

### Overall Audit Decision: `PASS — COMPARABLE FOR SPECIFIED SCOPE`

A comprehensive, source-level inspection of the NetOps repository codebase, call paths, telemetry pipelines, and diagnostic algorithms was conducted for the three provisionally authorized Phase 3 experimental arms:

1. **`ARM_3_RULE_BASED`**: Discrete rule engine evaluating boolean threshold matches without continuous candidate score weighting or second-highest candidate score margin confidence discounting.
2. **`ARM_4_PHASE2_BASELINE`**: Continuous multi-attribute candidate scoring engine $S(c)$ operating on pre-extracted static `NetworkState` snapshots with second-highest candidate score margin confidence discounting ($C = \text{round}(S(c^*)(1 - 0.5 S(c^{(2)})), 4)$).
3. **`ARM_5_CESO_CADE_NO_LLM`**: Dynamic end-to-end telemetry pipeline combining live multi-node metrics aggregation via `CESOService` with CADE continuous candidate scoring and margin confidence discounting.

### Key Conclusions:
- **Functional Distinctness**: All three pairwise arm comparisons are verified as **`MEANINGFULLY_DISTINCT`**. The arms implement fundamentally different diagnostic mechanisms, state representations, or telemetry ingestion models.
- **Ground-Truth Isolation**: All three arms achieved **`PASS`**. Telemetry processing and diagnostic candidate evaluation strictly consume operational metrics (`rtt_ms`, `packet_loss_pct`, `is_up`, `rx_errors`, `metric`, `mtu`) without accessing scenario labels, expected diagnosis strings, or benchmark evaluation metadata.
- **Fairness & Metric Support**: Observation windows, fault schedules, paired random seeds, and metric calculations (Accuracy, Precision, Recall, Macro-F1, Diagnosis Latency, Escalation Rate) are fully equivalent and supported across all three arms.
- **Phase 3 Execution Hold**: In strict accordance with audit instructions, **no Phase 3 research experiments were executed during this audit**. Standing Phase 3 authorization status (`AUTHORIZED — specified arms only`) remains unchanged, but actual execution must be initiated in a separate, dedicated research run.

---

## 2. Environment & Repository Verification

| Property | Value |
| :--- | :--- |
| **Repository Root** | `/mnt/d/NetOpsAI` |
| **Execution Platform** | `linux` (Ubuntu WSL2 on Windows) |
| **Python Interpreter** | `/mnt/d/NetOpsAI/.venv-linux/bin/python` |
| **Git Working-Tree Status (Before)** | `NOT_AVAILABLE` (Directory is not a git repository) |
| **Git Working-Tree Status (After)** | `NOT_AVAILABLE` (Directory is not a git repository) |

### Audited Source Files & Cryptographic Hashes

| Source File | SHA-256 Digest | Role / Description |
| :--- | :--- | :--- |
| `backend/app/cadd/engine.py` | `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326` | CADD explainable rule engine and continuous candidate scoring ($v2.0.0-phase2$) |
| `backend/app/ceso/service.py` | `e018695173262ecba6189b2f6c390f52a9bf3fb97ad09f4c01974ae54d335469` | CESO live telemetry aggregation service mapping raw metrics to `NetworkState` |
| `backend/app/evaluation/runner.py` | `d4ec4e43d370d979a8f51606d0e1958f43e42fa5bd80de22d7f7f2143f992c02` | Benchmark runner orchestrating scenario execution across arms |
| `scratch/run_phase2_experiment.py` | `591ab2e40484719ed0eb800204cac4cbb5b89db27a68a64e64929952934f331a` | Phase 2 reference experiment execution harness |
| `scratch/research_v2/phase3/experiment_matrix.csv` | `949817a7efb02d36d213ad6a67b6e90948de72172154b512573ff8d3cae766a9` | Phase 3 420-row experimental design matrix |

---

## 3. Detailed Per-Arm Implementation Identification

### Arm 3: `ARM_3_RULE_BASED`
- **Algorithm & Version**: Discrete Diagnostic Rule Engine (`ExplainableRuleEngine` / `DiagnosticEvidence` rule matching, v2.0.0-phase2).
- **Location**: `backend/app/cadd/engine.py` (Lines 161–230).
- **Telemetry Consumed**: `interfaces[].rtt_ms`, `interfaces[].packet_loss_pct`, `interfaces[].is_up`, `rx_errors`, `metric`, `mtu`.
- **Logic & Preprocessing**: Evaluates discrete boolean condition matching (e.g. `packet_loss_pct > 15.0`, `rtt_ms > 100.0`, `is_up == False`). Matches explicit rule patterns to return `DiagnosticEvidence` objects without candidate score weighting.
- **CESO / CADE / LLM Invocation**: CESO: `False`, CADE candidate scoring: `False`, LLM: `False`.
- **Confidence & Escalation**: Uses fixed binary/threshold rule confidence without second-highest score margin discounting.
- **Determinism**: 100% deterministic given identical `NetworkState`.

### Arm 4: `ARM_4_PHASE2_BASELINE`
- **Algorithm & Version**: Continuous Multi-Attribute Candidate Scoring Engine (CADD Engine v2.0.0-phase2).
- **Location**: `backend/app/cadd/engine.py` (Lines 231–380).
- **Telemetry Consumed**: Static pre-extracted `NetworkState` snapshot containing interface latencies, packet loss rates, interface operational states, error counters, and routing tables.
- **Logic & Preprocessing**: Computes continuous multi-attribute candidate score $S(c) \in [0, 1]$ across diagnostic candidates. Applies deterministic tie-breaking priority list (`["LINK_FLAPPING", "ROUTE_LEAK", "HARDWARE_FAULT", ...]`) and heuristic margin confidence formula:
  \[ C = \text{round}\left(S(c^*)\left(1 - 0.5 \cdot S(c^{(2)})\right), 4\right) \]
- **CESO / CADE / LLM Invocation**: CESO: `False`, CADE candidate scoring: `True`, LLM: `False`.
- **Confidence & Escalation**: Continuous confidence with second-highest candidate score margin discounting. Escalates if confidence falls below threshold.
- **Determinism**: 100% deterministic for identical static `NetworkState`.

### Arm 5: `ARM_5_CESO_CADE_NO_LLM`
- **Algorithm & Version**: Live Telemetry Aggregation (`CESOService`) + Continuous CADE Candidate Scoring (v2.0.0-phase3-auth).
- **Location**: `backend/app/ceso/service.py` (Lines 45–180) and `backend/app/cadd/engine.py`.
- **Telemetry Consumed**: Live multi-node telemetry stream (interface latencies, dynamic loss rates, route tables, node system metrics).
- **Logic & Preprocessing**: Dynamically queries and aggregates raw multi-node network telemetry via `CESOService` into `NetworkState`, then executes continuous CADE candidate scoring $S(c)$ and margin confidence discounting.
- **CESO / CADE / LLM Invocation**: CESO: `True`, CADE candidate scoring: `True`, LLM: `False`.
- **Confidence & Escalation**: Continuous margin-discounted confidence computed dynamically from live aggregated telemetry snapshot.
- **Determinism**: Fully deterministic relative to the captured telemetry snapshot.

---

## 4. Pairwise Functional-Difference Analysis

| Comparison Pair | Classification | Rationale & Source Evidence |
| :--- | :--- | :--- |
| **Arm 3 vs. Arm 4** | **`MEANINGFULLY_DISTINCT`** | Arm 3 relies exclusively on discrete boolean rule triggers (`DiagnosticEvidence`, lines 161–230), whereas Arm 4 evaluates continuous multi-attribute candidate scores $S(c)$ with second-highest score margin confidence discounting (lines 231–380). |
| **Arm 3 vs. Arm 5** | **`MEANINGFULLY_DISTINCT`** | Arm 3 evaluates discrete rules on static state without continuous candidate scoring, while Arm 5 combines live multi-node telemetry collection (`CESOService`) with continuous candidate scoring and margin discounting. |
| **Arm 4 vs. Arm 5** | **`MEANINGFULLY_DISTINCT`** | Arm 4 evaluates pre-extracted static state snapshots directly, whereas Arm 5 executes an end-to-end live telemetry ingestion pipeline (`CESOService`, `service.py:45-180`) before passing the dynamically assembled `NetworkState` to CADE. |

---

## 5. Input & Ground-Truth Isolation Audit

| Arm | Status | Data Flow Path | Line Ranges / Evidence | Finding Type |
| :--- | :---: | :--- | :--- | :--- |
| **`ARM_3_RULE_BASED`** | **`PASS`** | `NetworkState` $\rightarrow$ `ExplainableRuleEngine.diagnose_state()` $\rightarrow$ `DiagnosticEvidence` | `backend/app/cadd/engine.py` (L161–230) | `VERIFIED_ISOLATION` |
| **`ARM_4_PHASE2_BASELINE`** | **`PASS`** | `NetworkState` $\rightarrow$ `ExplainableRuleEngine.diagnose_state()` $\rightarrow$ Score $S(c)$ & Confidence $C$ | `backend/app/cadd/engine.py` (L231–380) | `VERIFIED_ISOLATION` |
| **`ARM_5_CESO_CADE_NO_LLM`** | **`PASS`** | Live Telemetry $\rightarrow$ `CESOService.get_network_state()` $\rightarrow$ `ExplainableRuleEngine.diagnose_state()` | `backend/app/ceso/service.py` (L45–180) | `VERIFIED_ISOLATION` |

### Isolation Verification Findings:
1. **No Ground-Truth Leakage**: None of the three arms inspect evaluation labels (`target_fault`, `expected_diagnosis`, `scenario_id`, `case_id`) during diagnosis.
2. **Operational Information Boundary**: Scenario identifiers and case IDs are retained strictly in benchmark logging (`runner.py`) for output aggregation and are never passed into diagnosis functions.
3. **No Hidden Escalation Leaks**: Confidence discounting strictly depends on candidate scores $S(c^*)$ and $S(c^{(2)})$, independent of ground-truth annotations.

---

## 6. Experimental Fairness & Metric Instrumentation Audit

- **Input Equivalence**: All three arms ingest telemetry corresponding to the exact same observation window and topology scenarios.
- **Repetition & Seed Control**: The 420-row Phase 3 matrix (`scratch/research_v2/phase3/experiment_matrix.csv`) specifies 10 repetitions per scenario-arm pair with paired execution seeds.
- **Metric Implementations**:
  - **Accuracy / Precision / Recall / Macro-F1**: Supported via standard categorical matching between prediction output and ground-truth label.
  - **Diagnosis Latency**: Supported via monotonic millisecond timestamp delta ($T_{\text{end}} - T_{\text{start}}$).
  - **Escalation Rate**: Supported by tracking low-confidence predictions ($C < \text{threshold}$) triggering escalation.

---

## 7. Material Issues & Recommendations

| Issue ID | Severity | Description | Recommended Action |
| :--- | :---: | :--- | :--- |
| **`ISSUE-01`** | `MINOR` | Live telemetry extraction in `ARM_5` introduces minor network polling latency compared to static state ingestion in `ARM_4`. | Record raw CADE compute latency separately from CESO network ingestion overhead in metric reports. |

---

## 8. Summary of Execution Status

- **Audit Execution**: Completed 100% read-only code and call-graph inspection.
- **Phase 3 Experiments**: **0 experiments executed**.
- **Existing Files**: **0 existing files modified or overwritten**.
- **Deliverables Produced**:
  - `scratch/research_v2/phase3/arm_comparability_audit.json`
  - `scratch/research_v2/phase3/arm_comparability_audit.md`
