"""
Real Fault Injector & Activation Verifier for NetOps Research V2.

Injects netem traffic control impairments into real Linux network namespaces
and independently verifies fault activation via telemetry probes.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from app.research_v2.guard import ResearchExecutionContext
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import (
    FaultDefinition,
    FaultInjectionRecord
)
from app.research_v2.testbed.telemetry import RealTelemetryCollector
from app.research_v2.testbed.exceptions import (
    FaultInjectionError,
    FaultActivationError
)


class RealFaultInjector:
    """
    Injects physical network faults into Linux namespaces and verifies activation.
    """

    @classmethod
    def create_high_latency_fault(
        cls,
        fault_id: str = "flt-001",
        target_ns: str = "rns-router-1",
        target_iface: str = "veth-r1-r2",
        delay_ms: int = 150,
        loss_pct: int = 20
    ) -> FaultDefinition:
        """
        Creates FaultDefinition for HIGH_LATENCY_CONGESTION using tc netem.
        """
        return FaultDefinition(
            fault_id=fault_id,
            fault_type="HIGH_LATENCY_CONGESTION",
            target_namespace=target_ns,
            target_interface=target_iface,
            parameters={"delay_ms": delay_ms, "loss_pct": loss_pct},
            injection_command=[
                "tc", "qdisc", "add", "dev", target_iface, "root", "netem",
                "delay", f"{delay_ms}ms", "loss", f"{loss_pct}%"
            ],
            reset_command=[
                "tc", "qdisc", "del", "dev", target_iface, "root"
            ]
        )

    @classmethod
    def inject_fault(
        cls,
        fault_def: FaultDefinition,
        experiment_id: str = "exp-default"
    ) -> FaultInjectionRecord:
        """
        Executes real fault injection and verifies activation via telemetry probes.
        """
        ResearchExecutionContext.assert_real_execution("RealFaultInjector")

        # 1. Pre-fault telemetry snapshot
        pre_snapshot = RealTelemetryCollector.collect_telemetry(experiment_id)

        injection_ts = datetime.now(timezone.utc)

        # 2. Execute real tc netem injection command in target namespace with privileged=True
        cmd_rec = ControlledExecutor.run_command(
            fault_def.injection_command,
            namespace=fault_def.target_namespace,
            privileged=True
        )

        if cmd_rec.return_code != 0:
            raise FaultInjectionError(
                f"Fault injection command failed on {fault_def.target_namespace}:{fault_def.target_interface}: {cmd_rec.stderr}"
            )

        # 3. Inspect tc qdisc state directly in target namespace (requires privileged=True to enter netns)
        tc_check = ControlledExecutor.run_command(
            ["tc", "qdisc", "show", "dev", fault_def.target_interface],
            namespace=fault_def.target_namespace,
            privileged=True
        )
        if "netem" not in tc_check.stdout:
            raise FaultInjectionError(
                f"qdisc netem was not found on interface '{fault_def.target_interface}' after injection"
            )

        # 4. Collect independent post-fault telemetry
        post_snapshot = RealTelemetryCollector.collect_telemetry(experiment_id)

        # 5. Verify fault activation criteria from telemetry metrics
        rtt_observed = post_snapshot.link_latency.rtt_avg_ms if post_snapshot.link_latency else 0.0
        loss_observed = post_snapshot.link_latency.packet_loss_pct if post_snapshot.link_latency else 0.0

        activation_verified = (rtt_observed > 50.0) or (loss_observed > 10.0)

        status = "ACTIVE" if activation_verified else "FAULT_ACTIVATION_FAILED"

        record = FaultInjectionRecord(
            fault_id=fault_def.fault_id,
            fault_type=fault_def.fault_type,
            target_namespace=fault_def.target_namespace,
            target_interface=fault_def.target_interface,
            parameters=fault_def.parameters,
            injection_command_record=cmd_rec,
            injection_timestamp=injection_ts,
            status=status,
            pre_fault_snapshot=pre_snapshot,
            post_fault_snapshot=post_snapshot,
            activation_verified=activation_verified,
            observed_rtt_ms=rtt_observed,
            observed_loss_pct=loss_observed
        )

        if not activation_verified:
            raise FaultActivationError(
                f"Fault injection completed but telemetry did not observe impairment (RTT={rtt_observed}ms, loss={loss_observed}%)"
            )

        return record
