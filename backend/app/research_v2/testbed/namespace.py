"""
Linux Network Namespace Manager for Research V2 Testbed.
"""

from typing import List
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import CommandExecutionRecord
from app.research_v2.testbed.exceptions import TopologyCreationError


class NamespaceManager:
    """Manages creation, listing, and deletion of Linux network namespaces."""

    @staticmethod
    def create_namespace(name: str) -> CommandExecutionRecord:
        record = ControlledExecutor.run_command(["ip", "netns", "add", name], privileged=True)
        if record.return_code != 0 and "File exists" not in record.stderr:
            raise TopologyCreationError(f"Failed to create namespace '{name}': {record.stderr}")
        return record

    @staticmethod
    def delete_namespace(name: str) -> CommandExecutionRecord:
        record = ControlledExecutor.run_command(["ip", "netns", "del", name], privileged=True)
        return record

    @staticmethod
    def list_namespaces() -> List[str]:
        record = ControlledExecutor.run_command(["ip", "netns", "list"], privileged=False)
        if record.return_code != 0:
            return []
        namespaces = []
        for line in record.stdout.splitlines():
            if line.strip():
                ns_name = line.strip().split()[0]
                namespaces.append(ns_name)
        return namespaces

    @staticmethod
    def exists_namespace(name: str) -> bool:
        return name in NamespaceManager.list_namespaces()
