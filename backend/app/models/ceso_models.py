from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timezone

class InterfaceState(BaseModel):
    name: str = Field(..., description="Interface name e.g. eth0, rtr1-eth1")
    is_up: bool = Field(True, description="Interface link status")
    ip_addresses: List[str] = Field(default_factory=list, description="IP addresses assigned")
    mac_address: str = Field("00:00:00:00:00:00", description="MAC address")
    rx_bytes: int = Field(0, description="Received bytes")
    tx_bytes: int = Field(0, description="Transmitted bytes")
    rx_errors: int = Field(0, description="RX error count")
    tx_errors: int = Field(0, description="TX error count")
    rx_drops: int = Field(0, description="RX dropped packet count")
    tx_drops: int = Field(0, description="TX dropped packet count")
    throughput_bps: float = Field(0.0, description="Interface throughput in bits per second")
    utilization_pct: float = Field(0.0, description="Interface bandwidth utilization percentage")
    mtu: int = Field(1500, description="MTU size")

class LinkLatency(BaseModel):
    source_node: str = Field(..., description="Source node ID")
    target_node: str = Field(..., description="Target node ID")
    rtt_ms: float = Field(..., description="Round-trip time in milliseconds")
    packet_loss_pct: float = Field(0.0, description="Packet loss percentage")
    status: str = Field("HEALTHY", description="Link health status e.g. HEALTHY, DEGRADED, UNREACHABLE")

class RouteEntry(BaseModel):
    destination: str = Field(..., description="Destination CIDR e.g. 10.0.1.0/24")
    gateway: Optional[str] = Field(None, description="Gateway IP address")
    interface: str = Field(..., description="Egress interface name")
    metric: int = Field(100, description="Routing metric cost")

class NodeMetrics(BaseModel):
    node_id: str = Field(..., description="Node or router ID e.g. rtr1, hostA")
    cpu_utilization_pct: float = Field(15.0, description="CPU utilization percentage")
    memory_utilization_pct: float = Field(35.0, description="RAM utilization percentage")

class NetworkState(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Snapshot timestamp")
    topology_id: str = Field("sim-3node-mesh", description="Topology identifier")
    interfaces: Dict[str, InterfaceState] = Field(default_factory=dict, description="Interface states by interface name")
    links: List[LinkLatency] = Field(default_factory=list, description="Link health metrics")
    routes: List[RouteEntry] = Field(default_factory=list, description="Active route entries")
    nodes: Dict[str, NodeMetrics] = Field(default_factory=dict, description="Node resource metrics")
    anomalies_detected: bool = Field(False, description="Flag indicating anomaly detected by CESO")
