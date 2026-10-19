# NetOps: Context-Aware Autonomous Network Incident Management Prototype

**NetOps** is an academic research prototype demonstrating a closed-loop, explainable, and safe automated network incident management workflow using open-source technologies and local execution.

---

## Architectural Architecture & Layering

The system is structured around three strictly decoupled, independent layers:

1. **CESO (Context Extraction and State Observation)**:
   * **Provider Abstraction Layer**: Supports two telemetry collection modes:
     * `SIMULATED` (Default): In-memory simulator for rapid, unprivileged local development on any OS.
     * `LINUX_TESTBED`: Queries real Linux network namespaces (`netns`) and `veth` pairs via `iproute2` and `ping` probes on Linux/WSL2 (with fallback parser on non-Linux platforms).
   * Normalizes observations into standardized `NetworkState` schema snapshots.
   * Exposes real-time Server-Sent Events (SSE) telemetry stream (`/api/v1/ceso/stream`).

2. **CADD (Context-Aware Diagnosis and Decision)**:
   * Consumes normalized `NetworkState` snapshots regardless of underlying telemetry provider.
   * Evaluates deterministic, explainable rules matching 4 distinct fault profiles.
   * Generates a `DiagnosticReport` with an explicit **Explainable Evidence Chain** (matched rules, observed values, threshold bounds) and an actionable `ActionPlan`.

3. **MSVS (Multi-Stage Validation and Safety)**:
   * **Stage 1 (Static Policy Guard)**: Enforces command whitelists and protects host management interfaces (`eth0`, `wlan0`, `lo`, `mgmt0`, `docker0`).
   * **Stage 2 (Impact & Parameter Bounds Pre-Check)**: Syntax and parameter validation.
   * **Stage 3 (Human-in-the-Loop Approval)**: Queues state-changing actions for explicit operator approval.
   * **Stage 4 (Controlled Execution)**: Executes permitted actions in a controlled simulated or isolated testbed environment.
   * **Stage 5 (Post-Action Verification)**: Re-queries CESO state snapshots to verify fault resolution.
   * **Research Evaluation Tracker**: Records lifecycle timestamps (`fault_injection`, `detection`, `diagnosis`, `approval`, `execution`, `verification`) and computes metrics (`MTTD`, `MTTR`, `Diagnostic Latency`, `Remediation Success Rate`, `Policy Violation Prevention Rate`).

---

## Isolated Linux Network Testbed Topology (Phase 4)

In `LINUX_TESTBED` mode, NetOps constructs an isolated 4-node network topology:

```text
[netops-hosta] <--- (veth-ha-r1) ---> [netops-rtr1] <--- (veth-r1-r2) ---> [netops-rtr2] <--- (veth-hb-r2) ---> [netops-hostb]
   10.0.1.10/24                        10.0.1.1/24                          10.0.2.2/24                        10.0.3.10/24
                                       10.0.2.1/24                          10.0.3.1/24
```

### Safety & Ownership Restrictions
* All NetOps testbed resources are prefixed with `netops-` or `veth-`.
* The `TestbedManager` and `SafetyPolicyEngine` strictly reject any command or parameter targeting host management interfaces (`eth0`, `wlan0`, `lo`) or unowned namespaces.

---

## 4 Fault Injection Scenarios

NetOps includes four deterministic network degradation profiles for research evaluation:

1. **High Latency & Congestion** (`HIGH_LATENCY_CONGESTION`):
   * *Symptom*: Link RTT spikes to `145.5ms` (threshold: `50.0ms`), `15%` packet loss, `95%` interface utilization, CPU `85%`.
   * *Linux Testbed Mechanism*: `tc qdisc add dev veth-r1-r2 root netem delay 145ms loss 15%`.
   * *Remediation*: `REROUTE_TRAFFIC` (modifies route metric to bypass congested path).
2. **Packet Loss Spike** (`PACKET_LOSS`):
   * *Symptom*: Link packet loss jumps to `25%`, `240` dropped packets.
   * *Linux Testbed Mechanism*: `tc qdisc add dev veth-r1-r2 root netem loss 25%`.
   * *Remediation*: `REROUTE_TRAFFIC` / buffer adjustment.
3. **Interface Link Failure** (`INTERFACE_FAILURE`):
   * *Symptom*: Interface status `is_up = False`, link status `UNREACHABLE`, link loss `100%`.
   * *Linux Testbed Mechanism*: `ip link set dev veth-r1-r2 down`.
   * *Remediation*: `SET_INTERFACE_STATE` (`target_state: UP`).
4. **Routing Table Misconfiguration** (`ROUTING_MISCONFIGURATION`):
   * *Symptom*: Destination route points to invalid egress interface (`rtr1-eth0`) or metric `999` (blackhole route).
   * *Linux Testbed Mechanism*: `ip route del 10.0.3.0/24`.
   * *Remediation*: `RESTORE_ROUTING_TABLE` (restores valid gateway and metric).

---

