"""
Deterministic 4-Node Network Namespace Topology Builder for Research V2.

Topology Architecture:
  host-a (10.0.1.10/24)
    | veth-ha-r1 <-> veth-r1-ha
  router-1 (10.0.1.1/24, 10.0.2.1/24)
    | veth-r1-r2 <-> veth-r2-r1
  router-2 (10.0.2.2/24, 10.0.3.1/24)
    | veth-r2-hb <-> veth-hb-r2
  host-b (10.0.3.10/24)
"""

from typing import Dict, Any
from app.research_v2.testbed.capabilities import check_testbed_capabilities
from app.research_v2.testbed.exceptions import (
    TestbedCapabilityError,
    TopologyCreationError,
    CleanupError
)
from app.research_v2.testbed.namespace import NamespaceManager
from app.research_v2.testbed.links import LinkManager
from app.research_v2.testbed.addressing import AddressManager
from app.research_v2.testbed.routing import RoutingManager


class ResearchTopology:
    """
    Manages creation, lifecycle, and teardown of deterministic 4-node research testbed.
    """
    NS_HOST_A = "rns-host-a"
    NS_ROUTER_1 = "rns-router-1"
    NS_ROUTER_2 = "rns-router-2"
    NS_HOST_B = "rns-host-b"

    ALL_NAMESPACES = [NS_HOST_A, NS_ROUTER_1, NS_ROUTER_2, NS_HOST_B]

    @classmethod
    def create_topology(cls) -> Dict[str, Any]:
        """
        Idempotent creation of the 4-node research topology.
        Fails explicitly if host environment lacks Linux network namespace capabilities.
        """
        caps = check_testbed_capabilities()
        if not caps["ready"]:
            raise TestbedCapabilityError(
                f"Host environment cannot create Linux research testbed: {caps.get('netns_error') or 'Platform is not Linux / missing netns capabilities'}"
            )

        # Cleanup any pre-existing namespaces to ensure fresh baseline
        cls.destroy_topology()

        try:
            # 1. Create Namespaces
            for ns in cls.ALL_NAMESPACES:
                NamespaceManager.create_namespace(ns)

            # 2. Create Veth Links
            # Link 1: host-a <-> router-1
            LinkManager.create_veth_pair("veth-ha-r1", cls.NS_HOST_A, "veth-r1-ha", cls.NS_ROUTER_1)

            # Link 2: router-1 <-> router-2
            LinkManager.create_veth_pair("veth-r1-r2", cls.NS_ROUTER_1, "veth-r2-r1", cls.NS_ROUTER_2)

            # Link 3: router-2 <-> host-b
            LinkManager.create_veth_pair("veth-r2-hb", cls.NS_ROUTER_2, "veth-hb-r2", cls.NS_HOST_B)

            # 3. Assign IP Addresses
            AddressManager.assign_ip(cls.NS_HOST_A, "veth-ha-r1", "10.0.1.10/24")
            AddressManager.assign_ip(cls.NS_ROUTER_1, "veth-r1-ha", "10.0.1.1/24")
            AddressManager.assign_ip(cls.NS_ROUTER_1, "veth-r1-r2", "10.0.2.1/24")
            AddressManager.assign_ip(cls.NS_ROUTER_2, "veth-r2-r1", "10.0.2.2/24")
            AddressManager.assign_ip(cls.NS_ROUTER_2, "veth-r2-hb", "10.0.3.1/24")
            AddressManager.assign_ip(cls.NS_HOST_B, "veth-hb-r2", "10.0.3.10/24")

            # 4. Bring Interfaces UP
            LinkManager.set_interface_up(cls.NS_HOST_A, "veth-ha-r1")
            LinkManager.set_interface_up(cls.NS_ROUTER_1, "veth-r1-ha")
            LinkManager.set_interface_up(cls.NS_ROUTER_1, "veth-r1-r2")
            LinkManager.set_interface_up(cls.NS_ROUTER_2, "veth-r2-r1")
            LinkManager.set_interface_up(cls.NS_ROUTER_2, "veth-r2-hb")
            LinkManager.set_interface_up(cls.NS_HOST_B, "veth-hb-r2")

            # 5. Enable IP Forwarding on Routers
            RoutingManager.enable_ip_forwarding(cls.NS_ROUTER_1)
            RoutingManager.enable_ip_forwarding(cls.NS_ROUTER_2)

            # 6. Configure IP Routing Tables
            # host-a -> default via 10.0.1.1
            RoutingManager.add_route(cls.NS_HOST_A, "default", via_ip="10.0.1.1")

            # router-1 -> reach 10.0.3.0/24 via 10.0.2.2
            RoutingManager.add_route(cls.NS_ROUTER_1, "10.0.3.0/24", via_ip="10.0.2.2")

            # router-2 -> reach 10.0.1.0/24 via 10.0.2.1
            RoutingManager.add_route(cls.NS_ROUTER_2, "10.0.1.0/24", via_ip="10.0.2.1")

            # host-b -> default via 10.0.3.1
            RoutingManager.add_route(cls.NS_HOST_B, "default", via_ip="10.0.3.1")

            return cls.get_topology_state()

        except Exception as e:
            # On creation failure, clean up namespaces to avoid orphans
            cls.destroy_topology()
            raise TopologyCreationError(f"Research topology creation failed: {str(e)}") from e

    @classmethod
    def destroy_topology(cls):
        """Deletes all research namespaces and attached veth links."""
        for ns in cls.ALL_NAMESPACES:
            try:
                NamespaceManager.delete_namespace(ns)
            except Exception:
                pass

    @classmethod
    def is_topology_present(cls) -> bool:
        """Checks if all 4 research namespaces exist."""
        active = NamespaceManager.list_namespaces()
        return all(ns in active for ns in cls.ALL_NAMESPACES)

    @classmethod
    def get_topology_state(cls) -> Dict[str, Any]:
        """Returns structured layout dictionary of the topology."""
        return {
            "topology_name": "4-node-linear-netns",
            "namespaces": {
                cls.NS_HOST_A: {"ip": "10.0.1.10/24", "gateway": "10.0.1.1"},
                cls.NS_ROUTER_1: {"ips": ["10.0.1.1/24", "10.0.2.1/24"], "routes": {"10.0.3.0/24": "10.0.2.2"}},
                cls.NS_ROUTER_2: {"ips": ["10.0.2.2/24", "10.0.3.1/24"], "routes": {"10.0.1.0/24": "10.0.2.1"}},
                cls.NS_HOST_B: {"ip": "10.0.3.10/24", "gateway": "10.0.3.1"}
            },
            "is_present": cls.is_topology_present()
        }
