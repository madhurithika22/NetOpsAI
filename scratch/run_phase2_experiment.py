"""
End-to-End Real Telemetry Diagnosis & Verification Experiment for NetOps Research V2 Phase 2.

Executes a controlled Linux network namespace experiment:
1. Platform capability check
2. 4-node research topology setup
3. Baseline observations (30 ICMP probes)
4. Real tc netem fault injection (HIGH_LATENCY_CONGESTION: delay 150ms, loss 20%)
5. Independent fault activation confirmation
6. Degraded telemetry collection (50 ICMP probes, qdisc counters) & operational state extraction
7. Ground-truth-independent CADE diagnosis (candidate scores, confidence, escalation decision)
8. Real remediation execution (reset command tc qdisc del)
9. Independent recovery verification via fresh telemetry probes and qdisc inspection
10. Phase 2 Research Result Validator assertion
11. Topology cleanup
12. Auditable Phase 2 JSON experiment record persistence (new immutable record)
"""

import os
import sys
import uuid
import json
from datetime import datetime, timezone

# Ensure backend directory is in python module search path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.research_v2.guard import ResearchExecutionContext, Phase2ResearchValidator
from app.research_v2.testbed.capabilities import check_testbed_capabilities
from app.research_v2.testbed.topology import ResearchTopology
from app.research_v2.testbed.telemetry import RealTelemetryCollector
from app.research_v2.testbed.faults import RealFaultInjector
from app.research_v2.testbed.remediation import RealRemediationExecutor
from app.research_v2.testbed.verification import IndependentVerifier
from app.research_v2.testbed.recorder import ExperimentRecorder
from app.research_v2.testbed.models import RemediationPlan
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry
from app.cadd.engine import ExplainableRuleEngine


