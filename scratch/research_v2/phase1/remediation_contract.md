# Remediation Contract Specification

- **Plan ID**: `plan-<id>`
- **Target Namespace**: `rns-router-1`
- **Target Interface**: `veth-r1-r2`
- **Remediation Command**: `tc qdisc del dev veth-r1-r2 root`
- **Causal Guarantee**: The command directly removes the netem qdisc queue on `veth-r1-r2`. No `reset_simulation()` or mock state modification is used.
