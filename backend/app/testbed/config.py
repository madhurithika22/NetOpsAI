from pydantic import BaseModel, Field
from typing import Dict, List, Optional

TESTBED_PREFIX = "netops-"
PROTECTED_HOST_INTERFACES = {"eth0", "wlan0", "lo", "mgmt0", "docker0"}

class VethPair(BaseModel):
    name_ns1: str = Field(..., description="Interface name inside first namespace e.g. veth-hA-r1")
    name_ns2: str = Field(..., description="Interface name inside second namespace e.g. veth-r1-hA")
    ns1: str = Field(..., description="Namespace 1 name e.g. netops-hosta")
    ns2: str = Field(..., description="Namespace 2 name e.g. netops-rtr1")
    ip_ns1: str = Field(..., description="IP address inside ns1 e.g. 10.0.1.10/24")
    ip_ns2: str = Field(..., description="IP address inside ns2 e.g. 10.0.1.1/24")

class NamespaceConfig(BaseModel):
    name: str = Field(..., description="Full namespace name e.g. netops-hosta")
    is_router: bool = Field(False, description="Flag indicating if IPv4 forwarding is enabled")
    static_routes: List[Dict[str, str]] = Field(default_factory=list, description="Static routes e.g. {'dest': '10.0.3.0/24', 'via': '10.0.1.1'}")

class TestbedTopologyConfig(BaseModel):
    topology_name: str = "netops-isolated-4node"
    prefix: str = TESTBED_PREFIX
    namespaces: Dict[str, NamespaceConfig] = Field(default_factory=dict)
    veth_pairs: List[VethPair] = Field(default_factory=list)

def get_default_testbed_config() -> TestbedTopologyConfig:
    """Returns baseline 4-node topology (HostA <-> Router1 <-> Router2 <-> HostB)."""
    namespaces = {
        "netops-hosta": NamespaceConfig(
            name="netops-hosta",
            is_router=False,
            static_routes=[{"destination": "10.0.2.0/24", "via": "10.0.1.1"}, {"destination": "10.0.3.0/24", "via": "10.0.1.1"}]
        ),
        "netops-rtr1": NamespaceConfig(
            name="netops-rtr1",
            is_router=True,
            static_routes=[{"destination": "10.0.3.0/24", "via": "10.0.2.2"}]
        ),
        "netops-rtr2": NamespaceConfig(
            name="netops-rtr2",
            is_router=True,
            static_routes=[{"destination": "10.0.1.0/24", "via": "10.0.2.1"}]
        ),
        "netops-hostb": NamespaceConfig(
            name="netops-hostb",
            is_router=False,
            static_routes=[{"destination": "10.0.1.0/24", "via": "10.0.3.1"}, {"destination": "10.0.2.0/24", "via": "10.0.3.1"}]
        ),
    }

    veth_pairs = [
        VethPair(name_ns1="veth-ha-r1", name_ns2="veth-r1-ha", ns1="netops-hosta", ns2="netops-rtr1", ip_ns1="10.0.1.10/24", ip_ns2="10.0.1.1/24"),
        VethPair(name_ns1="veth-r1-r2", name_ns2="veth-r2-r1", ns1="netops-rtr1", ns2="netops-rtr2", ip_ns1="10.0.2.1/24", ip_ns2="10.0.2.2/24"),
        VethPair(name_ns1="veth-r2-hb", name_ns2="veth-hb-r2", ns1="netops-rtr2", ns2="netops-hostb", ip_ns1="10.0.3.1/24", ip_ns2="10.0.3.10/24"),
    ]

    return TestbedTopologyConfig(namespaces=namespaces, veth_pairs=veth_pairs)
