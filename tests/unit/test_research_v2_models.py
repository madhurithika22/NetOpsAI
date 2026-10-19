"""
Unit tests for Research V2 data models.
"""

from datetime import datetime, timezone
from app.research_v2.testbed.models import (
    CommandExecutionRecord,
    LinkLatencyRecord,
    TelemetrySnapshot,
    FaultDefinition,
    RemediationPlan
)


def test_command_execution_record_model():
    rec = CommandExecutionRecord(
        original_command=["ip", "netns", "list"],
        effective_command=["ip", "netns", "list"],
        privileged=False,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_ms=1.2,
        return_code=0,
        stdout="ns1\nns2\n",
        stderr=""
    )
    assert rec.original_command == ["ip", "netns", "list"]
    assert rec.effective_command == ["ip", "netns", "list"]
    assert rec.privileged is False
    assert rec.return_code == 0
    assert "ns1" in rec.stdout


def test_telemetry_snapshot_model():
    snap = TelemetrySnapshot(
        snapshot_id="snap-001",
        experiment_id="exp-001",
        timestamp=datetime.now(timezone.utc),
        source_namespace="rns-host-a",
        destination_ip="10.0.3.10",
        is_healthy=True
    )
    assert snap.snapshot_id == "snap-001"
    assert snap.is_healthy is True


def test_fault_definition_model():
    fault = FaultDefinition(
        fault_id="flt-001",
        fault_type="HIGH_LATENCY_CONGESTION",
        target_namespace="rns-router-1",
        target_interface="veth-r1-r2",
        parameters={"delay_ms": 150},
        injection_command=["tc", "qdisc", "add", "dev", "veth-r1-r2", "root", "netem", "delay", "150ms"]
    )
    assert fault.fault_type == "HIGH_LATENCY_CONGESTION"
    assert fault.parameters["delay_ms"] == 150
