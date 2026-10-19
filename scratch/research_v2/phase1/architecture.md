# Research V2 Architecture & Dataflow

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
