from datetime import datetime, timezone
from typing import Dict, List
from app.scenarios.base import (
    ScenarioDefinition, TopologyNode, TopologyLink, TopologyService,
    FaultDefinition, RemediationCandidate
)
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics

def get_case03_datacenter_scenario() -> ScenarioDefinition:
    nodes = []
    for s in range(1, 5):
        nodes.append(TopologyNode(id=f"spine-0{s}", name=f"Spine Switch {s}", role="spine_switch", layer="core", ip_address=f"10.100.0.{s}"))
    for l in range(1, 9):
        nodes.append(TopologyNode(id=f"leaf-0{l}", name=f"Leaf Switch {l}", role="leaf_switch", layer="distribution", ip_address=f"10.100.1.{l}"))

    for a in range(1, 9):
        nodes.append(TopologyNode(id=f"app-srv-0{a}", name=f"App Node {a}", role="server", layer="services", ip_address=f"10.100.2.{a}"))
    for d in range(1, 5):
        nodes.append(TopologyNode(id=f"db-srv-0{d}", name=f"DB Cluster Node {d}", role="server", layer="services", ip_address=f"10.100.3.{d}"))
    for c in range(1, 5):
        nodes.append(TopologyNode(id=f"cache-0{c}", name=f"Redis Cache {c}", role="server", layer="services", ip_address=f"10.100.4.{c}"))
    for st in range(1, 5):
        nodes.append(TopologyNode(id=f"storage-0{st}", name=f"NVMe-oF Storage {st}", role="server", layer="services", ip_address=f"10.100.5.{st}"))

    nodes.extend([
        TopologyNode(id="lb-01", name="DC Ingress Load Balancer 1", role="load_balancer", layer="edge", ip_address="10.100.10.1"),
        TopologyNode(id="lb-02", name="DC Ingress Load Balancer 2", role="load_balancer", layer="edge", ip_address="10.100.10.2"),
        TopologyNode(id="fw-dc-01", name="DC Perimeter Firewall 1", role="firewall", layer="edge", ip_address="10.100.10.10"),
        TopologyNode(id="fw-dc-02", name="DC Perimeter Firewall 2", role="firewall", layer="edge", ip_address="10.100.10.11"),
    ])

    links = []
    # 1. Leaf to Spine Mesh (Connect each of 8 Leaf switches to all 4 Spine switches) -> 32 links
    for l in range(1, 9):
        for s in range(1, 5):
            links.append(TopologyLink(
                id=f"l-leaf0{l}-spine0{s}",
                source_node=f"leaf-0{l}",
                target_node=f"spine-0{s}",
                source_interface=f"eth{s}",
                target_interface=f"eth{l}",
                bandwidth_mbps=100000.0,
                latency_ms=0.1
            ))

    # 2. App Servers (1-8) to Leaf Switches
    for a in range(1, 9):
        lf_idx = ((a - 1) % 4) + 1
        links.append(TopologyLink(id=f"l-leaf0{lf_idx}-app0{a}", source_node=f"leaf-0{lf_idx}", target_node=f"app-srv-0{a}", source_interface=f"eth1{a}", target_interface="eth0"))

    # 3. DB Servers (1-4) to Leaf Switches (5-8)
    for d in range(1, 5):
        lf_idx = d + 4
        links.append(TopologyLink(id=f"l-leaf0{lf_idx}-db0{d}", source_node=f"leaf-0{lf_idx}", target_node=f"db-srv-0{d}", source_interface=f"eth1{d}", target_interface="eth0"))

    # 4. Cache Nodes (1-4) to Leaf Switches
    for c in range(1, 5):
        links.append(TopologyLink(id=f"l-leaf0{c}-cache0{c}", source_node=f"leaf-0{c}", target_node=f"cache-0{c}", source_interface="eth20", target_interface="eth0"))

    # 5. Storage Nodes (1-4) to Leaf Switches
    for st in range(1, 5):
        lf_idx = st + 4
        links.append(TopologyLink(id=f"l-leaf0{lf_idx}-storage0{st}", source_node=f"leaf-0{lf_idx}", target_node=f"storage-0{st}", source_interface="eth20", target_interface="eth0"))

    # 6. Load Balancers and Firewalls to Spine Core
    links.append(TopologyLink(id="l-spine01-lb01", source_node="spine-01", target_node="lb-01", source_interface="eth10", target_interface="eth0"))
    links.append(TopologyLink(id="l-spine02-lb02", source_node="spine-02", target_node="lb-02", source_interface="eth10", target_interface="eth0"))
    links.append(TopologyLink(id="l-spine03-fw01", source_node="spine-03", target_node="fw-dc-01", source_interface="eth10", target_interface="eth0"))
    links.append(TopologyLink(id="l-spine04-fw02", source_node="spine-04", target_node="fw-dc-02", source_interface="eth10", target_interface="eth0"))

    services = [
        TopologyService(id="svc-microservices", name="Cloud Microservices Mesh", hosted_on="app-srv-01", port=8080),
        TopologyService(id="svc-db-cluster", name="Distributed Database Cluster", hosted_on="db-srv-01", port=5432),
        TopologyService(id="svc-redis", name="In-Memory Cache Cluster", hosted_on="cache-01", port=6379),
    ]

    fault = FaultDefinition(
        fault_type="MTU_MISMATCH_FRAGMENTATION_CASCADE",
        target_element="spine-01<->leaf-03",
        description="MTU misconfiguration (1400 bytes on spine-01 eth3 vs 9000 bytes jumbo frame on leaf-03 eth1) causes silent ICMP drop, TCP retransmission storm, connection resets, and transaction delay.",
        causal_chain=[
            "spine-01 eth3 interface MTU accidentally configured to 1400 instead of 9000 jumbo frame standard",
            "db-srv-01 sends large SQL query response packets (MSS=8960 bytes) with DF (Don't Fragment) bit set",
            "spine-01 drops jumbo packets exceeding MTU 1400 and fails to return ICMP Fragmentation Needed",
            "Transport layer TCP retransmissions spike by 400% on app-srv-01 to db-srv-01 stream",
            "TCP socket connection reset count increases rapidly",
            "App server transaction latency surges from 2ms to 320ms due to TCP timeouts"
        ]
    )

    remed = RemediationCandidate(
        action_id="act-case03-remed",
        command_type="SET_INTERFACE_MTU",
        target_device="spine-01",
        parameters={
            "interface": "eth3",
            "mtu": 9000
        },
        reversion_action={
            "interface": "eth3",
            "mtu": 1400
        },
        description="Reconfigure spine-01 eth3 MTU to 9000 bytes to align jumbo frame size across the Leaf-Spine fabric.",
        is_destructive=True
    )

    return ScenarioDefinition(
        scenario_id="CASE_03",
        name="Leaf-Spine Data Center",
        description="36-node Leaf-Spine data center fabric suffering MTU fragmentation mismatch and TCP retransmission cascade.",
        category="Data Center Fabric / MTU Mismatch",
        target_node_count=36,
        target_link_count=len(links),
        nodes=nodes,
        links=links,
        services=services,
        fault_definition=fault,
        expected_fault_domain="Leaf-Spine Fabric MTU Alignment",
        expected_behavior="CADD correlates network MTU mismatch, TCP retransmission spike, and application latency.",
        remediation_candidates=[remed],
        verification_criteria={"expected_mtu": 9000, "max_retransmissions_pct": 0.1, "max_transaction_latency_ms": 5.0},
        llm_escalation_required=False,
        llm_confidence_threshold=0.70
    )

