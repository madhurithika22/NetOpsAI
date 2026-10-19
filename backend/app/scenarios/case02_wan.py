from datetime import datetime, timezone
from typing import Dict, List
from app.scenarios.base import (
    ScenarioDefinition, TopologyNode, TopologyLink, TopologyService,
    FaultDefinition, RemediationCandidate
)
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics

def get_case02_wan_scenario() -> ScenarioDefinition:
    nodes = []
    for b in range(1, 5):
        nodes.append(TopologyNode(id=f"br{b}-edge", name=f"Branch {b} Edge Router", role="wan_router", layer="edge", ip_address=f"172.16.{b}.1"))
        nodes.append(TopologyNode(id=f"br{b}-lan", name=f"Branch {b} LAN Switch", role="access_switch", layer="access", ip_address=f"172.16.{b}.2"))
        nodes.append(TopologyNode(id=f"br{b}-client", name=f"Branch {b} Client Host", role="client", layer="access", ip_address=f"172.16.{b}.100"))

    nodes.extend([
        TopologyNode(id="isp-prim-rtr1", name="Primary ISP Edge 1", role="isp_router", layer="edge", ip_address="198.51.100.1"),
        TopologyNode(id="isp-prim-rtr2", name="Primary ISP Edge 2", role="isp_router", layer="edge", ip_address="198.51.100.2"),
        TopologyNode(id="isp-sec-rtr1", name="Secondary ISP Edge 1", role="isp_router", layer="edge", ip_address="203.0.113.1"),
        TopologyNode(id="isp-sec-rtr2", name="Secondary ISP Edge 2", role="isp_router", layer="edge", ip_address="203.0.113.2"),
        TopologyNode(id="sdwan-ctrl01", name="SD-WAN Controller Primary", role="sdwan_controller", layer="core", ip_address="10.200.1.1"),
        TopologyNode(id="sdwan-ctrl02", name="SD-WAN Controller Secondary", role="sdwan_controller", layer="core", ip_address="10.200.1.2"),
        TopologyNode(id="dc-gw01", name="DC Gateway 1", role="core_router", layer="core", ip_address="10.200.2.1"),
        TopologyNode(id="dc-gw02", name="DC Gateway 2", role="core_router", layer="core", ip_address="10.200.2.2"),
        TopologyNode(id="dc-fw01", name="DC Firewall 1", role="firewall", layer="edge", ip_address="10.200.3.1"),
        TopologyNode(id="dc-fw02", name="DC Firewall 2", role="firewall", layer="edge", ip_address="10.200.3.2"),
        TopologyNode(id="app-srv-dc1", name="ERP Web Server 1", role="server", layer="services", ip_address="10.200.4.10"),
        TopologyNode(id="app-srv-dc2", name="ERP Web Server 2", role="server", layer="services", ip_address="10.200.4.11"),
        TopologyNode(id="db-srv-dc1", name="Oracle DB 1", role="server", layer="services", ip_address="10.200.4.20"),
        TopologyNode(id="db-srv-dc2", name="Oracle DB 2", role="server", layer="services", ip_address="10.200.4.21"),
        TopologyNode(id="cloud-gw01", name="AWS DirectConnect GW 1", role="cloud_gateway", layer="cloud", ip_address="10.250.1.1"),
        TopologyNode(id="cloud-gw02", name="Azure ExpressRoute GW 2", role="cloud_gateway", layer="cloud", ip_address="10.250.2.1"),
    ])

    links = []
    # Branch internal links & dual ISP connectivity
    for b in range(1, 5):
        links.append(TopologyLink(id=f"l-br{b}-c-l", source_node=f"br{b}-client", target_node=f"br{b}-lan", source_interface="eth0", target_interface="eth1"))
        links.append(TopologyLink(id=f"l-br{b}-l-e", source_node=f"br{b}-lan", target_node=f"br{b}-edge", source_interface="eth0", target_interface="eth1"))
        links.append(TopologyLink(id=f"l-br{b}-isp-p1", source_node=f"br{b}-edge", target_node="isp-prim-rtr1", source_interface="wan0", target_interface=f"eth{b}"))
        links.append(TopologyLink(id=f"l-br{b}-isp-s1", source_node=f"br{b}-edge", target_node="isp-sec-rtr1", source_interface="wan1", target_interface=f"eth{b}"))

    # Redundant ISP Edge Mesh
    links.append(TopologyLink(id="l-isp-p1-p2", source_node="isp-prim-rtr1", target_node="isp-prim-rtr2", source_interface="eth0", target_interface="eth0"))
    links.append(TopologyLink(id="l-isp-s1-s2", source_node="isp-sec-rtr1", target_node="isp-sec-rtr2", source_interface="eth0", target_interface="eth0"))

    # WAN to DC Gateways
    links.append(TopologyLink(id="l-isp-p1-dc1", source_node="isp-prim-rtr1", target_node="dc-gw01", source_interface="eth10", target_interface="wan0"))
    links.append(TopologyLink(id="l-isp-p2-dc2", source_node="isp-prim-rtr2", target_node="dc-gw02", source_interface="eth10", target_interface="wan0"))
    links.append(TopologyLink(id="l-isp-s1-dc2", source_node="isp-sec-rtr1", target_node="dc-gw02", source_interface="eth10", target_interface="wan1"))
    links.append(TopologyLink(id="l-isp-s2-dc1", source_node="isp-sec-rtr2", target_node="dc-gw01", source_interface="eth10", target_interface="wan1"))

    # SD-WAN Controllers to DC Core
    links.append(TopologyLink(id="l-sdwan1-dc1", source_node="sdwan-ctrl01", target_node="dc-gw01", source_interface="eth0", target_interface="eth2"))
    links.append(TopologyLink(id="l-sdwan2-dc2", source_node="sdwan-ctrl02", target_node="dc-gw02", source_interface="eth0", target_interface="eth2"))

    # DC Inter-Gateway link
    links.append(TopologyLink(id="l-dc1-dc2", source_node="dc-gw01", target_node="dc-gw02", source_interface="eth3", target_interface="eth3"))

    # DC Gateways to Firewalls
    links.append(TopologyLink(id="l-dc-gw1-fw1", source_node="dc-gw01", target_node="dc-fw01", source_interface="eth4", target_interface="eth1"))
    links.append(TopologyLink(id="l-dc-gw2-fw2", source_node="dc-gw02", target_node="dc-fw02", source_interface="eth4", target_interface="eth1"))

    # DC Firewalls to Servers
    links.append(TopologyLink(id="l-dc-fw1-app1", source_node="dc-fw01", target_node="app-srv-dc1", source_interface="eth2", target_interface="eth0"))
    links.append(TopologyLink(id="l-dc-fw1-app2", source_node="dc-fw01", target_node="app-srv-dc2", source_interface="eth3", target_interface="eth0"))
    links.append(TopologyLink(id="l-dc-fw2-db1", source_node="dc-fw02", target_node="db-srv-dc1", source_interface="eth2", target_interface="eth0"))
    links.append(TopologyLink(id="l-dc-fw2-db2", source_node="dc-fw02", target_node="db-srv-dc2", source_interface="eth3", target_interface="eth0"))

    # Cloud Gateways to DC Gateways
    links.append(TopologyLink(id="l-dc1-cgw1", source_node="dc-gw01", target_node="cloud-gw01", source_interface="eth5", target_interface="eth0"))
    links.append(TopologyLink(id="l-dc2-cgw2", source_node="dc-gw02", target_node="cloud-gw02", source_interface="eth5", target_interface="eth0"))

    services = [
        TopologyService(id="svc-erp", name="Enterprise ERP Suite", hosted_on="app-srv-dc1", port=443),
        TopologyService(id="svc-oracle", name="Oracle Financial DB", hosted_on="db-srv-dc1", port=1521),
    ]

    fault = FaultDefinition(
        fault_type="WAN_PATH_DEGRADATION_AND_CONGESTION",
        target_element="isp-prim-rtr1<->dc-gw01",
        description="Primary ISP circuit packet loss forces SD-WAN traffic steering to secondary path, inducing heavy congestion and secondary queue latency on backup link.",
        causal_chain=[
            "ISP Primary link experiences fiber micro-bends resulting in 22% packet loss",
            "SD-WAN controller detects SLA breach (RTT > 120ms, Loss > 15%)",
            "SD-WAN controller triggers dynamic path failover to Secondary ISP link",
            "All branch traffic shifts simultaneously to Secondary ISP circuit",
            "Secondary link utilization spikes to 96.5% bandwidth limit",
            "Buffer tail-drop congestion on dc-gw02 wan1 causes end-to-end ERP application latency spike (245ms)"
        ]
    )

    remed = RemediationCandidate(
        action_id="act-case02-remed",
        command_type="APPLY_SDWAN_QOS_TRAFFIC_SHAPING",
        target_device="dc-gw02",
        parameters={
            "interface": "wan1",
            "action": "ENABLE_TRAFFIC_SHAPING_AND_RATE_LIMIT",
            "high_priority_class": "ERP_BUSINESS_CRITICAL",
            "rate_limit_bulk_pct": 20
        },
        reversion_action={
            "interface": "wan1",
            "action": "DISABLE_QOS_SHAPING"
        },
        description="Apply SD-WAN QoS traffic shaping on dc-gw02 wan1 to prioritize critical ERP application traffic over bulk data.",
        is_destructive=True
    )

    return ScenarioDefinition(
        scenario_id="CASE_02",
        name="Multi-Site WAN / SD-WAN",
        description="Multi-site enterprise WAN topology with SD-WAN dynamic path failover and backup circuit queue congestion.",
        category="SD-WAN / WAN Failover",
        target_node_count=28,
        target_link_count=len(links),
        nodes=nodes,
        links=links,
        services=services,
        fault_definition=fault,
        expected_fault_domain="WAN Edge & Secondary Path Congestion",
        expected_behavior="CADD correlates primary ISP SLA breach with secondary path overflow and recommends QoS traffic shaping.",
        remediation_candidates=[remed],
        verification_criteria={"max_rtt_ms": 30.0, "max_packet_loss_pct": 2.0, "secondary_link_util_max_pct": 75.0},
        llm_escalation_required=False,
        llm_confidence_threshold=0.70
    )

