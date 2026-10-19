"""
Real Telemetry Collector for NetOps Research V2.

Executes ping probes, ip link stats, ip route, and tc qdisc queries against Linux network namespaces.
Produces immutable, fully auditable TelemetrySnapshots containing raw command evidence.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from app.research_v2.guard import ResearchExecutionContext
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import (
    TelemetrySnapshot,
    LinkLatencyRecord,
    InterfaceStateRecord,
    RouteRecord,
    QdiscRecord,
    CommandExecutionRecord
)
from app.research_v2.testbed.exceptions import ResearchTestbedError


def parse_ping_output(stdout: str) -> LinkLatencyRecord:
    """
    Parses standard Linux ping stdout to extract loss %, RTT min/avg/max/mdev.
    """
    tx, rx, loss_pct = 0, 0, 100.0
    rtt_min, rtt_avg, rtt_max, rtt_mdev = 999.0, 999.0, 999.0, 0.0

    # 1. Extract packet loss
    # Example: "5 packets transmitted, 5 received, 0% packet loss, time 804ms"
    tx_rx_match = re.search(r"(\d+)\s+(?:packets\s+)?transmitted,\s+(\d+)\s+(?:packets\s+)?received", stdout, re.IGNORECASE)
    if tx_rx_match:
        tx = int(tx_rx_match.group(1))
        rx = int(tx_rx_match.group(2))
        if tx > 0:
            loss_pct = round(((tx - rx) / tx) * 100.0, 2)

    # 2. Extract RTT metrics
    # Example: "rtt min/avg/max/mdev = 0.045/0.062/0.089/0.015 ms"
    rtt_match = re.search(r"rtt\s+min/avg/max/mdev\s*=\s*([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)", stdout, re.IGNORECASE)
    if rtt_match:
        rtt_min = float(rtt_match.group(1))
        rtt_avg = float(rtt_match.group(2))
        rtt_max = float(rtt_match.group(3))
        rtt_mdev = float(rtt_match.group(4))

    return LinkLatencyRecord(
        source_node="rns-host-a",
        target_node="rns-host-b",
        target_ip="10.0.3.10",
        packets_tx=tx,
        packets_rx=rx,
        packet_loss_pct=loss_pct,
        rtt_min_ms=rtt_min,
        rtt_avg_ms=rtt_avg,
        rtt_max_ms=rtt_max,
        rtt_mdev_ms=rtt_mdev
    )


class RealTelemetryCollector:
    """
    Real telemetry collector executing real Linux namespace queries.
    """

    @classmethod
    def collect_telemetry(
        cls,
        experiment_id: str = "exp-default",
        source_ns: str = "rns-host-a",
        target_ip: str = "10.0.3.10",
        probe_count: int = 30
    ) -> TelemetrySnapshot:
        """
        Collects real telemetry snapshot by probing the active Linux testbed.
        Entering network namespaces via ip netns exec requires privileged execution.
        """
        ResearchExecutionContext.assert_real_execution("RealTelemetryCollector")
        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc)
        raw_commands: List[CommandExecutionRecord] = []

        # 1. ICMP Reachability & Latency Probe
        ping_cmd = ["ping", "-c", str(probe_count), "-i", "0.2", "-W", "1", target_ip]
        ping_rec = ControlledExecutor.run_command(ping_cmd, namespace=source_ns, privileged=True)
        raw_commands.append(ping_rec)

        link_latency = parse_ping_output(ping_rec.stdout)

        # 2. Collect Interface States & Counters across namespaces
        interface_states: Dict[str, InterfaceStateRecord] = {}
        target_namespaces = ["rns-host-a", "rns-router-1", "rns-router-2", "rns-host-b"]

        for ns in target_namespaces:
            ip_link_rec = ControlledExecutor.run_command(["ip", "-s", "link", "show"], namespace=ns, privileged=True)
            raw_commands.append(ip_link_rec)

            # Parse ip link stdout for each interface
            curr_iface = None
            for line in ip_link_rec.stdout.splitlines():
                if ":" in line and ("<" in line or "mtu" in line):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        iface_name = parts[1].strip().split("@")[0].strip()
                        is_up = "state UP" in line or "LOWER_UP" in line
                        mtu_match = re.search(r"mtu\s+(\d+)", line)
                        mtu_val = int(mtu_match.group(1)) if mtu_match else 1500

                        curr_iface = InterfaceStateRecord(
                            name=f"{ns}:{iface_name}",
                            is_up=is_up,
                            mtu=mtu_val
                        )
                        interface_states[curr_iface.name] = curr_iface

        # 3. Collect Routing Tables
        routes: List[RouteRecord] = []
        for ns in target_namespaces:
            route_rec = ControlledExecutor.run_command(["ip", "route", "show"], namespace=ns, privileged=True)
            raw_commands.append(route_rec)
            for line in route_rec.stdout.splitlines():
                if line.strip():
                    routes.append(RouteRecord(
                        destination=line.split()[0] if line.split() else "unknown",
                        raw_route=f"{ns}: {line.strip()}"
                    ))

        # 4. Collect Traffic Control (tc) qdisc state with detailed statistics (-s)
        qdiscs: List[QdiscRecord] = []
        for ns in target_namespaces:
            tc_rec = ControlledExecutor.run_command(["tc", "-s", "qdisc", "show"], namespace=ns, privileged=True)
            raw_commands.append(tc_rec)
            for line in tc_rec.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split()
                    q_type = parts[1] if len(parts) > 1 else "unknown"
                    iface = parts[4] if len(parts) > 4 else "unknown"
                    qdiscs.append(QdiscRecord(
                        namespace=ns,
                        interface=iface,
                        qdisc_type=q_type,
                        options_raw=line.strip()
                    ))

        is_healthy = (
            link_latency.packet_loss_pct < 10.0 and
            link_latency.rtt_avg_ms < 50.0 and
            ping_rec.return_code == 0
        )

        return TelemetrySnapshot(
            snapshot_id=snapshot_id,
            experiment_id=experiment_id,
            timestamp=timestamp,
            source_namespace=source_ns,
            destination_ip=target_ip,
            link_latency=link_latency,
            interface_states=interface_states,
            routes=routes,
            qdiscs=qdiscs,
            raw_commands=raw_commands,
            is_healthy=is_healthy,
            summary=f"RTT avg={link_latency.rtt_avg_ms}ms, loss={link_latency.packet_loss_pct}%, healthy={is_healthy}"
        )
