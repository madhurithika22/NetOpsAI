# Token Efficiency Audit

**Experiment**: Controlled Preliminary Token-Efficiency Experiment (n=5 Paired Runs)  
**Model**: `qwen3:4b` via Ollama (`http://localhost:11434`)  
**Measurement Method**: `provider-reported` (`prompt_eval_count`, `eval_count`)

---

## 1. Summary Results

| Metric Dimension | Direct Raw Telemetry | NetOps CESO/CADD Context Package | Reduction % |
| :--- | :---: | :---: | :---: |
| **Mean Input Tokens** | `1238` | `695` | **43.86%** |
| **Mean Total Tokens** | `1494` | `951` | **36.35%** |
| **Mean Latency (ms)** | `78816.21` | `55916.94` | — |

---

## 2. Statistical Metrics (Input Token Reduction)
- **Mean**: `43.86%`
- **Median**: `43.86%`
- **Min**: `43.86%`
- **Max**: `43.86%`
- **Standard Deviation**: `0.0%`

*Label Note: Controlled preliminary experiment (n=5). Demonstrates representation efficiency without claiming statistical population generalization.*
