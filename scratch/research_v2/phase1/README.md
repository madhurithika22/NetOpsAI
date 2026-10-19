# NetOps Research V2 — Phase 1 Real Linux Namespace Testbed

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
