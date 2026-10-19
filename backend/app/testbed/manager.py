import sys
import os
import subprocess
import shutil
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel, Field
from app.testbed.config import get_default_testbed_config, TestbedTopologyConfig, TESTBED_PREFIX, PROTECTED_HOST_INTERFACES

class TestbedStatus(BaseModel):
    is_platform_supported: bool
    platform_name: str
    is_created: bool
    is_connected: bool
    active_namespaces: List[str] = Field(default_factory=list)
    active_interfaces: List[str] = Field(default_factory=list)
    message: str

class TestbedManager:
    """
    Manager for isolated Linux Network Namespace testbed.
    Enforces strict ownership validation (netops- prefix) and safety guards.
    """
    def __init__(self, config: Optional[TestbedTopologyConfig] = None):
        self.config = config or get_default_testbed_config()

    def is_supported_platform(self) -> bool:
        return sys.platform.startswith("linux")

    def is_owned_resource(self, resource_name: str) -> bool:
        """Validates that a resource belongs to NetOps testbed and is not a protected host resource."""
        if not resource_name:
            return False
        if resource_name in PROTECTED_HOST_INTERFACES:
            return False
        return resource_name.startswith(TESTBED_PREFIX) or resource_name.startswith("veth-")

    def get_status(self) -> TestbedStatus:
        platform_name = sys.platform
        supported = self.is_supported_platform()

        if not supported:
            return TestbedStatus(
                is_platform_supported=False,
                platform_name=platform_name,
                is_created=False,
                is_connected=False,
                active_namespaces=[],
                active_interfaces=[],
                message="Linux network namespaces are supported only on Linux or WSL2 with root/sudo."
            )

        # Query active netns
        namespaces = self._list_active_namespaces()
        netops_namespaces = [ns for ns in namespaces if ns.startswith(TESTBED_PREFIX)]
        is_created = len(netops_namespaces) == len(self.config.namespaces)

        is_connected = False
        if is_created:
            is_connected = self.verify_connectivity()

        return TestbedStatus(
            is_platform_supported=True,
            platform_name=platform_name,
            is_created=is_created,
            is_connected=is_connected,
            active_namespaces=netops_namespaces,
            active_interfaces=self._list_testbed_veths(),
            message="Testbed active and connected." if is_connected else ("Testbed created." if is_created else "Testbed not created.")
        )

    def create_testbed(self) -> TestbedStatus:
        if not self.is_supported_platform():
            return self.get_status()

        # Teardown any partial previous state safely
        self.teardown_testbed()

        try:
            # 1. Create namespaces
            for ns_name, ns_cfg in self.config.namespaces.items():
                if not self.is_owned_resource(ns_name):
                    raise ValueError(f"Refusing to create un-owned namespace '{ns_name}'.")
                self._run_cmd(["ip", "netns", "add", ns_name])
                self._run_cmd(["ip", "netns", "exec", ns_name, "ip", "link", "set", "lo", "up"])

                if ns_cfg.is_router:
                    self._run_cmd(["ip", "netns", "exec", ns_name, "sysctl", "-w", "net.ipv4.ip_forward=1"])

            # 2. Create veth pairs and assign to namespaces
            for veth in self.config.veth_pairs:
                self._run_cmd(["ip", "link", "add", veth.name_ns1, "type", "veth", "peer", "name", veth.name_ns2])
                self._run_cmd(["ip", "link", "set", veth.name_ns1, "netns", veth.ns1])
                self._run_cmd(["ip", "link", "set", veth.name_ns2, "netns", veth.ns2])

                # Configure IP and bring UP inside ns1
                self._run_cmd(["ip", "netns", "exec", veth.ns1, "ip", "addr", "add", veth.ip_ns1, "dev", veth.name_ns1])
                self._run_cmd(["ip", "netns", "exec", veth.ns1, "ip", "link", "set", veth.name_ns1, "up"])

                # Configure IP and bring UP inside ns2
                self._run_cmd(["ip", "netns", "exec", veth.ns2, "ip", "addr", "add", veth.ip_ns2, "dev", veth.name_ns2])
                self._run_cmd(["ip", "netns", "exec", veth.ns2, "ip", "link", "set", veth.name_ns2, "up"])

            # 3. Configure static routes
            for ns_name, ns_cfg in self.config.namespaces.items():
                for route in ns_cfg.static_routes:
                    self._run_cmd(["ip", "netns", "exec", ns_name, "ip", "route", "add", route["destination"], "via", route["via"]])

        except Exception as e:
            # Safe cleanup on failure
            self.teardown_testbed()
            raise RuntimeError(f"Failed to create Linux testbed: {str(e)}") from e

        return self.get_status()

    def teardown_testbed(self) -> TestbedStatus:
        if not self.is_supported_platform():
            return self.get_status()

        active_namespaces = self._list_active_namespaces()
        for ns in active_namespaces:
            # STRICT OWNERSHIP CHECK: Only delete namespaces starting with netops-
            if self.is_owned_resource(ns):
                try:
                    self._run_cmd(["ip", "netns", "del", ns])
                except Exception:
                    pass

        return self.get_status()

    def verify_connectivity(self) -> bool:
        if not self.is_supported_platform():
            return False
        try:
            # Ping hostB (10.0.3.10) from hostA namespace
            res = subprocess.run(
                ["ip", "netns", "exec", "netops-hosta", "ping", "-c", "2", "-W", "1", "10.0.3.10"],
                capture_output=True,
                text=True
            )
            return res.returncode == 0
        except Exception:
            return False

    def _list_active_namespaces(self) -> List[str]:
        if not self.is_supported_platform():
            return []
        try:
            res = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True, check=True)
            lines = res.stdout.strip().split("\n")
            namespaces = [line.split()[0] for line in lines if line.strip()]
            return namespaces
        except Exception:
            return []

    def _list_testbed_veths(self) -> List[str]:
        veths = []
        for v in self.config.veth_pairs:
            veths.extend([v.name_ns1, v.name_ns2])
        return veths

    def _run_cmd(self, cmd_args: List[str]) -> subprocess.CompletedProcess:
        """Executes a command list safely without shell expansion."""
        return subprocess.run(cmd_args, capture_output=True, text=True, check=True)

# Singleton manager instance
testbed_manager = TestbedManager()
