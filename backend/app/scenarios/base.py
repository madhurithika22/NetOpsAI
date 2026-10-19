from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics

class TopologyNode(BaseModel):
    id: str
    name: str
    role: str  # e.g. access_switch, dist_switch, core_router, firewall, wan_router, server, service
    layer: str  # access, distribution, core, edge, dc, cloud
    status: str = "UP"
    ip_address: Optional[str] = None

class TopologyLink(BaseModel):
    id: str
    source_node: str
    target_node: str
    source_interface: str
    target_interface: str
    bandwidth_mbps: float = 1000.0
    latency_ms: float = 2.0
    status: str = "HEALTHY"

class TopologyService(BaseModel):
    id: str
    name: str
    hosted_on: str
    port: int
    protocol: str = "TCP"
    status: str = "HEALTHY"

class FaultDefinition(BaseModel):
    fault_type: str
    target_element: str
    description: str
    causal_chain: List[str] = Field(default_factory=list)

class RemediationCandidate(BaseModel):
    action_id: str
    command_type: str
    target_device: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reversion_action: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    is_destructive: bool = True

class ScenarioDefinition(BaseModel):
    scenario_id: str
    name: str
    description: str
    category: str
    target_node_count: int
    target_link_count: int
    nodes: List[TopologyNode] = Field(default_factory=list)
    links: List[TopologyLink] = Field(default_factory=list)
    services: List[TopologyService] = Field(default_factory=list)
    fault_definition: FaultDefinition
    expected_fault_domain: str
    expected_behavior: str
    remediation_candidates: List[RemediationCandidate] = Field(default_factory=list)
    verification_criteria: Dict[str, Any] = Field(default_factory=dict)
    llm_escalation_required: bool = False
    llm_confidence_threshold: float = 0.70
