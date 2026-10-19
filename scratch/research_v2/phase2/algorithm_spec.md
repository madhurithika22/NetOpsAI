# Phase 2 Algorithm Specification — CADE Diagnosis & Confidence Engine

## 1. Objective & Scope

This document specifies the exact mathematical framework for CADE (Context-Aware Diagnosis Engine) in NetOps Research V2 Phase 2. CADE consumes operational telemetry extracted by CESO (`NetworkState`) and evaluates candidate fault hypotheses strictly through runtime-observable evidence without accessing ground-truth labels, scenario names, or evaluation metadata.

---

## 2. Diagnostic Candidate Set ($\mathcal{C}$) and Provenance

The candidate hypothesis set $\mathcal{C}$ covers both localized network faults and composite anomaly patterns:

1. `INTERFACE_FAILURE`: Physical or link-layer interface down / link error accumulation.
2. `ROUTING_MISCONFIGURATION`: Egress route blackhole, unroutable destination, or invalid metric cost ($\ge 999$).
3. `HIGH_LATENCY_CONGESTION`: Link RTT latency exceeding operational SLA without link down.
4. `PACKET_LOSS`: Packet loss percentage exceeding operational SLA without link down.
5. `DC_MTU_MISMATCH`: Fabric interface MTU size misalignment combined with packet drop accumulation.
6. `WAN_PATH_DEGRADATION`: Queue drops and bandwidth saturation on backup WAN circuits.
7. `OSPF_ADJACENCY_FLAP`: Interface error accumulation and metric flapping causing routing instability.
8. `UNKNOWN_COMPOSITE_ANOMALY`: Distributed multi-metric degradation across domains without a single dominating candidate.
9. `HEALTHY`: All observations operate within baseline SLA bounds.

---

## 3. Evidence Features & Exact Extraction Rules

Given a `NetworkState` snapshot $S = (I, L, R, N)$ where $I$ is interfaces, $L$ is link probes, $R$ is routes, $N$ is nodes:

### 3.1 Feature Definitions
- **Interface Down Ratio** ($f_{\text{down}}$):
  $$f_{\text{down}} = \frac{|\{i \in I \mid \neg i.\text{is\_up}\}|}{\max(1, |I|)} \in [0, 1]$$
- **Route Error Indicator** ($f_{\text{route}}$):
  $$f_{\text{route}} = \max_{r \in R} \mathbb{I}(r.\text{metric} \ge 999 \lor r.\text{interface} \text{ is invalid}) \in \{0, 1\}$$
- **Latency Score** ($f_{\text{lat}}$):
  $$f_{\text{lat}} = \max_{l \in L} \psi\left(\frac{l.\text{rtt\_ms} - 50.0}{50.0}\right) \in [0, 1]$$
  where $\psi(x) = \max(0.0, \min(1.0, x))$.
- **Packet Loss Score** ($f_{\text{loss}}$):
  $$f_{\text{loss}} = \max_{l \in L} \psi\left(\frac{l.\text{packet\_loss\_pct} - 10.0}{30.0}\right) \in [0, 1]$$
- **Interface Error Score** ($f_{\text{err}}$):
  $$f_{\text{err}} = \max_{i \in I} \psi\left(\frac{i.\text{rx\_errors}}{50.0}\right) \in [0, 1]$$
- **Utilization Score** ($f_{\text{util}}$):
  $$f_{\text{util}} = \max_{i \in I} \psi\left(\frac{i.\text{utilization\_pct} - 75.0}{20.0}\right) \in [0, 1]$$
- **MTU Drop Score** ($f_{\text{mtu}}$):
  $$f_{\text{mtu}} = \max_{i \in I} \mathbb{I}(i.\text{mtu} \neq 1500 \land i.\text{mtu} \neq 9000 \land i.\text{rx\_drops} > 100) \in \{0, 1\}$$

---

## 4. Candidate Scoring Equations ($S(c)$)

For each candidate $c \in \mathcal{C}$, score $S(c) \in [0, 1]$ is computed as follows:

1. **`INTERFACE_FAILURE`**:
   $$S(\text{INTERFACE\_FAILURE}) = f_{\text{down}}$$
2. **`ROUTING_MISCONFIGURATION`**:
   $$S(\text{ROUTING\_MISCONFIGURATION}) = f_{\text{route}}$$
3. **`DC_MTU_MISMATCH`**:
   $$S(\text{DC\_MTU\_MISMATCH}) = f_{\text{mtu}}$$
4. **`OSPF_ADJACENCY_FLAP`**:
   $$S(\text{OSPF\_ADJACENCY\_FLAP}) = \begin{cases} 0.6 \cdot f_{\text{err}} + 0.4 \cdot f_{\text{route}} & \text{if } f_{\text{err}} > 0 \land f_{\text{route}} > 0 \\ 0.0 & \text{otherwise} \end{cases}$$
5. **`WAN_PATH_DEGRADATION`**:
   $$S(\text{WAN\_PATH\_DEGRADATION}) = \begin{cases} 0.6 \cdot f_{\text{util}} + 0.4 \cdot f_{\text{loss}} & \text{if } f_{\text{util}} > 0 \\ 0.0 & \text{otherwise} \end{cases}$$