def run_phase2_experiment():
    print("==================================================")
    print("NETOPS RESEARCH V2 — PHASE 2 REAL DIAGNOSIS EXPERIMENT (CORRECTED)")
    print("==================================================")

    experiment_id = f"exp-phase2-{uuid.uuid4().hex[:8]}"
    run_id = f"run-p2-{uuid.uuid4().hex[:6]}"
    output_dir = "scratch/research_v2/phase2/runs"
    os.makedirs(output_dir, exist_ok=True)
    recorder = ExperimentRecorder(output_dir=output_dir)

    caps = check_testbed_capabilities()
    print(f"\n[1/10] Capability Detection Check:")
    print(f"  - Linux Platform: {caps['linux']} (OS: {sys.platform})")
    print(f"  - ip command:     {caps['ip_available']}")
    print(f"  - tc command:     {caps['tc_available']}")
    print(f"  - ping command:   {caps['ping_available']}")
    print(f"  - netns support:  {caps['netns_available']}")
    print(f"  - CAP_NET_ADMIN:  {caps['net_admin_available']}")
    print(f"  -> READY STATUS:  {caps['ready']}")

    if not caps["ready"]:
        print("\n" + "="*50)
        print("PHASE 2 BLOCKED — REAL TESTBED COULD NOT BE EXECUTED")
        print("="*50)
        return {
            "status": "BLOCKED",
            "experiment_id": experiment_id,
            "reason": caps.get('netns_error') or "Platform lacks Linux network namespace support"
        }

    engine = ExplainableRuleEngine()

    with ResearchExecutionContext(mode="research_real"):
        baseline_snap = None
        fault_def = None
        fault_inj_rec = None
        degraded_snap = None
        diag_report = None
        diag_plan = None
        rem_plan = None
        rem_exec_rec = None
        verification_rec = None
        final_status = "UNKNOWN"

        try:
            # 2. Topology Setup
            print("\n[2/10] Creating 4-node research topology...")
            ResearchTopology.create_topology()
            print("  Topology created successfully.")

            # 3. Baseline Measurement (30 ICMP probes)
            print("\n[3/10] Measuring baseline telemetry (30 probes)...")
            baseline_snap = RealTelemetryCollector.collect_telemetry(experiment_id, probe_count=30)
            print(f"  Baseline RTT avg: {baseline_snap.link_latency.rtt_avg_ms} ms")
            print(f"  Baseline Loss:    {baseline_snap.link_latency.packet_loss_pct} %")
            print(f"  Baseline Healthy: {baseline_snap.is_healthy}")

            if not baseline_snap.is_healthy:
                final_status = "BASELINE_FAILED"
                raise RuntimeError("Baseline network is unhealthy prior to fault injection")

            # 4. Fault Injection (tc netem)
            print("\n[4/10] Injecting real tc netem fault (delay=150ms, loss=20%)...")
            fault_def = RealFaultInjector.create_high_latency_fault()
            fault_inj_rec = RealFaultInjector.inject_fault(fault_def, experiment_id)
            print(f"  Fault status: {fault_inj_rec.status}")
            print(f"  Observed RTT: {fault_inj_rec.observed_rtt_ms} ms")
            print(f"  Observed Loss:{fault_inj_rec.observed_loss_pct} %")

            # 5. Fault Activation Verification
            print("\n[5/10] Verifying fault activation...")
            if not fault_inj_rec.activation_verified:
                final_status = "FAULT_ACTIVATION_FAILED"
                raise RuntimeError("Fault injection executed but telemetry did not observe impairment")
            print("  Fault activation verified.")

            # 6. Degraded Telemetry (50 ICMP probes) & Ground-Truth-Independent CADE Diagnosis
            print("\n[6/10] Collecting degraded telemetry (50 probes & qdisc counters) & executing CADE diagnosis...")
            degraded_snap = RealTelemetryCollector.collect_telemetry(experiment_id, probe_count=50)

            op_links = [
                LinkLatency(
                    source_node=degraded_snap.link_latency.source_node,
                    target_node=degraded_snap.link_latency.target_node,
                    rtt_ms=degraded_snap.link_latency.rtt_avg_ms,
                    packet_loss_pct=degraded_snap.link_latency.packet_loss_pct,
                    status="DEGRADED" if not degraded_snap.is_healthy else "HEALTHY"
                )
            ]

            op_interfaces = {}
            for if_name, if_rec in degraded_snap.interface_states.items():
                op_interfaces[if_name] = InterfaceState(
                    name=if_rec.name,
                    is_up=if_rec.is_up,
                    mtu=if_rec.mtu,
                    rx_errors=if_rec.rx_errors,
                    tx_errors=if_rec.tx_errors,
                    rx_drops=if_rec.rx_drops,
                    tx_drops=if_rec.tx_drops
                )

            op_routes = [
                RouteEntry(destination=r.destination, interface=r.raw_route.split(":")[0], metric=10)
                for r in degraded_snap.routes
            ]

            operational_state = NetworkState(
                snapshot_id=degraded_snap.snapshot_id,
                timestamp=degraded_snap.timestamp,
                topology_id="netops-linux-testbed",  # Generic operational topology identifier
                interfaces=op_interfaces,
                links=op_links,
                routes=op_routes,
                nodes={},
                anomalies_detected=not degraded_snap.is_healthy
            )

            diag_report, diag_plan = engine.diagnose_state(operational_state)
            print(f"  Predicted Diagnosis: {diag_report.fault_type}")
            print(f"  Computed Confidence:{diag_report.confidence_score}")
            print(f"  Escalation Required:{diag_report.escalation_required}")
            print(f"  Candidate Scores:   {json.dumps(diag_report.candidate_scores)}")

            # 7. Remediation Execution
            print("\n[7/10] Executing real remediation (reset command tc qdisc del)...")
            rem_plan = RemediationPlan(
                plan_id=f"plan-rem-{uuid.uuid4().hex[:6]}",
                fault_id=fault_def.fault_id,
                remediation_type="RESET_TC_NETEM",
                target_namespace=fault_def.target_namespace,
                target_interface=fault_def.target_interface,
                remediation_command=fault_def.reset_command
            )
            rem_exec_rec = RealRemediationExecutor.execute_remediation(rem_plan, experiment_id)
            print(f"  Remediation Status: {rem_exec_rec.status}")

            # 8. Independent Verification of Recovery
            print("\n[8/10] Performing independent post-remediation verification...")
            verification_rec = IndependentVerifier.verify_recovery(
                plan_id=rem_plan.plan_id,
                target_ns=fault_def.target_namespace,
                target_interface=fault_def.target_interface,
                experiment_id=experiment_id
            )
            print(f"  Verification Overall Passed: {verification_rec.overall_passed}")
            print(f"  Post-Recovery RTT:           {verification_rec.criteria_details['rtt_observed_ms']} ms")
            print(f"  Post-Recovery Loss:          {verification_rec.criteria_details['loss_observed_pct']} %")

            final_status = "RECOVERED" if (diag_report.fault_type == "HIGH_LATENCY_CONGESTION" and verification_rec.overall_passed) else "DIAGNOSIS_OR_VERIFICATION_FAILED"

        except Exception as e:
            print(f"\n[!] Experiment execution error: {str(e)}")
            if final_status == "UNKNOWN":
                final_status = "EXECUTION_FAILED"

        finally:
            print("\n[9/10] Cleaning up research topology...")
            try:
                ResearchTopology.destroy_topology()
                print("  Cleanup completed.")
            except Exception as ce:
                print(f"  Cleanup error: {str(ce)}")

            # 10. Assemble Record & Run Phase 2 Validator Guard
            print("\n[10/10] Assembling & validating Phase 2 experiment record...")
            exp_record = recorder.create_record(
                experiment_id=experiment_id,
                run_id=run_id,
                final_status=final_status,
                topology_def={"topology_id": "netops-linux-testbed", "node_count": 4, "link_count": 3},
                baseline_snapshot=baseline_snap,
                fault_def=fault_def,
                fault_inj_record=fault_inj_rec,
                remediation_plan=rem_plan,
                remediation_exec_record=rem_exec_rec,
                verification_record=verification_rec
            )

            record_dict = exp_record.model_dump(mode="json")
            if diag_report:
                record_dict["diagnosis_record"] = diag_report.model_dump(mode="json")

            # Associate evaluation ground-truth AFTER operational prediction persistence
            record_dict["evaluation_ground_truth"] = {
                "injected_fault_type": fault_def.fault_type if fault_def else "UNKNOWN",
                "injected_target": fault_def.target_interface if fault_def else "UNKNOWN",
                "diagnosis_correct": (diag_report.fault_type == "HIGH_LATENCY_CONGESTION") if diag_report else False
            }

            # Run Phase 2 validator guard
            validator_passed = Phase2ResearchValidator.validate_record(record_dict)
            print(f"  Phase 2 Research Validator Passed: {validator_passed}")

            filepath = os.path.join(output_dir, f"{experiment_id}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=2)

            print(f"\nPhase 2 corrected experiment record persisted to: {filepath}")
            print(f"Final Status: {final_status}")

            return {
                "status": final_status,
                "experiment_id": experiment_id,
                "filepath": filepath,
                "diagnosis": diag_report.fault_type if diag_report else None,
                "confidence": diag_report.confidence_score if diag_report else None,
                "candidate_scores": diag_report.candidate_scores if diag_report else None,
                "validator_passed": validator_passed
            }


if __name__ == "__main__":
    run_phase2_experiment()
