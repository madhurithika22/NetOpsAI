from datetime import datetime, timezone
from typing import Dict, List, Tuple
from app.scenarios.base import (
    ScenarioDefinition, TopologyNode, TopologyLink, TopologyService,
    FaultDefinition, RemediationCandidate
)
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics

def get_case01_enterprise_scenario() -> ScenarioDefinition:
    # 20 Nodes:
    # Access: acc-sw01, acc-sw02, acc-sw03, acc-sw04 (4)
    # Distribution: dist-sw01, dist-sw02, dist-sw03, dist-sw04 (4)
    # Core: core-rtr01, core-rtr02, core-rtr03, core-rtr04 (4)
    # Firewall: fw-edge01, fw-edge02 (2)
    # WAN: wan-rtr01, wan-rtr02 (2)
    # Servers: srv-app01, srv-db01 (2)
    # Services: dns-primary, auth-radius (2)
    
    nodes = [
        TopologyNode(id="acc-sw01", name="Access Switch 1", role="access_switch", layer="access", ip_address="10.10.1.1"),
        TopologyNode(id="acc-sw02", name="Access Switch 2", role="access_switch", layer="access", ip_address="10.10.1.2"),
        TopologyNode(id="acc-sw03", name="Access Switch 3", role="access_switch", layer="access", ip_address="10.10.1.3"),
        TopologyNode(id="acc-sw04", name="Access Switch 4", role="access_switch", layer="access", ip_address="10.10.1.4"),
        TopologyNode(id="dist-sw01", name="Dist Switch 1", role="dist_switch", layer="distribution", ip_address="10.10.2.1"),
        TopologyNode(id="dist-sw02", name="Dist Switch 2", role="dist_switch", layer="distribution", ip_address="10.10.2.2"),
        TopologyNode(id="dist-sw03", name="Dist Switch 3", role="dist_switch", layer="distribution", ip_address="10.10.2.3"),
        TopologyNode(id="dist-sw04", name="Dist Switch 4", role="dist_switch", layer="distribution", ip_address="10.10.2.4"),
        TopologyNode(id="core-rtr01", name="Core Router 1", role="core_router", layer="core", ip_address="10.10.3.1"),
        TopologyNode(id="core-rtr02", name="Core Router 2", role="core_router", layer="core", ip_address="10.10.3.2"),
        TopologyNode(id="core-rtr03", name="Core Router 3", role="core_router", layer="core", ip_address="10.10.3.3"),
        TopologyNode(id="core-rtr04", name="Core Router 4", role="core_router", layer="core", ip_address="10.10.3.4"),
        TopologyNode(id="fw-edge01", name="Firewall Edge 1", role="firewall", layer="edge", ip_address="10.10.4.1"),
        TopologyNode(id="fw-edge02", name="Firewall Edge 2", role="firewall", layer="edge", ip_address="10.10.4.2"),
        TopologyNode(id="wan-rtr01", name="WAN Edge Router 1", role="wan_router", layer="edge", ip_address="10.10.5.1"),
        TopologyNode(id="wan-rtr02", name="WAN Edge Router 2", role="wan_router", layer="edge", ip_address="10.10.5.2"),
        TopologyNode(id="srv-app01", name="App Server 1", role="server", layer="services", ip_address="10.10.6.10"),
        TopologyNode(id="srv-db01", name="DB Server 1", role="server", layer="services", ip_address="10.10.6.20"),
        TopologyNode(id="dns-primary", name="Primary DNS Service", role="service", layer="services", ip_address="10.10.6.53"),
        TopologyNode(id="auth-radius", name="RADIUS Auth Service", role="service", layer="services", ip_address="10.10.6.181"),
    ]

    links = []
    # Access to Dist
    links.append(TopologyLink(id="l-acc1-dist1", source_node="acc-sw01", target_node="dist-sw01", source_interface="eth0", target_interface="eth1"))
    links.append(TopologyLink(id="l-acc2-dist2", source_node="acc-sw02", target_node="dist-sw02", source_interface="eth0", target_interface="eth1"))
    links.append(TopologyLink(id="l-acc3-dist3", source_node="acc-sw03", target_node="dist-sw03", source_interface="eth0", target_interface="eth1"))
    links.append(TopologyLink(id="l-acc4-dist4", source_node="acc-sw04", target_node="dist-sw04", source_interface="eth0", target_interface="eth1"))
    # Dist to Core
    links.append(TopologyLink(id="l-dist1-core1", source_node="dist-sw01", target_node="core-rtr01", source_interface="eth2", target_interface="eth1"))
    links.append(TopologyLink(id="l-dist2-core2", source_node="dist-sw02", target_node="core-rtr02", source_interface="eth2", target_interface="eth1"))
    links.append(TopologyLink(id="l-dist3-core3", source_node="dist-sw03", target_node="core-rtr03", source_interface="eth2", target_interface="eth1"))
    links.append(TopologyLink(id="l-dist4-core4", source_node="dist-sw04", target_node="core-rtr04", source_interface="eth2", target_interface="eth1"))
    # Core Interconnect mesh
    links.append(TopologyLink(id="l-core1-core2", source_node="core-rtr01", target_node="core-rtr02", source_interface="eth2", target_interface="eth2"))
    links.append(TopologyLink(id="l-core2-core3", source_node="core-rtr02", target_node="core-rtr03", source_interface="eth3", target_interface="eth2"))
    links.append(TopologyLink(id="l-core3-core4", source_node="core-rtr03", target_node="core-rtr04", source_interface="eth3", target_interface="eth2"))
    links.append(TopologyLink(id="l-core4-core1", source_node="core-rtr04", target_node="core-rtr01", source_interface="eth3", target_interface="eth3"))
    # Core to FW / WAN / Services
    links.append(TopologyLink(id="l-core1-fw1", source_node="core-rtr01", target_node="fw-edge01", source_interface="eth4", target_interface="eth1"))
    links.append(TopologyLink(id="l-core2-fw2", source_node="core-rtr02", target_node="fw-edge02", source_interface="eth4", target_interface="eth1"))
    links.append(TopologyLink(id="l-fw1-wan1", source_node="fw-edge01", target_node="wan-rtr01", source_interface="eth2", target_interface="eth1"))
    links.append(TopologyLink(id="l-fw2-wan2", source_node="fw-edge02", target_node="wan-rtr02", source_interface="eth2", target_interface="eth1"))
    links.append(TopologyLink(id="l-core3-srv1", source_node="core-rtr03", target_node="srv-app01", source_interface="eth4", target_interface="eth0"))
    links.append(TopologyLink(id="l-core3-srv2", source_node="core-rtr03", target_node="srv-db01", source_interface="eth5", target_interface="eth0"))
    links.append(TopologyLink(id="l-core4-dns", source_node="core-rtr04", target_node="dns-primary", source_interface="eth4", target_interface="eth0"))
    links.append(TopologyLink(id="l-core4-auth", source_node="core-rtr04", target_node="auth-radius", source_interface="eth5", target_interface="eth0"))

    services = [
        TopologyService(id="svc-dns", name="DNS Service", hosted_on="dns-primary", port=53),
        TopologyService(id="svc-auth", name="RADIUS Auth", hosted_on="auth-radius", port=1812),
        TopologyService(id="svc-web", name="Enterprise Web App", hosted_on="srv-app01", port=443),
        TopologyService(id="svc-db", name="PostgreSQL Cluster", hosted_on="srv-db01", port=5432),
    ]

    fault = FaultDefinition(
        fault_type="OSPF_ADJACENCY_INSTABILITY",
        target_element="core-rtr01<->core-rtr02",
        description="OSPF adjacency flap on core link between core-rtr01 and core-rtr02 caused by MTU/timer mismatch, causing asymmetric routing and packet loss.",
        causal_chain=[
            "MTU mismatch / hello timer mismatch configured on core-rtr01 eth2",
            "OSPF neighbor state oscillates between EXSTART and DOWN",
            "Core routing table repeatedly flaps back and forth",
            "Traffic between dist-sw01 and core-rtr02 experiences asymmetric drops",
            "RTT increases to 160ms on core path, packet loss rises to 18%",
            "Enterprise Web App response times degrade"
        ]
    )

    remed = RemediationCandidate(
        action_id="act-case01-remed",
        command_type="RESET_OSPF_NEIGHBOR_AND_METRIC",
        target_device="core-rtr01",
        parameters={
            "interface": "eth2",
            "action": "RESTORE_OSPF_TIMERS_AND_METRIC",
            "hello_interval": 10,
            "cost": 10
        },
        reversion_action={
            "interface": "eth2",
            "action": "INJECT_OSPF_TIMER_MISMATCH",
            "hello_interval": 40
        },
        description="Restore OSPF hello timers and interface cost on core-rtr01 eth2 to re-establish stable FULL adjacency.",
        is_destructive=True
    )

    return ScenarioDefinition(
        scenario_id="CASE_01",
        name="Enterprise Campus + Core",
        description="Hierarchical 20-node enterprise network experiencing core OSPF adjacency instability and asymmetric routing.",
        category="Enterprise Core Routing",
        target_node_count=20,
        target_link_count=len(links),
        nodes=nodes,
        links=links,
        services=services,
        fault_definition=fault,
        expected_fault_domain="Core Routing Layer (OSPF)",
        expected_behavior="CADD identifies OSPF neighbor state oscillation and asymmetric path cost on core-rtr01.",
        remediation_candidates=[remed],
        verification_criteria={"max_rtt_ms": 10.0, "max_packet_loss_pct": 1.0, "ospf_state": "FULL"},
        llm_escalation_required=False,
        llm_confidence_threshold=0.70
    )