def generate_case02_telemetry(active_fault: str) -> NetworkState:
    now = datetime.now(timezone.utc)
    is_fault = (active_fault == "WAN_PATH_DEGRADATION_AND_CONGESTION")

    nodes = {
        "dc-gw01": NodeMetrics(node_id="dc-gw01", cpu_utilization_pct=42.0, memory_utilization_pct=50.0),
        "dc-gw02": NodeMetrics(node_id="dc-gw02", cpu_utilization_pct=91.0 if is_fault else 28.0, memory_utilization_pct=62.0),
        "sdwan-ctrl01": NodeMetrics(node_id="sdwan-ctrl01", cpu_utilization_pct=35.0, memory_utilization_pct=40.0),
        "br1-edge": NodeMetrics(node_id="br1-edge", cpu_utilization_pct=22.0, memory_utilization_pct=30.0),
    }

    interfaces = {
        "dc-gw01-wan0": InterfaceState(
            name="dc-gw01-wan0",
            is_up=True,
            ip_addresses=["198.51.100.254/30"],
            mac_address="52:54:00:20:01:01",
            rx_bytes=1024000,
            tx_bytes=1024000,
            rx_errors=450 if is_fault else 0,
            rx_drops=890 if is_fault else 0,
            throughput_bps=50000.0 if is_fault else 50000000.0,
            utilization_pct=5.0 if is_fault else 50.0,
            mtu=1500
        ),
        "dc-gw02-wan1": InterfaceState(
            name="dc-gw02-wan1",
            is_up=True,
            ip_addresses=["203.0.113.254/30"],
            mac_address="52:54:00:20:01:02",
            rx_bytes=98000000 if is_fault else 10240000,
            tx_bytes=98000000 if is_fault else 10240000,
            rx_errors=12,
            rx_drops=1450 if is_fault else 0,
            throughput_bps=96500000.0 if is_fault else 10000000.0,
            utilization_pct=96.5 if is_fault else 10.0,
            mtu=1500
        )
    }

    links = [
        LinkLatency(
            source_node="isp-prim-rtr1",
            target_node="dc-gw01",
            rtt_ms=185.0 if is_fault else 12.0,
            packet_loss_pct=22.5 if is_fault else 0.0,
            status="DEGRADED" if is_fault else "HEALTHY"
        ),
        LinkLatency(
            source_node="isp-sec-rtr1",
            target_node="dc-gw02",
            rtt_ms=145.0 if is_fault else 18.0,
            packet_loss_pct=8.5 if is_fault else 0.0,
            status="DEGRADED" if is_fault else "HEALTHY"
        ),
        LinkLatency(source_node="br1-edge", target_node="isp-prim-rtr1", rtt_ms=5.0, packet_loss_pct=0.0, status="HEALTHY"),
        LinkLatency(source_node="dc-gw02", target_node="app-srv-dc1", rtt_ms=1.5, packet_loss_pct=0.0, status="HEALTHY")
    ]

    routes = [
        RouteEntry(
            destination="10.200.0.0/16",
            gateway="203.0.113.254" if is_fault else "198.51.100.254",
            interface="dc-gw02-wan1" if is_fault else "dc-gw01-wan0",
            metric=5 if is_fault else 10
        )
    ]

    return NetworkState(
        snapshot_id="snap-case02",
        timestamp=now,
        topology_id="CASE_02",
        interfaces=interfaces,
        links=links,
        routes=routes,
        nodes=nodes,
        anomalies_detected=is_fault
    )
