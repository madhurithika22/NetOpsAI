from datetime import datetime, timezone
from typing import Dict, List
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics

class NetworkStateSimulator:
    """
    Simulates a 3-node topology (HostA <-> Router1 <-> Router2 <-> HostB).
    Provides baseline telemetry observations and 4 distinct fault injection profiles.
    """
    FAULT_PROFILES = [
        "NONE",
        "HIGH_LATENCY_CONGESTION",
        "PACKET_LOSS",
        "INTERFACE_FAILURE",
        "ROUTING_MISCONFIGURATION",
        "REROUTED"
    ]

    def __init__(self):
        self.active_fault: str = "NONE"
        self.snapshot_counter: int = 0

    def inject_fault(self, fault_type: str = "HIGH_LATENCY_CONGESTION"):
        if fault_type not in self.FAULT_PROFILES:
            raise ValueError(f"Unknown fault profile: {fault_type}. Allowed: {self.FAULT_PROFILES}")
        self.active_fault = fault_type

    def reset(self):
        self.active_fault = "NONE"

    def generate_snapshot(self) -> NetworkState:
        self.snapshot_counter += 1
        snapshot_id = f"snap-{self.snapshot_counter:04d}"
        now = datetime.now(timezone.utc)

        # Base node metrics
        nodes = {
            "rtr1": NodeMetrics(
                node_id="rtr1",
                cpu_utilization_pct=85.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 18.5,
                memory_utilization_pct=42.0
            ),
            "rtr2": NodeMetrics(
                node_id="rtr2",
                cpu_utilization_pct=22.0,
                memory_utilization_pct=38.0
            ),
            "hostA": NodeMetrics(
                node_id="hostA",
                cpu_utilization_pct=5.0,
                memory_utilization_pct=20.0
            ),
            "hostB": NodeMetrics(
                node_id="hostB",
                cpu_utilization_pct=5.0,
                memory_utilization_pct=20.0
            )
        }

        # Determine interface states based on active fault
        rtr1_eth1_up = True
        rtr1_eth1_rx_err = 0
        rtr1_eth1_rx_drop = 0
        rtr1_eth1_tx_drop = 0
        rtr1_eth1_throughput = 100_000.0  # 100 Kbps baseline
        rtr1_eth1_util = 10.0

        if self.active_fault == "INTERFACE_FAILURE":
            rtr1_eth1_up = False
            rtr1_eth1_rx_err = 45
            rtr1_eth1_throughput = 0.0
            rtr1_eth1_util = 0.0
        elif self.active_fault == "HIGH_LATENCY_CONGESTION":
            rtr1_eth1_rx_err = 12
            rtr1_eth1_throughput = 950_000.0  # 950 Kbps
            rtr1_eth1_util = 95.0
        elif self.active_fault == "PACKET_LOSS":
            rtr1_eth1_rx_drop = 240
            rtr1_eth1_tx_drop = 180
            rtr1_eth1_throughput = 450_000.0
            rtr1_eth1_util = 45.0

        interfaces = {
            "rtr1-eth0": InterfaceState(
                name="rtr1-eth0",
                is_up=True,
                ip_addresses=["10.0.1.1/24"],
                mac_address="52:54:00:12:34:56",
                rx_bytes=1024000,
                tx_bytes=2048000,
                rx_errors=0,
                tx_errors=0,
                throughput_bps=100000.0,
                utilization_pct=10.0,
                mtu=1500
            ),
            "rtr1-eth1": InterfaceState(
                name="rtr1-eth1",
                is_up=rtr1_eth1_up,
                ip_addresses=["10.0.2.1/24"],
                mac_address="52:54:00:12:34:57",
                rx_bytes=512000,
                tx_bytes=8192000,
                rx_errors=rtr1_eth1_rx_err,
                tx_errors=0,
                rx_drops=rtr1_eth1_rx_drop,
                tx_drops=rtr1_eth1_tx_drop,
                throughput_bps=rtr1_eth1_throughput,
                utilization_pct=rtr1_eth1_util,
                mtu=1500
            ),
            "rtr2-eth0": InterfaceState(
                name="rtr2-eth0",
                is_up=True,
                ip_addresses=["10.0.2.2/24"],
                mac_address="52:54:00:12:34:58",
                rx_bytes=8192000,
                tx_bytes=512000,
                rx_errors=0,
                tx_errors=0,
                throughput_bps=100000.0,
                utilization_pct=10.0,
                mtu=1500
            ),
        }

        # Determine link latency and health
        if self.active_fault == "HIGH_LATENCY_CONGESTION":
            rtr1_rtr2_link = LinkLatency(
                source_node="rtr1",
                target_node="rtr2",
                rtt_ms=145.5,
                packet_loss_pct=15.0,
                status="DEGRADED"
            )
        elif self.active_fault == "PACKET_LOSS":
            rtr1_rtr2_link = LinkLatency(
                source_node="rtr1",
                target_node="rtr2",
                rtt_ms=12.0,
                packet_loss_pct=25.0,
                status="DEGRADED"
            )
        elif self.active_fault == "INTERFACE_FAILURE":
            rtr1_rtr2_link = LinkLatency(
                source_node="rtr1",
                target_node="rtr2",
                rtt_ms=999.0,
                packet_loss_pct=100.0,
                status="UNREACHABLE"
            )
        else:
            rtr1_rtr2_link = LinkLatency(
                source_node="rtr1",
                target_node="rtr2",
                rtt_ms=4.8,
                packet_loss_pct=0.0,
                status="HEALTHY"
            )

        links = [
            LinkLatency(
                source_node="hostA",
                target_node="rtr1",
                rtt_ms=1.2,
                packet_loss_pct=0.0,
                status="HEALTHY"
            ),
            rtr1_rtr2_link,
            LinkLatency(
                source_node="rtr2",
                target_node="hostB",
                rtt_ms=2.1,
                packet_loss_pct=0.0,
                status="HEALTHY"
            ),
        ]

        # Determine routing entries
        if self.active_fault == "ROUTING_MISCONFIGURATION":
            # Invalid blackhole egress interface on rtr1 route for 10.0.2.0/24
            target_route = RouteEntry(
                destination="10.0.2.0/24",
                gateway=None,
                interface="rtr1-eth0",  # Loopback/Wrong interface!
                metric=999
            )
        elif self.active_fault == "REROUTED":
            target_route = RouteEntry(
                destination="10.0.2.0/24",
                gateway="10.0.2.2",
                interface="rtr1-eth1",
                metric=100
            )
        else:
            target_route = RouteEntry(
                destination="10.0.2.0/24",
                gateway="10.0.2.2",
                interface="rtr1-eth1",
                metric=10
            )

        routes = [
            RouteEntry(
                destination="10.0.1.0/24",
                gateway=None,
                interface="rtr1-eth0",
                metric=10
            ),
            target_route
        ]

        anomalies_detected = self.active_fault not in ["NONE", "REROUTED"]

        return NetworkState(
            snapshot_id=snapshot_id,
            timestamp=now,
            topology_id="sim-3node-mesh",
            interfaces=interfaces,
            links=links,
            routes=routes,
            nodes=nodes,
            anomalies_detected=anomalies_detected
        )
