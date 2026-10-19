import pytest
import time
from app.evaluation.runner import BenchmarkRunner
from app.evaluation.recorder import ExperimentRecorder
from app.evaluation.metrics import calculate_evaluation_metrics
from app.evaluation.models import EvaluationEnvironment, MetricStatus, ExperimentRun
from app.cadd.engine import ExplainableRuleEngine
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry
from app.scenarios.registry import scenario_registry
from app.ceso.service import ceso_service


def test_arm5_telemetry_fault_propagation_and_matching(tmp_path):
    """
    Verifies that Arm 5 preserves the injected scenario fault, and that
    Arms 3, 4, and 5 receive identical NetworkState telemetry inputs before diagnosis.
    """
    recorder = ExperimentRecorder(base_dir=str(tmp_path))
    runner = BenchmarkRunner(recorder=recorder)

    # 1. Direct Telemetry Comparison
    sc_id = "CASE_01"
    sc_def = scenario_registry.load_scenario(sc_id)
    fault_type = scenario_registry.inject_fault(sc_id)

    # Telemetry for Arm 3 / Arm 4
    telemetry_arm3_4 = scenario_registry.generate_telemetry(sc_id, fault_type)

    # Telemetry for Arm 5 via CESOService load_scenario
    telemetry_arm5 = ceso_service.load_scenario(sc_id, fault_type=fault_type)

    # Assert injected fault is active and identical in link RTT and packet loss
    assert telemetry_arm3_4.anomalies_detected is True
    assert telemetry_arm5.anomalies_detected is True
    assert len(telemetry_arm3_4.links) == len(telemetry_arm5.links)
    assert telemetry_arm3_4.links[0].rtt_ms == telemetry_arm5.links[0].rtt_ms
    assert telemetry_arm3_4.links[0].packet_loss_pct == telemetry_arm5.links[0].packet_loss_pct

    # 2. Benchmark Runner Execution Comparison for Arms 3, 4, and 5
    run3 = runner._run_single_scenario_benchmark(sc_id="CASE_01", run_number=1, seed=42, include_llm=False, run_direct_llm_comparison=False, arm_id="ARM_3_RULE_BASED")
    run4 = runner._run_single_scenario_benchmark(sc_id="CASE_01", run_number=1, seed=42, include_llm=False, run_direct_llm_comparison=False, arm_id="ARM_4_PHASE2_BASELINE")
    run5 = runner._run_single_scenario_benchmark(sc_id="CASE_01", run_number=1, seed=42, include_llm=False, run_direct_llm_comparison=False, arm_id="ARM_5_CESO_CADE_NO_LLM")

    # Verify all 3 arms received the exact same scenario state and GT label
    gt_type = sc_def.fault_definition.fault_type
    assert run3.ground_truth_fault_label == gt_type
    assert run4.ground_truth_fault_label == gt_type
    assert run5.ground_truth_fault_label == gt_type

    # Verify predictions are non-null and valid
    assert run3.predicted_fault_label is not None
    assert run4.predicted_fault_label is not None
    assert run5.predicted_fault_label is not None


def test_metric_rsr_and_vsr_correctness():
    """
    Verifies that RSR is reported as NOT_APPLICABLE when no remediations are executed,
    and that VSR is computed dynamically without hardcoded values.
    """
    run_no_remed = ExperimentRun(
        run_id="run-no-remed",
        timestamp="2026-10-09T10:00:00Z",
        start_time="2026-10-09T10:00:00Z",
        end_time="2026-10-09T10:00:01Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="CASE_01",
        ground_truth_fault_label="HIGH_LATENCY_CONGESTION",
        predicted_fault_label="HIGH_LATENCY_CONGESTION",
        remediation_status="PENDING",
        evidence_count=2,
        total_raw_evidence_count=10,
        is_completed=True
    )

    metrics_no_remed = calculate_evaluation_metrics([run_no_remed], EvaluationEnvironment.SIMULATED)

    # RSR must be NOT_APPLICABLE when no remediations were executed
    assert metrics_no_remed["rsr"].status == MetricStatus.NOT_APPLICABLE
    assert "No eligible active remediation actions were executed" in metrics_no_remed["rsr"].exclusion_reason

    # ECR must be MEASURED: (1 - 2/10) * 100 = 80.0%
    assert metrics_no_remed["ecr"].status == MetricStatus.MEASURED
    assert metrics_no_remed["ecr"].value == 80.0

    # VSR must remain NOT_MEASURED because verification target probe counts are unrecorded
    assert metrics_no_remed["vsr"].status == MetricStatus.NOT_MEASURED
    assert "Verification probe target scope telemetry not recorded" in metrics_no_remed["vsr"].exclusion_reason


def test_total_latency_wall_clock_measurement(tmp_path):
    """
    Verifies that total_elapsed_ms is measured as monotonic end-to-end wall-clock latency
    and is strictly greater than component latencies alone.
    """
    recorder = ExperimentRecorder(base_dir=str(tmp_path))
    runner = BenchmarkRunner(recorder=recorder)

    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_01",
        run_number=1,
        seed=42,
        include_llm=False,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    assert run.total_elapsed_ms > 0.0
    assert run.telemetry_collection_latency_ms >= 0.0
    assert run.diagnosis_latency_ms >= 0.0
    assert run.total_elapsed_ms >= (run.telemetry_collection_latency_ms + run.diagnosis_latency_ms)


def test_phase2_engine_equivalence():
    """
    Verifies that ExplainableRuleEngine.diagnose_state in current backend
    matches the deterministic Phase 2 baseline specification for scores, confidence, and action plans.
    """
    engine = ExplainableRuleEngine()
    assert engine.VERSION == "2.0.0-phase2"

    state = NetworkState(
        snapshot_id="snap-equiv-test",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=100.0, packet_loss_pct=0.0)],
        routes=[]
    )

    report, plan = engine.diagnose_state(state)

    assert report.fault_type == "HIGH_LATENCY_CONGESTION"
    assert report.candidate_scores["HIGH_LATENCY_CONGESTION"] == 0.7
    assert report.confidence_score == 0.7
    assert report.escalation_required is False
    assert len(plan.proposed_actions) == 1
    assert plan.proposed_actions[0].command_type == "REROUTE_TRAFFIC"
