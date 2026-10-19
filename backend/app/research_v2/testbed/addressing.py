"""
IP Address Manager for Research V2 Testbed.
"""

from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import CommandExecutionRecord
from app.research_v2.testbed.exceptions import TopologyCreationError


class AddressManager:
    """Manages IP address assignment inside network namespaces."""

    @staticmethod
    def assign_ip(ns: str, iface: str, ip_cidr: str) -> CommandExecutionRecord:
        record = ControlledExecutor.run_command(
            ["ip", "addr", "add", ip_cidr, "dev", iface],
            namespace=ns,
            privileged=True
        )
        if record.return_code != 0 and "File exists" not in record.stderr:
            raise TopologyCreationError(
                f"Failed to assign IP '{ip_cidr}' to '{iface}' in netns '{ns}': {record.stderr}"
            )
        return record
