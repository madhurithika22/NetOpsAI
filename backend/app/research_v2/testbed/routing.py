"""
IP Routing Manager for Research V2 Testbed.
"""

from typing import Optional
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import CommandExecutionRecord
from app.research_v2.testbed.exceptions import TopologyCreationError


class RoutingManager:
    """Manages IPv4 forwarding and routing table entries inside network namespaces."""

    @staticmethod
    def enable_ip_forwarding(ns: str) -> CommandExecutionRecord:
        """Enables net.ipv4.ip_forward sysctl in target namespace."""
        record = ControlledExecutor.run_command(
            ["sysctl", "-w", "net.ipv4.ip_forward=1"],
            namespace=ns,
            privileged=True
        )
        return record

    @staticmethod
    def add_route(
        ns: str,
        dest_cidr: str,
        via_ip: Optional[str] = None,
        dev_iface: Optional[str] = None,
        metric: Optional[int] = None
    ) -> CommandExecutionRecord:
        cmd = ["ip", "route", "add", dest_cidr]
        if via_ip:
            cmd.extend(["via", via_ip])
        if dev_iface:
            cmd.extend(["dev", dev_iface])
        if metric is not None:
            cmd.extend(["metric", str(metric)])

        record = ControlledExecutor.run_command(cmd, namespace=ns, privileged=True)
        if record.return_code != 0 and "File exists" not in record.stderr:
            raise TopologyCreationError(
                f"Failed to add route '{dest_cidr}' in netns '{ns}': {record.stderr}"
            )
        return record

    @staticmethod
    def delete_route(
        ns: str,
        dest_cidr: str,
        via_ip: Optional[str] = None,
        dev_iface: Optional[str] = None
    ) -> CommandExecutionRecord:
        cmd = ["ip", "route", "del", dest_cidr]
        if via_ip:
            cmd.extend(["via", via_ip])
        if dev_iface:
            cmd.extend(["dev", dev_iface])

        return ControlledExecutor.run_command(cmd, namespace=ns, privileged=True)
