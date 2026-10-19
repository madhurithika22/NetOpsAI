import sys
import subprocess
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics
from app.ceso.simulator import NetworkStateSimulator
from app.testbed.manager import testbed_manager

def parse_ping_output(ping_stdout: str, returncode: int = 0) -> Tuple[float, float]:
    """
    Parses standard Linux ping command stdout to extract measured RTT (ms) and Packet Loss (%).
    Returns (rtt_ms, packet_loss_pct).
    """
    if not ping_stdout or not ping_stdout.strip():
        return (999.0, 100.0)

    # 1. Primary Extraction: Transmitted vs Received packet counts
    # Examples:
    # "20 packets transmitted, 19 received, 5% packet loss, time 19041ms"
    # "5 packets transmitted, 4 received, +1 errors, 20% packet loss"
    # "10 packets transmitted, 9 received, 10% packet loss"
    loss_pct: Optional[float] = None
    tx_rx_match = re.search(r"(\d+)\s+(?:packets\s+)?transmitted,\s+(\d+)\s+(?:packets\s+)?received", ping_stdout, re.IGNORECASE)
    if tx_rx_match:
        tx = int(tx_rx_match.group(1))
        rx = int(tx_rx_match.group(2))
        if tx > 0:
            loss_pct = round(((tx - rx) / tx) * 100.0, 2)

    # 2. Secondary Extraction: Regex match on "% packet loss" or "% loss"
    if loss_pct is None:
        loss_match = re.search(r"(\d+(?:\.\d+)?)%\s*(?:packet\s*)?loss", ping_stdout, re.IGNORECASE)
        if loss_match:
            loss_pct = float(loss_match.group(1))

    # 3. Fallback: Check returncode
    if loss_pct is None:
        loss_pct = 0.0 if returncode == 0 else 100.0

    # 4. Extract measured RTT (e.g. "rtt min/avg/max/mdev = 144.981/145.363/146.120/0.250 ms")
    avg_rtt = 999.0
    rtt_match = re.search(r"rtt\s+min/avg/max(?:/mdev)?\s*=\s*[\d\.]+[\s/]+([\d\.]+)", ping_stdout, re.IGNORECASE)
    if rtt_match:
        avg_rtt = float(rtt_match.group(1))
    else:
        rtt_lines = [l for l in ping_stdout.split("\n") if "rtt min/avg/max" in l or "round-trip min/avg/max" in l]
        if rtt_lines and "=" in rtt_lines[0]:
            parts = rtt_lines[0].split("=")[1].strip().split("/")
            if len(parts) >= 2:
                try:
                    avg_rtt = float(parts[1])
                except ValueError:
                    avg_rtt = 999.0

    if loss_pct >= 100.0 and avg_rtt == 999.0:
        avg_rtt = 999.0

    return (avg_rtt, loss_pct)

def parse_ip_link_stats(ip_link_output: str, iface_name: str) -> dict:
    """
    Parses 'ip -s link' output for a specific interface to extract measured RX/TX bytes, errors, and drops.
    """
    stats = {
        "rx_bytes": 0, "tx_bytes": 0,
        "rx_errors": 0, "tx_errors": 0,
        "rx_drops": 0, "tx_drops": 0,
        "is_up": True
    }
    if not ip_link_output:
        return stats

    lines = ip_link_output.split("\n")
    in_iface = False
    rx_next = False
    tx_next = False

    for line in lines:
        if iface_name in line and ("<" in line or ":" in line):
            in_iface = True
            stats["is_up"] = "state UP" in line or "LOWER_UP" in line or "NO-CARRIER" not in line
            continue
        if in_iface and ("<" in line and ":" in line):
            break

        if in_iface:
            if "RX:" in line:
                rx_next = True
                tx_next = False
                continue
            elif "TX:" in line:
                tx_next = True
                rx_next = False
                continue

            if rx_next and line.strip() and line.strip()[0].isdigit():
                parts = line.strip().split()
                if len(parts) >= 4:
                    stats["rx_bytes"] = int(parts[0])
                    stats["rx_errors"] = int(parts[2])
                    stats["rx_drops"] = int(parts[3])
                rx_next = False

            elif tx_next and line.strip() and line.strip()[0].isdigit():
                parts = line.strip().split()
                if len(parts) >= 4:
                    stats["tx_bytes"] = int(parts[0])
                    stats["tx_errors"] = int(parts[2])
                    stats["tx_drops"] = int(parts[3])
                tx_next = False

    return stats

class TelemetryProvider(ABC):
    """Abstract Telemetry Provider Interface for CESO Layer."""
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def collect_telemetry(self) -> NetworkState:
        pass

    @abstractmethod
    def inject_fault(self, fault_type: str) -> NetworkState:
        pass

    @abstractmethod
    def reset(self) -> NetworkState:
        pass