def generate_case01_telemetry(active_fault: str) -> NetworkState:
    now = datetime.now(timezone.utc)
    is_fault = (active_fault == "OSPF_ADJACENCY_INSTABILITY")
    
    nodes = {
        "core-rtr01": NodeMetrics(node_id="core-rtr01", cpu_utilization_pct=78.5 if is_fault else 22.0, memory_utilization_pct=45.0),
        "core-rtr02": NodeMetrics(node_id="core-rtr02", cpu_utilization_pct=65.0 if is_fault else 19.0, memory_utilization_pct=41.0),
        "core-rtr03": NodeMetrics(node_id="core-rtr03", cpu_utilization_pct=25.0, memory_utilization_pct=38.0),
        "core-rtr04": NodeMetrics(node_id="core-rtr04", cpu_utilization_pct=24.0, memory_utilization_pct=37.0),
        "dist-sw01": NodeMetrics(node_id="dist-sw01", cpu_utilization_pct=15.0, memory_utilization_pct=30.0),
    }

    interfaces = {
        "core-rtr01-eth2": InterfaceState(
            name="core-rtr01-eth2",
            is_up=True,
            ip_addresses=["10.10.3.1/30"],
            mac_address="52:54:00:10:03:01",
            rx_bytes=10485760 if is_fault else 5242880,
            tx_bytes=10485760 if is_fault else 5242880,
            rx_errors=142 if is_fault else 0,
            tx_errors=38 if is_fault else 0,
            rx_drops=210 if is_fault else 0,
            throughput_bps=8500000.0 if is_fault else 1200000.0,
            utilization_pct=85.0 if is_fault else 12.0,
            mtu=1500
        ),
        "core-rtr02-eth2": InterfaceState(
            name="core-rtr02-eth2",
            is_up=True,
            ip_addresses=["10.10.3.2/30"],
            mac_address="52:54:00:10:03:02",
            rx_bytes=5242880,
            tx_bytes=5242880,
            rx_errors=18 if is_fault else 0,
            throughput_bps=1200000.0,
            utilization_pct=12.0,
            mtu=1500
        )
    }

    links = [
        LinkLatency(source_node="dist-sw01", target_node="core-rtr01", rtt_ms=2.1, packet_loss_pct=0.0, status="HEALTHY"),
        LinkLatency(
            source_node="core-rtr01",
            target_node="core-rtr02",
            rtt_ms=162.5 if is_fault else 3.8,
            packet_loss_pct=18.5 if is_fault else 0.0,
            status="DEGRADED" if is_fault else "HEALTHY"
        ),
        LinkLatency(source_node="core-rtr02", target_node="core-rtr03", rtt_ms=4.1, packet_loss_pct=0.0, status="HEALTHY"),
        LinkLatency(source_node="core-rtr03", target_node="srv-app01", rtt_ms=1.8, packet_loss_pct=0.0, status="HEALTHY"),
    ]

    routes = [
        RouteEntry(destination="10.10.6.0/24", gateway="10.10.3.2", interface="core-rtr01-eth2", metric=999 if is_fault else 10),
        RouteEntry(destination="10.10.1.0/24", gateway="10.10.2.1", interface="core-rtr01-eth1", metric=10)
    ]

    return NetworkState(
        snapshot_id="snap-case01",
        timestamp=now,
        topology_id="CASE_01",
        interfaces=interfaces,
        links=links,
        routes=routes,
        nodes=nodes,
        anomalies_detected=is_fault
    )
