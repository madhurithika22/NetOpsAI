# Phase 2 Audit — CADE Diagnosis Engine, Telemetry, and Ground-Truth Isolation

## 1. Current Diagnosis Algorithm and Source Locations

The current diagnosis logic is implemented in `ExplainableRuleEngine` ([`backend/app/cadd/engine.py:L7-L421`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L7-L421)). It evaluates a `NetworkState` snapshot through an if-else decision chain:

1. **Case 01 Rule ([`backend/app/cadd/engine.py:L29-L74`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L29-L74))**: Checks `state.topology_id == "CASE_01"`. If true and interface `core-rtr01-eth2` is present, emits `fault_type="OSPF_ADJACENCY_INSTABILITY"` with `confidence_score=0.95`.
2. **Case 02 Rule ([`backend/app/cadd/engine.py:L77-L122`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L77-L122))**: Checks `state.topology_id == "CASE_02"`. If true and interface `dc-gw02-wan1` is present, emits `fault_type="WAN_PATH_DEGRADATION_AND_CONGESTION"` with `confidence_score=0.94`.
3. **Case 03 Rule ([`backend/app/cadd/engine.py:L125-L168`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L125-L168))**: Checks `state.topology_id == "CASE_03"`. If true and interface `spine-01-eth3` is present, emits `fault_type="MTU_MISMATCH_FRAGMENTATION_CASCADE"` with `confidence_score=0.96`.
4. **Case 04 Rule ([`backend/app/cadd/engine.py:L171-L220`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L171-L220))**: Checks `state.topology_id == "CASE_04"`. If true, emits `fault_type="UNKNOWN_COMPOSITE_ANOMALY"` with `confidence_score=0.47` and sets `escalation_required=True`.
5. **Generic Link/Interface Rules ([`backend/app/cadd/engine.py:L223-L398`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L223-L398))**:
   - `INTERFACE_FAILURE`: If any interface has `is_up == False`, emits `confidence_score=1.0`.
   - `ROUTING_MISCONFIGURATION`: If route metric >= 999 or points to wrong interface, emits `confidence_score=0.98`.
   - `HIGH_LATENCY_CONGESTION`: If link RTT > 50ms, emits `confidence_score=0.95`.
   - `PACKET_LOSS`: If link loss > 10%, emits `confidence_score=0.92`.
6. **Healthy Baseline ([`backend/app/cadd/engine.py:L401-L421`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L401-L421))**: Emits `fault_type="HEALTHY"` with `confidence_score=1.0`.

---

## 2. Implemented Confidence / Score Formulas

There are currently **zero** mathematical formulas implemented for confidence or candidate scoring in `ExplainableRuleEngine`:

- All confidence scores (`0.95`, `0.94`, `0.96`, `0.47`, `1.0`, `0.98`, `0.92`) are static literals assigned directly in Python code ([`backend/app/cadd/engine.py:L48,L96,L144,L188,L243,L283,L329,L375,L408`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L48)).
- No evidence weighting, metric normalization, probability calculation, or quantitative candidate comparison is performed.

---

## 3. Input and Output Schemas for Each Stage