6. **`HIGH_LATENCY_CONGESTION`**:
   $$S(\text{HIGH\_LATENCY\_CONGESTION}) = \begin{cases} 0.7 \cdot f_{\text{lat}} + 0.3 \cdot f_{\text{loss}} & \text{if } f_{\text{down}} = 0 \land f_{\text{lat}} > f_{\text{loss}} \\ 0.0 & \text{otherwise} \end{cases}$$
7. **`PACKET_LOSS`**:
   $$S(\text{PACKET\_LOSS}) = \begin{cases} 0.8 \cdot f_{\text{loss}} + 0.2 \cdot f_{\text{lat}} & \text{if } f_{\text{down}} = 0 \land f_{\text{loss}} \ge f_{\text{lat}} \\ 0.0 & \text{otherwise} \end{cases}$$
8. **`UNKNOWN_COMPOSITE_ANOMALY`**:
   $$S(\text{UNKNOWN\_COMPOSITE\_ANOMALY}) = \begin{cases} \min(0.65, 0.4 \cdot f_{\text{lat}} + 0.3 \cdot f_{\text{loss}} + 0.3 \cdot f_{\text{util}}) & \text{if } \max_{c \neq \text{COMPOSITE}} S(c) < 0.70 \land \text{anomalies\_detected} \\ 0.0 & \text{otherwise} \end{cases}$$
9. **`HEALTHY`**:
   $$S(\text{HEALTHY}) = \max\left(0.0, 1.0 - \max_{k} f_k\right)$$

---

## 5. Candidate Selection Rule & Deterministic Tie-Breaking

The primary diagnosis prediction $c^*$ is the candidate maximizing candidate score:
$$c^* = \operatorname{arg\,max}_{c \in \mathcal{C}} S(c)$$

### Tie-Breaking Priority
In case of equal scores $S(c_1) = S(c_2)$, ties are resolved deterministically using the following fixed precedence order:
1. `INTERFACE_FAILURE`
2. `ROUTING_MISCONFIGURATION`
3. `DC_MTU_MISMATCH`
4. `OSPF_ADJACENCY_FLAP`
5. `WAN_PATH_DEGRADATION`
6. `HIGH_LATENCY_CONGESTION`
7. `PACKET_LOSS`
8. `UNKNOWN_COMPOSITE_ANOMALY`
9. `HEALTHY`

---

## 6. Confidence Score Semantics ($C$)

The diagnostic confidence score $C \in [0.0, 1.0]$ is derived mathematically from the top candidate score $S(c^*)$ and the runner-up score $S(c^{(2)})$ via margin discounting:
$$C = \begin{cases} 1.0 & \text{if } c^* = \text{HEALTHY and } S(\text{HEALTHY}) = 1.0 \\ \text{round}\left(S(c^*) \cdot (1.0 - 0.5 \cdot S(c^{(2)})), 4\right) & \text{otherwise} \end{cases}$$

### Documentation of Semantics
$C$ represents a deterministic evidence margin intensity score in $[0, 1]$. It is **not** a calibrated posterior probability distribution.

---

## 7. Escalation Threshold & Decision Policy

The escalation decision flag `escalation_required` is evaluated as:
$$\text{escalation\_required} = (C < \Theta_{\text{esc}}) \lor (c^* = \text{UNKNOWN\_COMPOSITE\_ANOMALY})$$
where $\Theta_{\text{esc}} = 0.70$.

---

## 8. Missing, Non-Finite, and Boundary Input Behavior

1. **Absent Telemetry**: Missing interface, link, or route dictionaries yield feature values $0.0$.
2. **Non-Finite Values (`NaN`, `Inf`)**: All float inputs are sanitized via `math.isnan()` / `math.isinf()` check and coerced to $0.0$.
3. **Zero Denominators**: Normalized ratios use $\max(1, N)$ or explicit guard conditions to prevent division by zero.
4. **Numerical Precision**: Float operations are rounded to 4 decimal places for deterministic cross-platform reproducibility.

---

## 9. Comparison with Audited Implementation

| Aspect | Audited Implementation ([`cadd/engine.py`](file:///d:/NetOpsAI/backend/app/cadd/engine.py)) | Phase 2 Algorithm Specification | Reason for Change |
|---|---|---|---|
| **Scenario Branching** | Hardcoded `if topology_id == "CASE_01"` | Fully removed; evaluates features only | Eliminates ground-truth leakage path |
| **Confidence Origin** | Hardcoded literals (`0.95`, `0.47`, etc.) | Derived from evidence margin $S(c^*)(1 - 0.5 S(c^{(2)}))$ | Ensures mathematical reproducibility |
| **Candidate Scoring** | Rule matching order | Multi-attribute feature aggregation $S(c)$ | Standardizes evidence weighting |
| **Unknown Faults** | Forced by `CASE_04` ID match | Dynamic score when no single candidate $\ge 0.70$ | Replaces scenario lookup with telemetry logic |
| **Deterministic Tie-Breaking** | Implicit if-else order | Explicit pre-defined precedence list | Guarantees reproducible execution |
