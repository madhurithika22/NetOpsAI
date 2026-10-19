"""
End-to-End Real Experiment Runner for NetOps Research V2 Phase 1.

Executes the HIGH_LATENCY_CONGESTION real causal experiment sequence:
1. Capability check
2. Topology creation
3. Baseline telemetry measurement
4. Real tc netem fault injection
5. Fault activation verification
6. Real tc qdisc del remediation execution
7. Independent recovery verification
8. Topology cleanup
9. Auditable JSON experiment record persistence
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure backend directory is in python module search path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.research_v2.guard import ResearchExecutionContext
from app.research_v2.testbed.capabilities import check_testbed_capabilities
from app.research_v2.testbed.topology import ResearchTopology
from app.research_v2.testbed.telemetry import RealTelemetryCollector
from app.research_v2.testbed.faults import RealFaultInjector
from app.research_v2.testbed.remediation import RealRemediationExecutor
from app.research_v2.testbed.verification import IndependentVerifier
from app.research_v2.testbed.recorder import ExperimentRecorder
from app.research_v2.testbed.models import RemediationPlan


def run_phase1_experiment():
    print("==================================================")
    print("NETOPS RESEARCH V2 — PHASE 1 E2E REAL EXPERIMENT")
    print("==================================================")

    experiment_id = f"exp-phase1-{uuid.uuid4().hex[:8]}"
    run_id = f"run-{uuid.uuid4().hex[:6]}"
    recorder = ExperimentRecorder()

    # 1. Capability Check
    caps = check_testbed_capabilities()
    print(f"\n[1/8] Capability Detection Check:")
    print(f"  - Linux Platform: {caps['linux']} (OS: {sys.platform})")
    print(f"  - ip command:     {caps['ip_available']}")
    print(f"  - tc command:     {caps['tc_available']}")
    print(f"  - ping command:   {caps['ping_available']}")
    print(f"  - netns support:  {caps['netns_available']}")
    print(f"  - CAP_NET_ADMIN:  {caps['net_admin_available']}")
    print(f"  -> READY STATUS:  {caps['ready']}")

    if not caps["ready"]:
        print("\n" + "="*50)
        print("PHASE 1 BLOCKED — REAL TESTBED COULD NOT BE EXECUTED")
        print("="*50)
        print(f"Reason: {caps.get('netns_error') or 'Host environment lacks Linux network namespace support'}")

        # Save failed experiment record
        record = recorder.create_record(
            experiment_id=experiment_id,
            run_id=run_id,
            final_status="CAPABILITY_CHECK_FAILED",
            topology_def={"error": "Platform lacks Linux network namespace support"}
        )
        json_path = recorder.save_record(record)
        print(f"\nSaved capability failure audit record to: {json_path}")
        return {
            "status": "BLOCKED",
            "experiment_id": experiment_id,
            "reason": caps.get('netns_error') or "Platform lacks Linux network namespace support",
            "json_path": json_path,
            "caps": caps
        }

    # If capabilities are ready, run the full real execution inside research_real guard
    with ResearchExecutionContext(mode="research_real"):
        baseline_snap = None
        fault_def = None
        fault_inj_rec = None
        plan = None
        rem_exec_rec = None
        ver_rec = None
        final_status = "UNKNOWN"

        try:
            # 2. Topology Creation
            print("\n[2/8] Creating 4-node research topology (rns-host-a, rns-router-1, rns-router-2, rns-host-b)...")
            top_state = ResearchTopology.create_topology()
            print("  Topology created successfully.")

            # 3. Baseline Measurement
            print("\n[3/8] Measuring baseline telemetry (rns-host-a -> rns-host-b 10.0.3.10)...")
            baseline_snap = RealTelemetryCollector.collect_telemetry(experiment_id)
            print(f"  Baseline RTT avg: {baseline_snap.link_latency.rtt_avg_ms} ms")
            print(f"  Baseline Loss:    {baseline_snap.link_latency.packet_loss_pct} %")
            print(f"  Baseline Healthy: {baseline_snap.is_healthy}")

            if not baseline_snap.is_healthy:
                final_status = "BASELINE_FAILED"
                raise RuntimeError("Baseline network is unhealthy prior to fault injection")

            # 4. Fault Injection (HIGH_LATENCY_CONGESTION)
            print("\n[4/8] Injecting real tc netem fault (delay=150ms, loss=20%) on rns-router-1:veth-r1-r2...")
            fault_def = RealFaultInjector.create_high_latency_fault()
            fault_inj_rec = RealFaultInjector.inject_fault(fault_def, experiment_id)
            print(f"  Fault status: {fault_inj_rec.status}")
            print(f"  Observed RTT: {fault_inj_rec.observed_rtt_ms} ms")
            print(f"  Observed Loss:{fault_inj_rec.observed_loss_pct} %")

            # 5. Fault Activation Verification
            print("\n[5/8] Verifying fault activation...")
            if not fault_inj_rec.activation_verified:
                final_status = "FAULT_ACTIVATION_FAILED"
                raise RuntimeError("Fault injection executed but telemetry did not observe impairment")
            print("  Fault activation verified.")

            # 6. Real Remediation Execution (tc qdisc del dev veth-r1-r2 root)
            print("\n[6/8] Executing real remediation command (tc qdisc del dev veth-r1-r2 root)...")
            plan = RemediationPlan(
                plan_id=f"plan-{uuid.uuid4().hex[:8]}",
                fault_id=fault_def.fault_id,
                remediation_type="REMOVE_NETEM_QDISC",
                target_namespace=fault_def.target_namespace,
                target_interface=fault_def.target_interface,
                remediation_command=fault_def.reset_command
            )
            rem_exec_rec = RealRemediationExecutor.execute_remediation(plan, experiment_id)
            print(f"  Remediation status: {rem_exec_rec.status}")

            # 7. Independent Post-Remediation Recovery Verification
            print("\n[7/8] Independently verifying recovery...")
            ver_rec = IndependentVerifier.verify_recovery(
                plan_id=plan.plan_id,
                target_ns=fault_def.target_namespace,
                target_interface=fault_def.target_interface,
                experiment_id=experiment_id
            )
            print(f"  Recovery overall passed: {ver_rec.overall_passed}")
            print(f"  Post RTT observed:       {ver_rec.verification_snapshot.link_latency.rtt_avg_ms} ms")
            print(f"  Post Loss observed:      {ver_rec.verification_snapshot.link_latency.packet_loss_pct} %")
            print(f"  qdisc netem absent:      {ver_rec.qdisc_absent}")

            final_status = "RECOVERED" if ver_rec.overall_passed else "RECOVERY_FAILED"

        except Exception as e:
            print(f"\n[!] Experiment execution error: {str(e)}")
            if final_status == "UNKNOWN":
                final_status = "EXECUTION_FAILED"

        finally:
            # 8. Cleanup & Record Persistence
            print("\n[8/8] Cleaning up research topology namespaces...")
            try:
                ResearchTopology.destroy_topology()
                print("  Cleanup completed.")
            except Exception as ce:
                print(f"  Cleanup error: {str(ce)}")
                final_status = "CLEANUP_FAILED"

            record = recorder.create_record(
                experiment_id=experiment_id,
                run_id=run_id,
                final_status=final_status,
                topology_def=ResearchTopology.get_topology_state(),
                baseline_snapshot=baseline_snap,
                fault_def=fault_def,
                fault_inj_record=fault_inj_rec,
                remediation_plan=plan,
                remediation_exec_record=rem_exec_rec,
                verification_record=ver_rec
            )
            json_path = recorder.save_record(record)
            print(f"\nExperiment record saved to: {json_path}")
            print(f"Final Status: {final_status}")

            return {
                "status": final_status,
                "experiment_id": experiment_id,
                "json_path": json_path
            }


if __name__ == "__main__":
    run_phase1_experiment()
