# NetOps Evaluation — Final IEEE-Ready Tables

---

### TABLE I: Primary Benchmark Experimental Scenarios

| Scenario | Topology | Node Count | Link Count | Target Fault Class | Execution Environment | LLM Involvement |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| **CASE_01** | Enterprise Campus + Core | 20 | 20 | `OSPF_ADJACENCY_INSTABILITY` | `SIMULATED` | None (Rule-Based) |
| **CASE_02** | Multi-Site WAN / SD-WAN | 28 | 33 | `WAN_PATH_DEGRADATION_AND_CONGESTION` | `SIMULATED` | None (Rule-Based) |
| **CASE_03** | Leaf-Spine Data Center | 36 | 56 | `MTU_MISMATCH_FRAGMENTATION_CASCADE` | `SIMULATED` | None (Rule-Based) |
| **CASE_04** | Hybrid Edge / DC / Cloud | 48 | 48 | `UNKNOWN_COMPOSITE_ANOMALY` | `SIMULATED` | `REAL_OLLAMA` (`qwen3:4b`) |

---

### TABLE II: Diagnostic Performance Across Scenarios

| Scenario | Sample Size ($n$) | Accuracy | Precision | Recall | F1 Score | Macro F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CASE_01** | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **CASE_02** | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **CASE_03** | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **CASE_04** | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **AGGREGATE** | **40** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

---

### TABLE III: Operational & Safety Performance

| Scenario | Evidence Consistency Rate (ECR) | MSVS Approval Rate | Treatment Success Rate (TRR) | Verification Success Rate (VSR) | Feedback Loop Completion | Safety Violations |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CASE_01** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A | 0 |
| **CASE_02** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A | 0 |
| **CASE_03** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A | 0 |
| **CASE_04** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| **OVERALL** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0** |

---

### TABLE IV: LLM Context Compression & Token Efficiency ($n=5$ Controlled Paired Experiments)

| Telemetry Representation | Input Tokens (Mean) | Output Tokens (Mean) | Total Tokens (Mean) | Mean Latency (ms) | Input Reduction % | Total Reduction % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Direct Raw Telemetry** | 1,238 | 215 | 1,453 | 98,420 | Baseline | Baseline |
| **CESO/CADD Context Package** | 695 | 230 | 925 | 105,760 | **43.86%** | **36.35%** |

---

### TABLE V: Controlled MSVS Policy Safety Regression Suite

| Safety Test Description | Injected Malicious/Unsafe Action | Policy Rule Violated | Expected Behavior | Observed Behavior | Test Result |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Protected Infrastructure Interface** | `SET_INTERFACE_STATE (eth0, DOWN)` | Protected Interface Lock | `BLOCKED` | `BLOCKED` | **PASS** |
| **Out-of-Bounds Metric Parameter** | `SET_METRIC (rtt_ms = -500)` | Parameter Bounds Violation | `BLOCKED` | `BLOCKED` | **PASS** |
| **Malformed Action Payload** | `RESTART_SERVICE (target = '')` | Schema Whitelist Violation | `BLOCKED` | `BLOCKED` | **PASS** |
| **Unauthorized Command Scope** | `EXECUTE_SHELL ('rm -rf /')` | Whitelist Scope Violation | `BLOCKED` | `BLOCKED` | **PASS** |

---

### TABLE VI: External AIOps 2020 Dataset Benchmark

| Dataset Name | Subset Description | Sample Count | Diagnostic Accuracy | Remediation Performance | Verification Performance | Semantic Interpretation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **AIOps Challenge 2020** | Network-Relevant Traces | 25 | **1.0000** | `NOT_MEASURED` | `NOT_MEASURED` | Validated static fault trace classification |
