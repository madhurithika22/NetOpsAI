from datetime import datetime, timezone
from typing import Dict, List
from app.scenarios.base import (
    ScenarioDefinition, TopologyNode, TopologyLink, TopologyService,
    FaultDefinition, RemediationCandidate
)
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics

def get_case04_hybrid_scenario() -> ScenarioDefinition:
    nodes = []
    for eg in range(1, 5):
        nodes.append(TopologyNode(id=f"edge-gw-0{eg}", name=f"Edge Gateway {eg}", role="edge_gateway", layer="edge", ip_address=f"192.168.10.{eg}"))
    for en in range(1, 13):
        nodes.append(TopologyNode(id=f"edge-node-{en:02d}", name=f"IoT/Edge Compute Node {en}", role="edge_node", layer="edge", ip_address=f"192.168.20.{en}"))
    for wr in range(1, 5):
        nodes.append(TopologyNode(id=f"wan-rtr-0{wr}", name=f"SD-WAN Router {wr}", role="wan_router", layer="edge", ip_address=f"172.20.1.{wr}"))
    for sp in range(1, 5):
        nodes.append(TopologyNode(id=f"spine-dc-0{sp}", name=f"Hybrid Core Spine {sp}", role="spine_switch", layer="core", ip_address=f"10.50.0.{sp}"))
    for lf in range(1, 9):
        nodes.append(TopologyNode(id=f"leaf-dc-0{lf}", name=f"Hybrid Leaf Switch {lf}", role="leaf_switch", layer="distribution", ip_address=f"10.50.1.{lf}"))
    for ap in range(1, 7):
        nodes.append(TopologyNode(id=f"app-svc-0{ap}", name=f"Hybrid App Worker {ap}", role="server", layer="services", ip_address=f"10.50.2.{ap}"))
    for db in range(1, 5):
        nodes.append(TopologyNode(id=f"db-svc-0{db}", name=f"Hybrid DB Node {db}", role="server", layer="services", ip_address=f"10.50.3.{db}"))
    nodes.append(TopologyNode(id="cloud-gw-01", name="AWS DirectConnect Gateway", role="cloud_gateway", layer="cloud", ip_address="10.99.1.1"))
    nodes.append(TopologyNode(id="cloud-gw-02", name="Azure ExpressRoute Gateway", role="cloud_gateway", layer="cloud", ip_address="10.99.2.1"))
    for cs in range(1, 5):
        nodes.append(TopologyNode(id=f"cloud-svc-0{cs}", name=f"Cloud Serverless Worker {cs}", role="cloud_service", layer="cloud", ip_address=f"10.99.10.{cs}"))

    links = []
    # 1. Edge nodes to Edge Gateways (12 links)
    for en in range(1, 13):
        gw_idx = ((en - 1) % 4) + 1
        links.append(TopologyLink(
            id=f"l-en{en:02d}-eg0{gw_idx}",
            source_node=f"edge-node-{en:02d}",
            target_node=f"edge-gw-0{gw_idx}",
            source_interface="eth0",
            target_interface=f"eth{en}"
        ))

    # 2. Edge Gateways to SD-WAN Routers (4 links)
    for eg in range(1, 5):
        links.append(TopologyLink(id=f"l-eg0{eg}-wan0{eg}", source_node=f"edge-gw-0{eg}", target_node=f"wan-rtr-0{eg}", source_interface="wan0", target_interface="eth0"))

    # 3. SD-WAN Routers to Hybrid Spine Core (4 links)
    for wr in range(1, 5):
        links.append(TopologyLink(id=f"l-wan0{wr}-spine0{wr}", source_node=f"wan-rtr-0{wr}", target_node=f"spine-dc-0{wr}", source_interface="eth1", target_interface="eth0"))

    # 4. Spine Core Interconnect Mesh (4 links)
    links.append(TopologyLink(id="l-spine1-spine2", source_node="spine-dc-01", target_node="spine-dc-02", source_interface="eth90", target_interface="eth90"))
    links.append(TopologyLink(id="l-spine2-spine3", source_node="spine-dc-02", target_node="spine-dc-03", source_interface="eth91", target_interface="eth91"))
    links.append(TopologyLink(id="l-spine3-spine4", source_node="spine-dc-03", target_node="spine-dc-04", source_interface="eth92", target_interface="eth92"))
    links.append(TopologyLink(id="l-spine4-spine1", source_node="spine-dc-04", target_node="spine-dc-01", source_interface="eth93", target_interface="eth93"))

    # 5. DC Leaf-Spine Fabric Links (8 Leaf switches connected to Spine Core)
    for lf in range(1, 9):
        sp_idx = ((lf - 1) % 4) + 1
        links.append(TopologyLink(
            id=f"l-leaf0{lf}-spine0{sp_idx}",
            source_node=f"leaf-dc-0{lf}",
            target_node=f"spine-dc-0{sp_idx}",
            source_interface="eth0",
            target_interface=f"eth{lf}"
        ))

    # 6. DC Servers to Leaf Switches
    for ap in range(1, 7):
        lf_idx = ((ap - 1) % 4) + 1
        links.append(TopologyLink(
            id=f"l-app0{ap}-leaf0{lf_idx}",
            source_node=f"app-svc-0{ap}",
            target_node=f"leaf-dc-0{lf_idx}",
            source_interface="eth0",
            target_interface=f"eth1{ap}"
        ))

    for db in range(1, 5):
        lf_idx = ((db - 1) % 4) + 5
        links.append(TopologyLink(
            id=f"l-db0{db}-leaf0{lf_idx}",
            source_node=f"db-svc-0{db}",
            target_node=f"leaf-dc-0{lf_idx}",
            source_interface="eth0",
            target_interface=f"eth1{db}"
        ))

    # 7. Hybrid Core to Cloud Gateways
    links.append(TopologyLink(id="l-spine01-cgw01", source_node="spine-dc-01", target_node="cloud-gw-01", source_interface="eth10", target_interface="eth0"))
    links.append(TopologyLink(id="l-spine02-cgw02", source_node="spine-dc-02", target_node="cloud-gw-02", source_interface="eth10", target_interface="eth0"))

    # 8. Cloud Services to Cloud Gateways
    for cs in range(1, 5):
        cgw_id = "cloud-gw-01" if cs <= 2 else "cloud-gw-02"
        links.append(TopologyLink(
            id=f"l-csvc0{cs}-{cgw_id}",
            source_node=f"cloud-svc-0{cs}",
            target_node=cgw_id,
            source_interface="eth0",
            target_interface=f"eth{cs}"
        ))

    services = [
        TopologyService(id="svc-iot-analytics", name="Real-Time Telemetry Analytics Engine", hosted_on="app-svc-01", port=9092),
        TopologyService(id="svc-cloud-sync", name="Hybrid Cloud Database Sync", hosted_on="db-svc-01", port=5432),
        TopologyService(id="svc-edge-dns", name="Edge Resolver Cache", hosted_on="edge-gw-01", port=53),
    ]

    fault = FaultDefinition(
        fault_type="NOVEL_COMPOSITE_ANOMALY",
        target_element="edge-gw-01 + wan-rtr-01 + cloud-gw-01",
        description="Composite cross-domain degradation: edge gateway CPU overload, DNS cache contention, BGP route metric shift, and WAN micro-burst congestion.",
        causal_chain=[
            "edge-gw-01 DNS cache lock contention elevates CPU utilization to 58%",
            "Edge resolver response time increases from 2ms to 140ms",
            "BGP route metric drift shifts cloud sync traffic from cloud-gw-01 to secondary WAN circuit",
            "WAN RTT rises to 85ms and packet loss increases to 7.5%",
            "TCP connection resets surge across hybrid cloud workers",
            "End-to-end IoT analytics transaction latency increases to 190ms"
        ]
    )

    remed = RemediationCandidate(
        action_id="act-case04-remed",
        command_type="RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE",
        target_device="edge-gw-01",
        parameters={
            "service": "dns-resolver",
            "target_gateway": "edge-gw-01",
            "action": "FLUSH_DNS_CACHE_AND_RESTORE_BGP_LOCAL_PREF",
            "bgp_neighbor": "cloud-gw-01",
            "local_pref": 200
        },
        reversion_action={
            "target_gateway": "edge-gw-01",
            "action": "SET_BGP_LOCAL_PREF",
            "local_pref": 50
        },
        description="Flush edge resolver DNS cache lock and restore BGP local preference on edge-gw-01 towards cloud-gw-01.",
        is_destructive=True
    )

    return ScenarioDefinition(
        scenario_id="CASE_04",
        name="Hybrid Edge / Data Center / Cloud",
        description="Complex 48-node hybrid cloud/edge mesh experiencing a novel composite cross-layer anomaly requiring LLM escalation.",
        category="Hybrid Cloud Composite Anomaly",
        target_node_count=48,
        target_link_count=len(links),
        nodes=nodes,
        links=links,
        services=services,
        fault_definition=fault,
        expected_fault_domain="Hybrid Edge/Cloud Overlay",
        expected_behavior="Rule engine returns LOW_CONFIDENCE (< 0.70) UNKNOWN_COMPOSITE_ANOMALY, triggering LLM escalation for reasoning.",
        remediation_candidates=[remed],
        verification_criteria={"max_rtt_ms": 15.0, "max_packet_loss_pct": 1.0, "max_dns_latency_ms": 5.0},
        llm_escalation_required=True,
        llm_confidence_threshold=0.70
    )

