import os
import json

def write_f(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'[OK] Wrote {path}')

def generate_docs():
    print("Generating Phase 1 Documentation...")

    # 1. README.md
    readme_md = """# NetOps Research V2 — Phase 1 Real Linux Namespace Testbed

## Overview
Phase 1 establishes the physical/software experimental substrate for NetOps Research V2. It replaces synthetic telemetry and simulated state resets with an authentic Linux Network Namespace testbed supporting causal fault injection, real command execution, independent verification, and raw command recording.

## Core Package Structure
- `backend/app/research_v2/guard.py`: `ResearchExecutionContext` guard enforcing zero simulation paths during research runs.
- `backend/app/research_v2/testbed/capabilities.py`: `check_testbed_capabilities()` detecting OS, `ip`, `tc`, `ping`, and `netns` support.
- `backend/app/research_v2/testbed/executor.py`: `ControlledExecutor` running namespace commands safely via list args.
- `backend/app/research_v2/testbed/namespace.py`: `NamespaceManager` handling `ip netns` creation and teardown.
- `backend/app/research_v2/testbed/links.py`: `LinkManager` creating veth pairs and setting MTU / state.
- `backend/app/research_v2/testbed/addressing.py`: `AddressManager` configuring IP CIDRs inside namespaces.
- `backend/app/research_v2/testbed/routing.py`: `RoutingManager` enabling sysctl forwarding and static routes.
- `backend/app/research_v2/testbed/topology.py`: `ResearchTopology` managing 4-node topology (`rns-host-a` <-> `rns-router-1` <-> `rns-router-2` <-> `rns-host-b`).
- `backend/app/research_v2/testbed/telemetry.py`: `RealTelemetryCollector` collecting ping probes, interface counters, routes, and tc qdisc states.
- `backend/app/research_v2/testbed/faults.py`: `RealFaultInjector` injecting `tc qdisc add dev veth-r1-r2 root netem delay 150ms loss 20%`.
- `backend/app/research_v2/testbed/remediation.py`: `RealRemediationExecutor` executing `tc qdisc del dev veth-r1-r2 root`.
- `backend/app/research_v2/testbed/verification.py`: `IndependentVerifier` independently checking RTT, packet loss, and qdisc removal.
- `backend/app/research_v2/testbed/recorder.py`: `ExperimentRecorder` saving immutable JSON run records to `scratch/research_v2/phase1/runs/`.
"""
    write_f("scratch/research_v2/phase1/README.md", readme_md)

    # 2. architecture.md
    arch_md = """# Research V2 Architecture & Dataflow

```
REAL LINUX NETWORK NAMESPACES (rns-host-a, rns-router-1, rns-router-2, rns-host-b)
  ↓
CAPABILITY CHECK (Linux, iproute2, tc, ping, netns, CAP_NET_ADMIN)
  ↓
REAL BASELINE TELEMETRY (RealTelemetryCollector probing ICMP & sysfs/netstat)
  ↓
REAL FAULT INJECTION (tc qdisc add dev veth-r1-r2 root netem delay 150ms loss 20%)
  ↓
ACTIVATION VERIFICATION (Telemetry confirms RTT > 50ms / loss > 10%)
  ↓
REAL REMEDIATION EXECUTION (tc qdisc del dev veth-r1-r2 root)
  ↓
INDEPENDENT POST-REMEDIATION VERIFICATION (Probes RTT < 20ms & netem qdisc absent)
  ↓
IMMUTABLE EXPERIMENT RECORD (JSON stored in scratch/research_v2/phase1/runs/)
```
"""
    write_f("scratch/research_v2/phase1/architecture.md", arch_md)

    # 3. topology.md
    topo_md = """# 4-Node Linear Research Topology Specification

- `rns-host-a`: IP `10.0.1.10/24`, Gateway `10.0.1.1`
- `rns-router-1`: IPs `10.0.1.1/24` (veth-r1-ha), `10.0.2.1/24` (veth-r1-r2), Route `10.0.3.0/24 via 10.0.2.2`
- `rns-router-2`: IPs `10.0.2.2/24` (veth-r2-r1), `10.0.3.1/24` (veth-r2-hb), Route `10.0.1.0/24 via 10.0.2.1`
- `rns-host-b`: IP `10.0.3.10/24`, Gateway `10.0.3.1`
"""
    write_f("scratch/research_v2/phase1/topology.md", topo_md)

    # 4. fault_model.md
    fault_md = """# Fault Model Specification — HIGH_LATENCY_CONGESTION

- **Fault ID**: `flt-001`
- **Fault Type**: `HIGH_LATENCY_CONGESTION`
- **Target Namespace**: `rns-router-1`
- **Target Interface**: `veth-r1-r2`
- **Injection Mechanism**: `tc qdisc add dev veth-r1-r2 root netem delay 150ms loss 20%`
- **Activation Criteria**: `RTT > 50.0ms` OR `packet_loss > 10.0%`
"""
    write_f("scratch/research_v2/phase1/fault_model.md", fault_md)

    # 5. remediation_contract.md
    rem_md = """# Remediation Contract Specification

- **Plan ID**: `plan-<id>`
- **Target Namespace**: `rns-router-1`
- **Target Interface**: `veth-r1-r2`
- **Remediation Command**: `tc qdisc del dev veth-r1-r2 root`
- **Causal Guarantee**: The command directly removes the netem qdisc queue on `veth-r1-r2`. No `reset_simulation()` or mock state modification is used.
"""
    write_f("scratch/research_v2/phase1/remediation_contract.md", rem_md)

    # 6. verification_contract.md
    ver_md = """# Independent Verification Contract Specification

- **Component**: `IndependentVerifier`
- **Checks**:
  1. `reachability_healthy`: `ping -c 5` packets received > 0
  2. `loss_healthy`: Measured loss <= 5.0%
  3. `rtt_healthy`: Measured RTT avg <= 20.0ms
  4. `qdisc_absent`: `tc qdisc show dev veth-r1-r2` does NOT contain `netem`
"""
    write_f("scratch/research_v2/phase1/verification_contract.md", ver_md)

    # 7. research_integrity.md
    integ_md = """# Research Integrity Rules for Phase 1

1. ZERO SIMULATION FALLBACKS: If host OS lacks Linux network namespace support, capability check fails explicitly.
2. NO FABRICATED MEASUREMENTS: Telemetry snapshot fields are parsed directly from shell command output.
3. CAUSAL REMEDIATION: Remediation requires running real corrective commands (`tc qdisc del`).
4. IMMUTABLE RAW EVIDENCE: All raw command stdout, stderr, and exit codes are recorded in experiment JSON logs.
"""
    write_f("scratch/research_v2/phase1/research_integrity.md", integ_md)

    # 8. phase1_status.json
    status_json = {
        "phase": "1",
        "implementation_complete": True,
        "capabilities_implemented": True,
        "topology_implemented": True,
        "telemetry_implemented": True,
        "fault_injector_implemented": True,
        "remediation_executor_implemented": True,
        "independent_verifier_implemented": True,
        "experiment_recorder_implemented": True,
        "research_guard_implemented": True,
        "simulation_paths_removed_from_research_path": True,
        "ready_for_linux_execution": True
    }
    write_f("scratch/research_v2/phase1/phase1_status.json", json.dumps(status_json, indent=2))

    print("Phase 1 Documentation generation complete.")

if __name__ == "__main__":
    generate_docs()
