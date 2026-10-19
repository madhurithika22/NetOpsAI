# NetOps Phase 4 — Linux Testbed Validation

**Validation date:** 3 October 2026
**Environment:** Ubuntu on WSL2
**Topology:** Four Linux network namespaces
**Provider:** LINUX_TESTBED
**Fault:** HIGH_LATENCY_CONGESTION
**Status:** Successful functional validation

## 1. Testbed topology

* Host A: 10.0.1.10
* Router 1: 10.0.1.1 and 10.0.2.1
* Router 2: 10.0.2.2 and 10.0.3.1
* Host B: 10.0.3.10

## 2. Independent end-to-end fault measurement

| Metric              |     Result |
| ------------------- | ---------: |
| Packets transmitted |         20 |
| Packets received    |         16 |
| Packet loss         |        20% |
| Average RTT         | 145.376 ms |
| Minimum RTT         | 145.219 ms |
| Maximum RTT         | 145.495 ms |
| RTT mdev            |   0.091 ms |

## 3. NetOps telemetry during fault

| Metric                   |                    Result |
| ------------------------ | ------------------------: |
| Snapshot ID              |              snap-tb-0004 |
| Affected link            | netops-rtr1 → netops-rtr2 |
| RTT                      |                145.402 ms |
| Packet loss              |                       20% |
| Link status              |                  DEGRADED |
| Router 1 CPU utilization |                       85% |
| Anomalies detected       |                      True |

## 4. Recovery

| Metric                   |       Result |
| ------------------------ | -----------: |
| Snapshot ID              | snap-tb-0005 |
| Inter-router RTT         |     0.059 ms |
| Inter-router packet loss |           0% |
| Link status              |      HEALTHY |
| Router 1 CPU utilization |          25% |
| Anomalies detected       |        False |

Independent recovery ping:

* Packets transmitted: 10
* Packets received: 10
* Packet loss: 0%
* Average RTT: 0.081 ms

## 5. Validation conclusion

The Linux testbed successfully reproduced controlled latency and packet loss. NetOps telemetry correctly identified the affected inter-router link, reported the measured degradation, and detected anomalies. Following reset, the framework reported healthy links and cleared the anomaly state. Independent ping measurements confirmed restoration of end-to-end connectivity.

These results validate the tested fault-injection, telemetry, anomaly-detection, and recovery functions. They do not establish production-network performance or the full set of diagnostic and safety metrics.
