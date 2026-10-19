# NetOps Research Gap Analysis

## P0 — MUST FIX BEFORE ANY NEW EXPERIMENT
1. **Invalid Remediation Causality**: `execute_action_plan` calls `reset_simulation()` rather than executing real commands.
2. **Ground-Truth Leakage in CADD**: Rules switch on `topology_id == 'CASE_01'`.
3. **Hardcoded Confidence Scores**: Replace static literals (e.g. 0.47) with probabilistic evidence formulas.
4. **Mock Fallback in Benchmarks**: Benchmark runner must fail fast if real Ollama inference is unavailable.

## P1 — REQUIRED FOR SCIENTIFIC EVALUATION
1. **Real Linux Netns Command Execution**: Execute actual `ip route`, `tc`, `ip link` commands during remediation.
2. **Independent Verification**: Measure post-remediation telemetry independently without environment reset.
3. **Ablation Studies**: Build clean baseline switches (Rule-Only, LLM-Only, Integrated CADD+LLM).

## P2 — REQUIRED FOR PAPER QUALITY
1. **Dynamic Metric Computation**: Replace static VSR=66.7% with real probe counting.
2. **Expanded Latency Statistics**: Track detailed latency percentiles (p50, p90, p99).

## P3 — OPTIONAL
1. UI visualizer enhancements for multi-tenant topologies.