def generate_case04_telemetry(active_fault: str) -> NetworkState:
    now = datetime.now(timezone.utc)
    is_fault = (active_fault == "NOVEL_COMPOSITE_ANOMALY")

    nodes = {
        "edge-gw-01": NodeMetrics(node_id="edge-gw-01", cpu_utilization_pct=58.0 if is_fault else 12.0, memory_utilization_pct=48.0),
        "wan-rtr-01": NodeMetrics(node_id="wan-rtr-01", cpu_utilization_pct=45.0 if is_fault else 18.0, memory_utilization_pct=35.0),
        "cloud-gw-01": NodeMetrics(node_id="cloud-gw-01", cpu_utilization_pct=40.0 if is_fault else 15.0, memory_utilization_pct=32.0),
        "app-svc-01": NodeMetrics(node_id="app-svc-01", cpu_utilization_pct=62.0 if is_fault else 14.0, memory_utilization_pct=41.0),
    }

    interfaces = {
        "edge-gw-01-wan0": InterfaceState(
            name="edge-gw-01-wan0",
            is_up=True,
            ip_addresses=["172.20.1.1/30"],
            mac_address="52:54:00:40:01:01",
            rx_bytes=15240000,
            tx_bytes=15240000,
            rx_errors=85 if is_fault else 0,
            rx_drops=340 if is_fault else 0,
            throughput_bps=75000000.0 if is_fault else 15000000.0,
            utilization_pct=75.0 if is_fault else 15.0,
            mtu=1500
        ),
        "cloud-gw-01-eth0": InterfaceState(
            name="cloud-gw-01-eth0",
            is_up=True,
            ip_addresses=["10.99.1.1/30"],
            mac_address="52:54:00:40:01:10",
            rx_bytes=20000000,
            tx_bytes=20000000,
            rx_errors=12,
            throughput_bps=30000000.0,
            utilization_pct=30.0,
            mtu=1500
        )
    }

    links = [
        LinkLatency(
            source_node="edge-gw-01",
            target_node="wan-rtr-01",
            rtt_ms=85.0 if is_fault else 3.5,
            packet_loss_pct=7.5 if is_fault else 0.0,
            status="DEGRADED" if is_fault else "HEALTHY"
        ),
        LinkLatency(
            source_node="wan-rtr-01",
            target_node="cloud-gw-01",
            rtt_ms=45.0 if is_fault else 8.0,
            packet_loss_pct=3.2 if is_fault else 0.0,
            status="DEGRADED" if is_fault else "HEALTHY"
        ),
        LinkLatency(source_node="cloud-gw-01", target_node="cloud-svc-01", rtt_ms=1.2, packet_loss_pct=0.0, status="HEALTHY")
    ]

    routes = [
        RouteEntry(
            destination="10.99.10.0/24",
            gateway="172.20.1.2",
            interface="edge-gw-01-wan0",
            metric=150 if is_fault else 10
        )
    ]

    return NetworkState(
        snapshot_id="snap-case04",
        timestamp=now,
        topology_id="CASE_04",
        interfaces=interfaces,
        links=links,
        routes=routes,
        nodes=nodes,
        anomalies_detected=is_fault
    )
