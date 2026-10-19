"""
Real Linux Network Namespace Testbed Integration Test.

Runs ONLY on Linux hosts with root / CAP_NET_ADMIN privileges.
Skipped automatically on Windows / non-supported environments without faking success.
"""

import sys
import pytest
from app.research_v2.testbed.capabilities import check_testbed_capabilities
from app.research_v2.testbed.topology import ResearchTopology
from app.research_v2.testbed.telemetry import RealTelemetryCollector
from app.research_v2.testbed.faults import RealFaultInjector
from app.research_v2.testbed.remediation import RealRemediationExecutor
from app.research_v2.testbed.verification import IndependentVerifier
from app.research_v2.testbed.models import RemediationPlan

caps = check_testbed_capabilities()
REASON_NOT_LINUX = f"Real Linux Network Namespace testbed requires Linux OS & root netns privileges (host: {sys.platform}, ready: {caps['ready']})"


@pytest.mark.skipif(not caps["ready"], reason=REASON_NOT_LINUX)
def test_real_linux_testbed_e2e_flow():
    """
    Complete real Linux netns E2E causal experiment.
    """
    try:
        # 1. Create Topology
        top_state = ResearchTopology.create_topology()
        assert top_state["is_present"] is True

        # 2. Baseline Telemetry
        base_snap = RealTelemetryCollector.collect_telemetry("test-exp-001")
        assert base_snap.is_healthy is True
        assert base_snap.link_latency.packet_loss_pct < 5.0

        # 3. Inject Real tc netem Fault
        fault_def = RealFaultInjector.create_high_latency_fault("flt-test-01")
        inj_rec = RealFaultInjector.inject_fault(fault_def, "test-exp-001")
        assert inj_rec.status == "ACTIVE"
        assert inj_rec.activation_verified is True
        assert inj_rec.observed_rtt_ms > 50.0

        # 4. Execute Real Remediation (tc qdisc del dev veth-r1-r2 root)
        plan = RemediationPlan(
            plan_id="plan-test-01",
            fault_id=fault_def.fault_id,
            remediation_type="REMOVE_NETEM_QDISC",
            target_namespace=fault_def.target_namespace,
            target_interface=fault_def.target_interface,
            remediation_command=fault_def.reset_command
        )
        rem_rec = RealRemediationExecutor.execute_remediation(plan, "test-exp-001")
        assert rem_rec.status == "EXECUTED"

        # 5. Independent Verification
        ver_rec = IndependentVerifier.verify_recovery(
            plan_id=plan.plan_id,
            target_ns=fault_def.target_namespace,
            target_interface=fault_def.target_interface,
            experiment_id="test-exp-001"
        )
        assert ver_rec.overall_passed is True
        assert ver_rec.qdisc_absent is True
        assert ver_rec.loss_healthy is True

    finally:
        # 6. Guaranteed Cleanup
        ResearchTopology.destroy_topology()
        assert ResearchTopology.is_topology_present() is False
