import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.testbed.manager import testbed_manager
from app.testbed.config import PROTECTED_HOST_INTERFACES, TESTBED_PREFIX

class FaultInjectionLog(BaseModel):
    fault_id: str
    fault_type: str
    target_namespace: str
    target_interface: str
    command_executed: str
    timestamp: datetime
    status: str

class TestbedFaultInjector:
    """
    Controlled Network Fault Injector for Linux Network Namespace Testbed.
    Enforces strict safety validation against NetOps-owned testbed resources.
    Captures exact stderr output on command failures.
    """
    ALLOWED_FAULT_TYPES = {
        "HIGH_LATENCY_CONGESTION",
        "PACKET_LOSS",
        "INTERFACE_FAILURE",
        "ROUTING_MISCONFIGURATION"
    }

    def __init__(self):
        self.active_fault: str = "NONE"
        self.injection_logs: List[FaultInjectionLog] = []

    def inject_testbed_fault(
        self,
        fault_type: str,
        target_ns: str = "netops-rtr1",
        target_iface: str = "veth-r1-r2"
    ) -> FaultInjectionLog:
        # 1. Safety Validation Checks (always enforced regardless of mode)
        self._validate_safety(fault_type, target_ns, target_iface)

        log_entry = FaultInjectionLog(
            fault_id=f"flt-{len(self.injection_logs)+1:03d}",
            fault_type=fault_type,
            target_namespace=target_ns,
            target_interface=target_iface,
            command_executed="",
            timestamp=datetime.now(timezone.utc),
            status="PENDING"
        )

        testbed_status = testbed_manager.get_status()

        # Check if real Linux testbed execution is possible (supported platform AND active created namespaces)
        should_execute_real = testbed_status.is_platform_supported and testbed_status.is_created

        if not should_execute_real:
            # If testbed is not created, log validated simulated testbed fault safely
            log_entry.command_executed = f"[SIMULATED TESTBED FAULT] {fault_type} on {target_ns}:{target_iface}"
            log_entry.status = "SUCCESS"
            self.active_fault = fault_type
            self.injection_logs.append(log_entry)
            return log_entry

        # 2. Execute real Linux netns tc/ip command on active Linux testbed
        try:
            if fault_type == "HIGH_LATENCY_CONGESTION":
                cmd = ["ip", "netns", "exec", target_ns, "tc", "qdisc", "add", "dev", target_iface, "root", "netem", "delay", "145ms", "loss", "15%"]
            elif fault_type == "PACKET_LOSS":
                cmd = ["ip", "netns", "exec", target_ns, "tc", "qdisc", "add", "dev", target_iface, "root", "netem", "loss", "25%"]
            elif fault_type == "INTERFACE_FAILURE":
                cmd = ["ip", "netns", "exec", target_ns, "ip", "link", "set", "dev", target_iface, "down"]
            elif fault_type == "ROUTING_MISCONFIGURATION":
                cmd = ["ip", "netns", "exec", target_ns, "ip", "route", "del", "10.0.3.0/24"]
            else:
                raise ValueError(f"Unsupported fault type '{fault_type}'.")

            log_entry.command_executed = " ".join(cmd)
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            log_entry.status = "SUCCESS"
            self.active_fault = fault_type

        except subprocess.CalledProcessError as cpe:
            stderr_msg = cpe.stderr.strip() if cpe.stderr else (cpe.stdout.strip() if cpe.stdout else str(cpe))
            detailed_err = f"exit code {cpe.returncode}: {stderr_msg}"
            log_entry.status = f"FAILED ({detailed_err})"
            self.injection_logs.append(log_entry)
            # Attempt safety cleanup
            self.reset_testbed_faults(target_ns, target_iface)
            raise RuntimeError(
                f"Testbed fault injection failed for command '{' '.join(cmd)}' ({detailed_err})"
            ) from cpe
        except Exception as e:
            log_entry.status = f"FAILED: {str(e)}"
            self.injection_logs.append(log_entry)
            self.reset_testbed_faults(target_ns, target_iface)
            raise RuntimeError(f"Testbed fault injection error: {str(e)}") from e

        self.injection_logs.append(log_entry)
        return log_entry

    def reset_testbed_faults(self, target_ns: str = "netops-rtr1", target_iface: str = "veth-r1-r2"):
        self.active_fault = "NONE"
        testbed_status = testbed_manager.get_status()
        if not (testbed_status.is_platform_supported and testbed_status.is_created):
            return

        # Restore baseline on active Linux testbed
        try:
            subprocess.run(["ip", "netns", "exec", target_ns, "tc", "qdisc", "del", "dev", target_iface, "root"], capture_output=True, text=True)
            subprocess.run(["ip", "netns", "exec", target_ns, "ip", "link", "set", "dev", target_iface, "up"], capture_output=True, text=True)
            subprocess.run(["ip", "netns", "exec", target_ns, "ip", "route", "add", "10.0.3.0/24", "via", "10.0.2.2"], capture_output=True, text=True)
        except Exception:
            pass

    def _validate_safety(self, fault_type: str, target_ns: str, target_iface: str):
        if fault_type not in self.ALLOWED_FAULT_TYPES:
            raise ValueError(f"Fault type '{fault_type}' is not in permitted safety allowlist.")

        if target_iface in PROTECTED_HOST_INTERFACES:
            raise PermissionError(f"CRITICAL SAFETY VIOLATION: Target interface '{target_iface}' is a protected host resource.")

        if not testbed_manager.is_owned_resource(target_ns):
            raise PermissionError(f"CRITICAL SAFETY VIOLATION: Target namespace '{target_ns}' is not owned by NetOps testbed.")

        if not testbed_manager.is_owned_resource(target_iface):
            raise PermissionError(f"CRITICAL SAFETY VIOLATION: Target interface '{target_iface}' is not owned by NetOps testbed.")

# Singleton fault injector
testbed_fault_injector = TestbedFaultInjector()
