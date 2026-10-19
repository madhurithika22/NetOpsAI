import pytest
from app.evaluation.runner import BenchmarkRunner, AUTHORIZED_ARMS, UNIMPLEMENTED_ARMS, BLOCKED_ARMS
from app.cadd.engine import ExplainableRuleEngine
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry
from app.evaluation.recorder import ExperimentRecorder


def test_arm_dispatch_validation(tmp_path):
    recorder = ExperimentRecorder(base_dir=str(tmp_path))
    runner = BenchmarkRunner(recorder=recorder)

    # Authorized arms should complete successfully
    for valid_arm in sorted(AUTHORIZED_ARMS):
        run = runner._run_single_scenario_benchmark(
            sc_id="CASE_01",
            run_number=1,
            seed=42,
            include_llm=False,
            run_direct_llm_comparison=False,
            arm_id=valid_arm
        )
        assert run.arm_id == valid_arm
        assert run.is_completed is True

    # Unimplemented or blocked arms must fail closed with ValueError
    invalid_arms = list(UNIMPLEMENTED_ARMS | BLOCKED_ARMS | {"ARM_UNKNOWN_INVALID"})
    for invalid_arm in invalid_arms:
        with pytest.raises(ValueError, match="is not authorized or implemented"):
            runner._run_single_scenario_benchmark(
                sc_id="CASE_01",
                run_number=1,
                seed=42,
                include_llm=False,
                run_direct_llm_comparison=False,
                arm_id=invalid_arm
            )


def test_arm3_vs_arm4_algorithmic_distinction():
    engine = ExplainableRuleEngine()
    
    # State with moderate high latency (60ms) and high loss (35%)
    state = NetworkState(
        snapshot_id="snap-test-diff",
        interfaces={"eth1": InterfaceState(name="eth1", is_up=True, throughput_bps=1.0)},
        links=[LinkLatency(source_node="rtr1", target_node="rtr2", rtt_ms=60.0, packet_loss_pct=35.0, status="DEGRADED")],
        routes=[]
    )

    # Arm 3: Rule-Based discrete matching
    report_arm3, _ = engine.diagnose_rule_based(state)
    assert report_arm3.algorithm_version == "1.0.0-arm3-rule-based"
    # Rule precedence evaluates RULE_HIGH_LATENCY first for link rtt_ms > 50.0
    assert report_arm3.fault_type == "HIGH_LATENCY_CONGESTION"

    # Arm 4: Continuous candidate scoring S(c)
    report_arm4, _ = engine.diagnose_state(state)
    assert report_arm4.algorithm_version == "2.0.0-phase2"
    # Continuous scoring evaluates f_loss = (35-10)/30 = 0.833, f_lat = (60-50)/50 = 0.20
    # Since f_loss >= f_lat, candidate score for PACKET_LOSS is 0.8*0.833 + 0.2*0.2 = 0.7066
    # HIGH_LATENCY_CONGESTION requires f_lat > f_loss so its score is 0.0
    assert report_arm4.fault_type == "PACKET_LOSS"

    # Confirm distinct predictions for identical input
    assert report_arm3.fault_type != report_arm4.fault_type


def test_arm4_frozen_phase2_baseline_preservation():
    engine = ExplainableRuleEngine()
    assert engine.VERSION == "2.0.0-phase2"

    # Baseline test state with single down interface
    state = NetworkState(
        snapshot_id="snap-test-frozen",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=False)},
        links=[],
        routes=[]
    )

    report, plan = engine.diagnose_state(state)
    assert report.algorithm_version == "2.0.0-phase2"
    assert report.fault_type == "INTERFACE_FAILURE"
    assert report.confidence_score == 1.0
    assert len(plan.proposed_actions) == 1
    assert plan.proposed_actions[0].command_type == "SET_INTERFACE_STATE"


def test_arm5_ceso_invocation_no_llm(tmp_path):
    recorder = ExperimentRecorder(base_dir=str(tmp_path))
    runner = BenchmarkRunner(recorder=recorder)

    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_01",
        run_number=1,
        seed=42,
        include_llm=True,  # Even if include_llm is True, Arm 5 must NOT escalate to LLM
        run_direct_llm_comparison=False,
        arm_id="ARM_5_CESO_CADE_NO_LLM"
    )

    assert run.arm_id == "ARM_5_CESO_CADE_NO_LLM"
    assert run.llm_escalated is False
    assert run.llm_invocation_count == 0
    assert run.ceso_context is not None
    assert "snapshot_id" in run.ceso_context


def test_ground_truth_isolation(tmp_path):
    recorder = ExperimentRecorder(base_dir=str(tmp_path))
    runner = BenchmarkRunner(recorder=recorder)

    # Run CASE_04 with include_llm=False and ensure scenario ID CASE_04 does NOT trigger forced LLM escalation
    run_c4 = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=42,
        include_llm=False,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )
    # Forced sc_id == "CASE_04" leak removed: escalation is based strictly on confidence/rule
    assert run_c4.llm_escalated is False


def test_timing_instrumentation(tmp_path):
    recorder = ExperimentRecorder(base_dir=str(tmp_path))
    runner = BenchmarkRunner(recorder=recorder)

    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_02",
        run_number=1,
        seed=42,
        include_llm=False,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    assert run.telemetry_collection_latency_ms >= 0.0
    assert run.diagnosis_latency_ms >= 0.0
    assert run.llm_latency_ms == 0.0
    assert run.total_elapsed_ms >= (run.telemetry_collection_latency_ms + run.diagnosis_latency_ms)
