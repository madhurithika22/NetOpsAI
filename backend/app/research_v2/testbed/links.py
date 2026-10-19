"""
Veth Link & Interface Manager for Research V2 Testbed.
"""

from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import CommandExecutionRecord
from app.research_v2.testbed.exceptions import TopologyCreationError


class LinkManager:
    """Manages creation, namespace attachment, and configuration of veth interface pairs."""

    @staticmethod
    def create_veth_pair(
        iface_a: str,
        ns_a: str,
        iface_b: str,
        ns_b: str
    ) -> CommandExecutionRecord:
        """
        Creates a veth pair on host and moves endpoints into their respective namespaces.
        """
        cmd = [
            "ip", "link", "add", iface_a, "type", "veth", "peer", "name", iface_b
        ]
        record = ControlledExecutor.run_command(cmd, privileged=True)
        if record.return_code != 0 and "File exists" not in record.stderr:
            raise TopologyCreationError(f"Failed to create veth pair {iface_a}<->{iface_b}: {record.stderr}")

        # Move iface_a to ns_a
        rec_a = ControlledExecutor.run_command(["ip", "link", "set", iface_a, "netns", ns_a], privileged=True)
        if rec_a.return_code != 0:
            raise TopologyCreationError(f"Failed to move interface '{iface_a}' to netns '{ns_a}': {rec_a.stderr}")

        # Move iface_b to ns_b
        rec_b = ControlledExecutor.run_command(["ip", "link", "set", iface_b, "netns", ns_b], privileged=True)
        if rec_b.return_code != 0:
            raise TopologyCreationError(f"Failed to move interface '{iface_b}' to netns '{ns_b}': {rec_b.stderr}")

        return record

    @staticmethod
    def set_interface_up(ns: str, iface: str) -> CommandExecutionRecord:
        record = ControlledExecutor.run_command(["ip", "link", "set", "dev", iface, "up"], namespace=ns, privileged=True)
        # Always bring lo up in namespace as well
        ControlledExecutor.run_command(["ip", "link", "set", "dev", "lo", "up"], namespace=ns, privileged=True)
        return record

    @staticmethod
    def set_interface_down(ns: str, iface: str) -> CommandExecutionRecord:
        return ControlledExecutor.run_command(["ip", "link", "set", "dev", iface, "down"], namespace=ns, privileged=True)

    @staticmethod
    def set_interface_mtu(ns: str, iface: str, mtu: int) -> CommandExecutionRecord:
        return ControlledExecutor.run_command(["ip", "link", "set", "dev", iface, "mtu", str(mtu)], namespace=ns, privileged=True)
