# 4-Node Linear Research Topology Specification

- `rns-host-a`: IP `10.0.1.10/24`, Gateway `10.0.1.1`
- `rns-router-1`: IPs `10.0.1.1/24` (veth-r1-ha), `10.0.2.1/24` (veth-r1-r2), Route `10.0.3.0/24 via 10.0.2.2`
- `rns-router-2`: IPs `10.0.2.2/24` (veth-r2-r1), `10.0.3.1/24` (veth-r2-hb), Route `10.0.1.0/24 via 10.0.2.1`
- `rns-host-b`: IP `10.0.3.10/24`, Gateway `10.0.3.1`
