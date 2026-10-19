"""
Independent Verification Engine for NetOps Research V2.

Independently measures post-remediation network state to verify actual recovery.
Does not trust executor claims or application-internal assumptions.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from app.research_v2.guard import ResearchExecutionContext
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import IndependentVerificationRecord
from app.research_v2.testbed.telemetry import RealTelemetryCollector
from app.research_v2.testbed.exceptions import VerificationError


class IndependentVerifier:
    """
    Independently verifies post-remediation state recovery via telemetry probes and qdisc inspection.
    """

    @classmethod
    def verify_recovery(
        cls,
        plan_id: str,
        target_ns: str = "rns-router-1",
        target_interface: str = "veth-r1-r2",
        target_iface: Optional[str] = None,
        experiment_id: str = "exp-default",
        rtt_threshold_ms: float = 20.0,
        loss_threshold_pct: float = 5.0
    ) -> IndependentVerificationRecord:
        """
        Collects fresh post-remediation telemetry and inspects target qdisc state.
        """
        ResearchExecutionContext.assert_real_execution("IndependentVerifier")

        iface_name = target_iface or target_interface

        verification_id = f"ver-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc)

        # 1. Collect fresh post-remediation telemetry
        post_snapshot = RealTelemetryCollector.collect_telemetry(experiment_id)

        rtt_observed = post_snapshot.link_latency.rtt_avg_ms if post_snapshot.link_latency else 999.0
        loss_observed = post_snapshot.link_latency.packet_loss_pct if post_snapshot.link_latency else 100.0

        reachability_healthy = post_snapshot.link_latency is not None and post_snapshot.link_latency.packets_rx > 0
        loss_healthy = loss_observed <= loss_threshold_pct
        rtt_healthy = rtt_observed <= rtt_threshold_ms

        # 2. Inspect tc qdisc state in target namespace directly with privileged=True
        tc_check = ControlledExecutor.run_command(
            ["tc", "qdisc", "show", "dev", iface_name],
            namespace=target_ns,
            privileged=True
        )
        qdisc_absent = "netem" not in tc_check.stdout

        overall_passed = reachability_healthy and loss_healthy and rtt_healthy and qdisc_absent

        criteria_details = {
            "reachability_healthy": reachability_healthy,
            "loss_observed_pct": loss_observed,
            "loss_threshold_pct": loss_threshold_pct,
            "loss_healthy": loss_healthy,
            "rtt_observed_ms": rtt_observed,
            "rtt_threshold_ms": rtt_threshold_ms,
            "rtt_healthy": rtt_healthy,
            "qdisc_netem_absent": qdisc_absent,
            "tc_qdisc_raw": tc_check.stdout.strip()
        }

        record = IndependentVerificationRecord(
            verification_id=verification_id,
            plan_id=plan_id,
            timestamp=timestamp,
            verification_snapshot=post_snapshot,
            reachability_healthy=reachability_healthy,
            loss_healthy=loss_healthy,
            rtt_healthy=rtt_healthy,
            qdisc_absent=qdisc_absent,
            overall_passed=overall_passed,
            criteria_details=criteria_details
        )

        if not overall_passed:
            raise VerificationError(
                f"Independent verification failed for plan '{plan_id}': "
                f"RTT={rtt_observed}ms (max {rtt_threshold_ms}), loss={loss_observed}% (max {loss_threshold_pct}), "
                f"qdisc_netem_absent={qdisc_absent}"
            )

        return record
