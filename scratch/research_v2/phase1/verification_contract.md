# Independent Verification Contract Specification

- **Component**: `IndependentVerifier`
- **Checks**:
  1. `reachability_healthy`: `ping -c 5` packets received > 0
  2. `loss_healthy`: Measured loss <= 5.0%
  3. `rtt_healthy`: Measured RTT avg <= 20.0ms
  4. `qdisc_absent`: `tc qdisc show dev veth-r1-r2` does NOT contain `netem`