## API Endpoint Reference

| Module | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **CESO** | `GET` | `/api/v1/ceso/state` | Retrieve current normalized network state snapshot |
| **CESO** | `POST` | `/api/v1/ceso/collect` | Trigger immediate telemetry collection |
| **CESO** | `GET` | `/api/v1/ceso/stream` | Server-Sent Events (SSE) live telemetry stream |
| **CADD** | `POST` | `/api/v1/cadd/diagnose` | Run explainable diagnosis on current state |
| **CADD** | `GET` | `/api/v1/cadd/latest` | Fetch latest diagnostic report and action plan |
| **MSVS** | `POST` | `/api/v1/msvs/validate` | Validate action plan against safety policies |
| **MSVS** | `GET` | `/api/v1/msvs/approvals` | List pending human approval requests |
| **MSVS** | `POST` | `/api/v1/msvs/approvals/{id}/approve` | Approve a pending action plan |
| **MSVS** | `POST` | `/api/v1/msvs/approvals/{id}/reject` | Reject a pending action plan |
| **MSVS** | `POST` | `/api/v1/msvs/execute/{id}` | Execute approved plan in active environment |
| **MSVS** | `GET` | `/api/v1/msvs/audit-logs` | Retrieve execution audit log history |
| **MSVS** | `GET` | `/api/v1/msvs/metrics` | Retrieve research evaluation metrics summary |
| **MSVS** | `GET` | `/api/v1/msvs/metrics/export-csv` | Download evaluation metrics as CSV file |
| **SIM** | `GET` | `/api/v1/simulation/environment` | Retrieve active provider mode and testbed status |
| **SIM** | `POST` | `/api/v1/simulation/environment/switch` | Switch active provider mode (`SIMULATED` vs `LINUX_TESTBED`) |
| **SIM** | `GET` | `/api/v1/simulation/testbed/status` | Query status of Linux network namespace testbed |
| **SIM** | `POST` | `/api/v1/simulation/testbed/create` | Create isolated Linux network namespace testbed |
| **SIM** | `POST` | `/api/v1/simulation/testbed/teardown` | Teardown isolated Linux network namespace testbed |
| **SIM** | `POST` | `/api/v1/simulation/inject-fault` | Inject fault scenario (`HIGH_LATENCY_CONGESTION`, `PACKET_LOSS`, `INTERFACE_FAILURE`, `ROUTING_MISCONFIGURATION`) |
| **SIM** | `POST` | `/api/v1/simulation/reset` | Reset simulation or testbed back to baseline healthy state |

---

## Local Running & Testing Instructions

### 1. Prerequisites
* Python 3.12+
* Node.js v20+ / npm
* (Optional for real testbed): Linux OS or WSL2 with `sudo` access to `ip` and `tc` utilities.

### 2. Running Backend
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 3. Running Frontend Dashboard
```powershell
cd frontend
npm run dev
```

### 4. Running Full Test Suite (29 Tests)
```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

---

## Verification & Environment Status

* **Simulated Mode**: Verified 100% functional on all platforms (Windows, Linux, macOS) without requiring root privileges.
* **Linux Testbed Mode**: Fully implemented with safe command lists, ownership validation, and fallback telemetry parser for Windows/unprivileged testing environments.

---

## Phase 3 Experimental Design & Baseline Provenance

The planned Phase 3 experimental matrix evaluates 3 primary diagnostic arms across 4 retained scenarios (`CASE_01` to `CASE_04`) with 120 planned rows:

1. **ARM_3_RULE_BASED**: Standard rule-matching engine (`RULE_BASED_VERSION = "1.0.0-arm3-rule-based"`).
2. **ARM_4_PHASE2_BASELINE** (Scientific Display Name: **Modified Phase 2-Derived Baseline**):
   - Evaluates the continuous heuristic candidate scoring engine currently implemented in [`backend/app/cadd/engine.py`](file:///d:/NetOpsAI/backend/app/cadd/engine.py) (SHA-256: `97227c88ee345b53474d11491912f3c960e2a2414f5059f7bf02d4a4c050bad8`, baseline Git commit: `0cc7a40fedea656a486117aa0201210a3dfa4661`).
   - The historical frozen Phase 2 engine is preserved separately as an archival research artifact under [`research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py`](file:///d:/NetOpsAI/research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py) (SHA-256: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`, 20,498 bytes) with documented incomplete formal Git SCM provenance. It is **not** imported into runtime execution.
   - The identifier `ARM_4_PHASE2_BASELINE` is retained strictly as an internal programmatic compatibility identifier for runner and matrix schemas.
3. **ARM_5_CESO_CADE_NO_LLM**: Context-Aware Diagnosis Engine (CADE) candidate scoring with CESO telemetry extraction without secondary LLM invocation.

> [!IMPORTANT]
> **Safety Guard**: Phase 3 research execution remains strictly unauthorized (`phase3_execution_authorized = false`). No experiment rows, live benchmarks, or fault injections are authorized.