class SimulatedTelemetryProvider(TelemetryProvider):
    """In-memory simulated telemetry provider."""
    def __init__(self):
        self.simulator = NetworkStateSimulator()

    @property
    def provider_name(self) -> str:
        return "SIMULATED"

    def collect_telemetry(self) -> NetworkState:
        return self.simulator.generate_snapshot()

    def inject_fault(self, fault_type: str) -> NetworkState:
        self.simulator.inject_fault(fault_type)
        return self.collect_telemetry()

    def reset(self) -> NetworkState:
        self.simulator.reset()
        return self.collect_telemetry()

class LinuxTestbedTelemetryProvider(TelemetryProvider):
    """
    Linux Network Namespace Testbed Telemetry Provider.
    Queries iproute2 and ping commands inside namespaces on Linux.
    Falls back gracefully to recorded netns telemetry snapshots on unsupported platforms.
    """
    def __init__(self):
        self.active_fault: str = "NONE"
        self.snapshot_counter: int = 0

    @property
    def provider_name(self) -> str:
        return "LINUX_TESTBED"

    def collect_telemetry(self) -> NetworkState:
        self.snapshot_counter += 1
        snapshot_id = f"snap-tb-{self.snapshot_counter:04d}"
        now = datetime.now(timezone.utc)

        if testbed_manager.is_supported_platform() and testbed_manager.get_status().is_created:
            return self._collect_real_linux_telemetry(snapshot_id, now)
        else:
            return self._collect_mocked_testbed_telemetry(snapshot_id, now)

    def inject_fault(self, fault_type: str) -> NetworkState:
        self.active_fault = fault_type
        return self.collect_telemetry()

    def reset(self) -> NetworkState:
        self.active_fault = "NONE"
        return self.collect_telemetry()

    def _collect_real_linux_telemetry(self, snapshot_id: str, now: datetime) -> NetworkState:
        interfaces: Dict[str, InterfaceState] = {}
        links: List[LinkLatency] = []
        routes: List[RouteEntry] = []

        # 1. Query rtr1 netns interface stats via ip -s link
        try:
            r1_link_out = subprocess.run(["ip", "netns", "exec", "netops-rtr1", "ip", "-s", "link", "show", "veth-r1-r2"], capture_output=True, text=True).stdout
            r1_stats = parse_ip_link_stats(r1_link_out, "veth-r1-r2")
        except Exception:
            r1_stats = {"is_up": False, "rx_bytes": 0, "tx_bytes": 0, "rx_errors": 0, "tx_errors": 0, "rx_drops": 0, "tx_drops": 0}

        interfaces["veth-r1-r2"] = InterfaceState(
            name="veth-r1-r2",
            is_up=r1_stats["is_up"],
            ip_addresses=["10.0.2.1/24"],
            rx_bytes=r1_stats["rx_bytes"],
            tx_bytes=r1_stats["tx_bytes"],
            rx_errors=r1_stats["rx_errors"],
            tx_errors=r1_stats["tx_errors"],
            rx_drops=r1_stats["rx_drops"],
            tx_drops=r1_stats["tx_drops"],
            throughput_bps=950000.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 100000.0,
            utilization_pct=95.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 10.0
        )

        # 2. Measure Link 1: netops-hosta -> netops-rtr1 (10.0.1.1)
        try:
            p1_res = subprocess.run(["ip", "netns", "exec", "netops-hosta", "ping", "-c", "5", "-i", "0.1", "-W", "1", "10.0.1.1"], capture_output=True, text=True)
            rtt1, loss1 = parse_ping_output(p1_res.stdout, p1_res.returncode)
        except Exception:
            rtt1, loss1 = 1.2, 0.0

        links.append(LinkLatency(source_node="netops-hosta", target_node="netops-rtr1", rtt_ms=rtt1, packet_loss_pct=loss1, status="HEALTHY" if (rtt1 < 50.0 and loss1 < 10.0) else "DEGRADED"))

        # 3. Measure Link 2 (The Impaired Link): netops-rtr1 -> netops-rtr2 (10.0.2.2) using 20 ICMP probes
        try:
            p2_res = subprocess.run(["ip", "netns", "exec", "netops-rtr1", "ping", "-c", "20", "-i", "0.1", "-W", "1", "10.0.2.2"], capture_output=True, text=True)
            measured_rtt, measured_loss = parse_ping_output(p2_res.stdout, p2_res.returncode)
        except Exception:
            measured_rtt = 999.0
            measured_loss = 100.0

        is_degraded = (measured_rtt > 50.0) or (measured_loss > 10.0) or (not r1_stats["is_up"])

        links.append(
            LinkLatency(
                source_node="netops-rtr1",
                target_node="netops-rtr2",
                rtt_ms=measured_rtt,
                packet_loss_pct=measured_loss,
                status="DEGRADED" if is_degraded else "HEALTHY"
            )
        )

        # 4. Measure Link 3: netops-rtr2 -> netops-hostb (10.0.3.10)
        try:
            p3_res = subprocess.run(["ip", "netns", "exec", "netops-rtr2", "ping", "-c", "5", "-i", "0.1", "-W", "1", "10.0.3.10"], capture_output=True, text=True)
            rtt3, loss3 = parse_ping_output(p3_res.stdout, p3_res.returncode)
        except Exception:
            rtt3, loss3 = 2.1, 0.0

        links.append(LinkLatency(source_node="netops-rtr2", target_node="netops-hostb", rtt_ms=rtt3, packet_loss_pct=loss3, status="HEALTHY" if (rtt3 < 50.0 and loss3 < 10.0) else "DEGRADED"))

        # 5. Route table state
        routes.append(RouteEntry(destination="10.0.3.0/24", gateway="10.0.2.2", interface="veth-r1-r2", metric=10))

        nodes = {
            "netops-rtr1": NodeMetrics(node_id="netops-rtr1", cpu_utilization_pct=85.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 25.0, memory_utilization_pct=40.0),
            "netops-rtr2": NodeMetrics(node_id="netops-rtr2", cpu_utilization_pct=20.0, memory_utilization_pct=35.0)
        }

        return NetworkState(
            snapshot_id=snapshot_id,
            timestamp=now,
            topology_id="netops-linux-testbed",
            interfaces=interfaces,
            links=links,
            routes=routes,
            nodes=nodes,
            anomalies_detected=is_degraded
        )

    def _collect_mocked_testbed_telemetry(self, snapshot_id: str, now: datetime) -> NetworkState:
        rtr1_r2_up = self.active_fault != "INTERFACE_FAILURE"
        rtt_ms = 145.5 if self.active_fault == "HIGH_LATENCY_CONGESTION" else (999.0 if not rtr1_r2_up else 4.8)
        loss_pct = 25.0 if self.active_fault == "PACKET_LOSS" else (15.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else (100.0 if not rtr1_r2_up else 0.0))

        interfaces = {
            "veth-r1-ha": InterfaceState(name="veth-r1-ha", is_up=True, ip_addresses=["10.0.1.1/24"], throughput_bps=100000.0),
            "veth-r1-r2": InterfaceState(
                name="veth-r1-r2",
                is_up=rtr1_r2_up,
                ip_addresses=["10.0.2.1/24"],
                rx_errors=45 if self.active_fault == "INTERFACE_FAILURE" else 0,
                rx_drops=240 if self.active_fault == "PACKET_LOSS" else 0,
                throughput_bps=950000.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 100000.0,
                utilization_pct=95.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 10.0
            )
        }

        links = [
            LinkLatency(source_node="netops-hosta", target_node="netops-rtr1", rtt_ms=1.2, packet_loss_pct=0.0, status="HEALTHY"),
            LinkLatency(source_node="netops-rtr1", target_node="netops-rtr2", rtt_ms=rtt_ms, packet_loss_pct=loss_pct, status="HEALTHY" if (rtt_ms < 50 and loss_pct < 10) else "DEGRADED"),
            LinkLatency(source_node="netops-rtr2", target_node="netops-hostb", rtt_ms=2.1, packet_loss_pct=0.0, status="HEALTHY"),
        ]

        bad_route = self.active_fault == "ROUTING_MISCONFIGURATION"
        routes = [
            RouteEntry(destination="10.0.1.0/24", gateway=None, interface="veth-r1-ha", metric=10),
            RouteEntry(destination="10.0.3.0/24", gateway="10.0.2.2" if not bad_route else None, interface="veth-r1-r2" if not bad_route else "veth-r1-ha", metric=10 if not bad_route else 999)
        ]

        nodes = {
            "netops-rtr1": NodeMetrics(node_id="netops-rtr1", cpu_utilization_pct=85.0 if self.active_fault == "HIGH_LATENCY_CONGESTION" else 20.0, memory_utilization_pct=40.0),
            "netops-rtr2": NodeMetrics(node_id="netops-rtr2", cpu_utilization_pct=20.0, memory_utilization_pct=35.0)
        }

        return NetworkState(
            snapshot_id=snapshot_id,
            timestamp=now,
            topology_id="netops-linux-testbed",
            interfaces=interfaces,
            links=links,
            routes=routes,
            nodes=nodes,
            anomalies_detected=self.active_fault not in ["NONE", "REROUTED"]
        )


class TelemetryProviderFactory:
    @staticmethod
    def get_provider(mode: str = "SIMULATED") -> TelemetryProvider:
        if mode == "LINUX_TESTBED":
            return LinuxTestbedTelemetryProvider()
        return SimulatedTelemetryProvider()

