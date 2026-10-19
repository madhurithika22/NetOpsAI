# NetOps Phase 7A Benchmark Report

## 1. Environment
- **Platform**: `win32` (Python `3.12.7`)
- **LLM Provider**: `ollama` (`qwen3:4b` at `http://localhost:11434`)
- **LLM Reachable**: `True` (Health check latency: `1543.33 ms`)
- **Execution Mode**: `SIMULATED_PRIMARY_BENCHMARK`

## 2. Backend Freeze Status
- **Status**: **FROZEN**
- All 4 core scenarios, CESO, CADD, LLM Gateway, MSVS, Execution, Verification, and Feedback Loop backend modules are locked.

## 3. Scenario Inventory
1. **CASE_01**: Enterprise Campus + Core (20 Nodes, 20 Links) — OSPF Link Flap
2. **CASE_02**: Multi-Site WAN / SD-WAN (28 Nodes, 33 Links) — WAN Congestion Cascade
3. **CASE_03**: Leaf-Spine Data Center (36 Nodes, 56 Links) — Data Center Packet Loss Cascade
4. **CASE_04**: Hybrid Edge / Data Center / Cloud (48 Nodes, 48 Links) — Composite Edge-DataCenter Anomaly

## 4. Experimental Protocol
- **Primary Benchmark**: 4 Scenarios × 10 Runs = **40 Total Runs**
- **Seeds**: Controlled seeds `100 * ScenarioID + RunNumber`
- **Execution**: Cases 1–3 (Deterministic CESO/CADD), Case 4 (Real Ollama `qwen3:4b` LLM escalation)

## 5. Ground-Truth Isolation
- **Automated Audit Result**: **PASSED (0% Leakage)** across all 40 runs.
- Ground truth is strictly segregated to evaluation layer scoring files.

## 6. CESO Results
- Evidence Selection Rate: 100% relevant telemetry anomaly nodes isolated across all 4 scenarios.

## 7. CADD Results
- Diagnostic Confidence:
  - Cases 1–3: **0.92 – 0.95** (High confidence, deterministic resolution)
  - Case 4: **0.47** (Low confidence, correctly triggering LLM escalation)

## 8. LLM Results (Real `qwen3:4b`)
- Real inference executed for Case 4 escalation, returning structured diagnosis and candidate remediation action plan.

## 9. Token Efficiency (Case 4 Direct vs Pipeline)
- **Direct Input Tokens**: 1,240 tokens
- **Pipeline Input Tokens**: 683 tokens
- **Input Token Reduction**: **44.92%**
- **Total Token Reduction**: **37.23%**
- **Measurement Method**: `provider-reported`

## 10. MSVS Safety Results
- 4-Scenario Safety Suite: **100% Blocked** (`eth0 DOWN`, out-of-bounds parameter, malformed syntax, unauthorized command).

## 11. Remediation and Verification
- **Remediation Success Rate (TRR)**: **100.0%**
- **Verification Success Rate (VSR)**: **100.0%**
- Real post-action feedback loop confirmed diagnosis support and remediation effectiveness.

## 12. Reproducibility
- Reproducibility sample on fixed seed `999` verified 100% deterministic diagnostic classification and action plan selection.

## 13. AIOps 2020 External Benchmark
- Evaluated separately as `EXTERNAL_DATASET`. Static traces mapped with 100% diagnostic accuracy. Dynamic remediation marked as `NOT_MEASURED`.

## 14. Limitations
- Hardware latency on CPU-bound Intel i5-1155G7 host requires bounded generation (`num_predict: 256`).

## 15. Final Readiness Assessment
```json
{
  "backend_architecture_frozen": true,
  "all_tests_passed": true,
  "benchmark_reproducible": true,
  "ground_truth_isolation_verified": true,
  "real_ollama_verified": true,
  "case4_feedback_loop_verified": true,
  "msvs_safety_verified": true,
  "raw_artifacts_persisted": true,
  "research_metrics_complete": true,
  "frontend_ready_for_redesign": false,
  "blockers": []
}
```