def generate_case03_telemetry(active_fault: str) -> NetworkState:
    now = datetime.now(timezone.utc)
    is_fault = (active_fault == "MTU_MISMATCH_FRAGMENTATION_CASCADE")

    nodes = {
        "spine-01": NodeMetrics(node_id="spine-01", cpu_utilization_pct=65.0 if is_fault else 15.0, memory_utilization_pct=40.0),
        "leaf-03": NodeMetrics(node_id="leaf-03", cpu_utilization_pct=58.0 if is_fault else 14.0, memory_utilization_pct=38.0),
        "app-srv-01": NodeMetrics(node_id="app-srv-01", cpu_utilization_pct=82.0 if is_fault else 10.0, memory_utilization_pct=35.0),
        "db-srv-01": NodeMetrics(node_id="db-srv-01", cpu_utilization_pct=75.0 if is_fault else 20.0, memory_utilization_pct=55.0),
    }

    interfaces = {
        "spine-01-eth3": InterfaceState(
            name="spine-01-eth3",
            is_up=True,
            ip_addresses=["10.100.0.1/30"],
            mac_address="52:54:00:30:01:03",
            rx_bytes=50000000,
            tx_bytes=50000000,
            rx_errors=1240 if is_fault else 0,
            rx_drops=4500 if is_fault else 0,
            throughput_bps=450000000.0,
            utilization_pct=45.0,
            mtu=1400 if is_fault else 9000
        ),
        "leaf-03-eth1": InterfaceState(
            name="leaf-03-eth1",
            is_up=True,
            ip_addresses=["10.100.1.3/30"],
            mac_address="52:54:00:30:03:01",
            rx_bytes=50000000,
            tx_bytes=50000000,
            rx_errors=0,
            rx_drops=0,
            throughput_bps=450000000.0,
            utilization_pct=45.0,
            mtu=9000
        )
    }

    links = [
        LinkLatency(
            source_node="leaf-03",
            target_node="spine-01",
            rtt_ms=320.0 if is_fault else 0.4,
            packet_loss_pct=28.0 if is_fault else 0.0,
            status="DEGRADED" if is_fault else "HEALTHY"
        ),
        LinkLatency(source_node="app-srv-01", target_node="leaf-01", rtt_ms=0.2, packet_loss_pct=0.0, status="HEALTHY"),
        LinkLatency(source_node="leaf-03", target_node="db-srv-01", rtt_ms=0.3, packet_loss_pct=0.0, status="HEALTHY"),
    ]

    routes = [
        RouteEntry(destination="10.100.3.0/24", gateway="10.100.0.1", interface="spine-01-eth3", metric=10)
    ]

    return NetworkState(
        snapshot_id="snap-case03",
        timestamp=now,
        topology_id="CASE_03",
        interfaces=interfaces,
        links=links,
        routes=routes,
        nodes=nodes,
        anomalies_detected=is_fault
    )
