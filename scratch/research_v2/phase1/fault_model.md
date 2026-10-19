# Fault Model Specification — HIGH_LATENCY_CONGESTION

- **Fault ID**: `flt-001`
- **Fault Type**: `HIGH_LATENCY_CONGESTION`
- **Target Namespace**: `rns-router-1`
- **Target Interface**: `veth-r1-r2`
- **Injection Mechanism**: `tc qdisc add dev veth-r1-r2 root netem delay 150ms loss 20%`
- **Activation Criteria**: `RTT > 50.0ms` OR `packet_loss > 10.0%`
