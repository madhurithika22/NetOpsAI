# NetOps Mock / Simulation Audit

## Classifications Used:
- **A. PRODUCTION_REAL**: Production code interacting with real external state.
- **B. RESEARCH_REAL**: Authentic research measurement code.
- **C. SIMULATION_ONLY**: Synthetic state generator or simulator.
- **D. TEST_FIXTURE**: Unit/integration test asset.
- **E. MOCK_PROVIDER**: Simulated provider implementation.
- **F. HARDCODED_RESEARCH_VALUE**: Static value embedded directly in code or report.
- **G. UNKNOWN_REQUIRES_REVIEW**: Code requiring further investigation.

## Summary of Critical Findings
Found **14 mock paths**, **12 simulation paths**, and **18 hardcoded research values**.

| File | Line / Range | Symbol | Classification | Contaminates Research? | Phase 1 Action |
|---|---|---|---|---|---|
| `backend/app/ceso/provider.py` | 136-150 | `SimulatedTelemetryProvider` | SIMULATION_ONLY | YES | Replace with real linux telemetry or dataset replay |
| `backend/app/ceso/provider.py` | 210-211 | `_collect_real_linux_telemetry` | HARDCODED_RESEARCH_VALUE | YES | Read sysfs/procfs for real throughput & utilization |
| `backend/app/llm/providers/mock.py` | 1-86 | `MockLLMProvider` | MOCK_PROVIDER | YES | Isolate mock provider strictly to unit tests |
| `backend/app/msvs/service.py` | 94 | `MSVSService.execute_action_plan` | SIMULATION_ONLY | YES | Implement real command execution in netns/routers |
| `backend/app/cadd/engine.py` | 204 | Case 4 Rule | HARDCODED_RESEARCH_VALUE | YES | Replace 0.47 with dynamic evidence-weighted formula |
| `backend/app/evaluation/metrics.py` | 125 | `VSR Metric` | HARDCODED_RESEARCH_VALUE | YES | Calculate VSR dynamically from verification probes |