### Stage 1: Telemetry Collection (CESO)
- **Input**: Raw Linux `/proc`/iproute2/ping commands or simulated scenario state ([`backend/app/ceso/provider.py:L188-L269`](file:///d:/NetOpsAI/backend/app/ceso/provider.py#L188-L269)).
- **Output**: `NetworkState` ([`backend/app/models/ceso_models.py:L38-L46`](file:///d:/NetOpsAI/backend/app/models/ceso_models.py#L38-L46)) containing `interfaces: Dict[str, InterfaceState]`, `links: List[LinkLatency]`, `routes: List[RouteEntry]`, `nodes: Dict[str, NodeMetrics]`, `topology_id: str`, `anomalies_detected: bool`.

### Stage 2: Diagnostic Engine (CADE)
- **Input**: `NetworkState` object.
- **Output**: `Tuple[DiagnosticReport, ActionPlan]` ([`backend/app/models/cadd_models.py:L12-L38`](file:///d:/NetOpsAI/backend/app/models/cadd_models.py#L12-L38)) containing `fault_type`, `impacted_elements`, `severity`, `confidence_score`, `evidence_chain`, `escalation_required`, and proposed remediation actions.

### Stage 3: LLM Escalation & Evaluation
- **Input**: `LLMContextPackage` constructed in `BenchmarkRunner` ([`backend/app/evaluation/runner.py:L102-L120`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L102-L120)).
- **Output**: `LLMDiagnosisResponse` ([`backend/app/llm/gateway.py:L88-L123`](file:///d:/NetOpsAI/backend/app/llm/gateway.py#L88-L123)) and `ExperimentRun` ([`backend/app/evaluation/models.py`](file:///d:/NetOpsAI/backend/app/evaluation/models.py)).

---

## 4. Suspected Ground-Truth Leakage Paths

The audit identified four distinct ground-truth leakage paths:

1. **Topology/Scenario Identifier Branching**: `ExplainableRuleEngine.diagnose_state` checks `state.topology_id` against scenario names (`CASE_01`, `CASE_02`, `CASE_03`, `CASE_04`) ([`backend/app/cadd/engine.py:L29,L77,L125,L171`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L29)). The scenario name directly dictates the returned diagnosis and hardcoded confidence.
2. **Evaluation Ground-Truth Contamination in LLM Context**: `BenchmarkRunner._run_single_scenario_benchmark` passes scenario description `sc_def.fault_definition.description`, `sc_def.expected_fault_domain`, and `sc_def.remediation_candidates` into `LLMContextPackage` ([`backend/app/evaluation/runner.py:L113-L118`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L113-L118)).
3. **Pre-Evaluation Label Merging**: `BenchmarkRunner` reads `sc_def.fault_definition.fault_type` before passing state to CADE and stores ground-truth label alongside prediction without enforcing snapshot immutability before prediction emission ([`backend/app/evaluation/runner.py:L76-L89`](file:///d:/NetOpsAI/backend/app/evaluation/runner.py#L76-L89)).
4. **Hardcoded Low Confidence Triggering Escalation**: Case 4 has a hardcoded `confidence_score = 0.47` ([`backend/app/cadd/engine.py:L188`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L188)) specifically to force `escalation_required = True`.

---

## 5. Existing Thresholds and Selection Method

- `LATENCY_THRESHOLD_MS = 50.0`: Hardcoded constant ([`backend/app/cadd/engine.py:L13`](file:///d:/NetOpsAI/backend/app/cadd/engine.py:L13)).
- `PACKET_LOSS_THRESHOLD_PCT = 10.0`: Hardcoded constant ([`backend/app/cadd/engine.py:L14`](file:///d:/NetOpsAI/backend/app/cadd/engine.py:L14)).
- `CONFIDENCE_ESCALATION_THRESHOLD = 0.70`: Hardcoded constant ([`backend/app/cadd/engine.py:L15`](file:///d:/NetOpsAI/backend/app/cadd/engine.py:L15)).

*Selection Method*: These thresholds were ad-hoc heuristics selected without empirical calibration or statistical specifications.

---

## 6. Existing Tests and Actual Telemetry Available for Validation

### Existing Tests
- `tests/unit/test_cadd.py`: Tests basic `diagnose_state` with simulated states.
- `tests/unit/test_ceso.py`: Tests simulated and Linux provider state extraction.
- `tests/unit/test_evaluation_metrics.py`: Tests metric computation.
- `tests/unit/test_research_v2_capabilities.py`: Tests testbed environment checks.
- `tests/unit/test_research_v2_guard.py`: Tests research context guard.
- `tests/unit/test_research_v2_executor.py`: Tests `ControlledExecutor` namespace command execution.
- `tests/phase1/test_privileged_execution.py`: Tests privileged execution in WSL2.

### Actual Telemetry Available
- Phase 1 raw JSON experiment records in [`scratch/research_v2/phase1/runs/`](file:///d:/NetOpsAI/scratch/research_v2/phase1/runs/).
  - `exp-phase1-e270f859.json`: Contains real Linux testbed `ping`, `ip link`, `ip route`, `tc qdisc` execution logs and RTT/loss telemetry during `HIGH_LATENCY_CONGESTION` fault injection.

---

## 7. Proposed Code Changes and Reasons

1. **Refactor `ExplainableRuleEngine` into a Reproducible Mathematical Candidate-Scoring Engine**:
   - *Reason*: Remove all hardcoded confidence values (`0.95`, `0.47`, etc.) and `topology_id` checks. Compute scores and confidence dynamically from observed metric evidence.
2. **Define Formal Mathematical Telemetry Feature Extraction and Normalization**:
   - *Reason*: Provide deterministic, non-linear normalization functions ($S_{lat}$, $S_{loss}$, $S_{link\_down}$, $S_{route\_err}$, $S_{mtu}$) bounded in $[0, 1]$.
3. **Implement Weighted Multi-Attribute Score Aggregation**:
   - *Reason*: Calculate explicit evidence scores for candidate fault hypotheses (`INTERFACE_FAILURE`, `HIGH_LATENCY_CONGESTION`, `PACKET_LOSS`, `ROUTING_MISCONFIGURATION`, `DC_MTU_MISMATCH`, `WAN_PATH_DEGRADATION`, `OSPF_ADJACENCY_FLAP`, `UNKNOWN_COMPOSITE_ANOMALY`).
4. **Implement Principled Confidence & Escalation Function**:
   - *Reason*: Compute confidence as $C = S_{top} \cdot (1 - S_{second\_top})$ or margin-based score. Compare against `CONFIDENCE_ESCALATION_THRESHOLD` to determine escalation dynamically.
5. **Enforce Strict Operational Inputs (Remove Ground-Truth Leakage)**:
   - *Reason*: Strip `topology_id` scenario matching from CADE. Ensure CADE sees only runtime-observable telemetry.
6. **Update `BenchmarkRunner` & LLM Context Packaging**:
   - *Reason*: Ensure operational diagnosis is emitted and recorded *before* evaluation layer attaches ground-truth labels.
7. **Add Research Result Validator Guard (Phase 2)**:
   - *Reason*: Reject research records that leak ground truth, contain hardcoded confidence, or lack computed mathematical trace.
