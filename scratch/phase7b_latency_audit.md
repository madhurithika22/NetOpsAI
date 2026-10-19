# Latency Semantics Audit

**Objective**: Explicitly audit and segregate pipeline timing metrics from network physical transport metrics.

---

## 1. Latency Metric Definitions & Disaggregation

| Latency Category | Symbol | Description | Measured Range / Value |
| :--- | :--- | :--- | :--- |
| **Network Baseline RTT** | $RTT_{net}$ | Physical baseline network transport round-trip time | Case 1: 2.1ms | Case 2: 145ms | Case 3: 320ms | Case 4: 85ms |
| **Mean Time to Detect** | $MTTD$ | CESO/CADD evidence extraction & rule evaluation time | **0.10 ms – 0.75 ms** (Mean: **0.24 ms**) |
| **Deterministic Pipeline Latency** | $T_{det}$ | End-to-end execution for Cases 1–3 (No LLM escalation) | **0.74 ms – 1.77 ms** (Mean: **0.85 ms**) |
| **LLM Inference Latency** | $T_{llm}$ | Real Ollama `qwen3:4b` inference latency on CPU | **103.8 s – 141.2 s** (Mean: **109.0 s**) |
| **End-to-End Hybrid Latency** | $T_{e2e}$ | Total execution time for Case 4 (Rule + LLM + MSVS + Verif) | **103.8 s – 141.2 s** (Mean: **109.0 s**) |

---

## 2. Latency Verification Rules
- **Rule 1**: $MTTD$ is computed strictly from rule evaluation timestamps and does NOT include $RTT_{net}$.
- **Rule 2**: Deterministic pipeline latencies (Cases 1–3) and LLM-escalated latencies (Case 4) are presented separately and NOT combined into a misleading single average.
