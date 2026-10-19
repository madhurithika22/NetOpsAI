import pytest
from app.evaluation.models import (
    ExperimentRun, EvaluationEnvironment, MetricStatus
)
from app.evaluation.metrics import calculate_evaluation_metrics


def test_metrics_empty_runs():
    metrics = calculate_evaluation_metrics([], EvaluationEnvironment.SIMULATED)
    assert metrics["accuracy"].status == MetricStatus.NOT_MEASURED
    assert metrics["accuracy"].sample_count == 0
    assert metrics["ecr"].status == MetricStatus.NOT_MEASURED
    assert metrics["urr"].status == MetricStatus.NOT_MEASURED


def test_metrics_simulated_runs_calculation():
    run1 = ExperimentRun(
        run_id="run-1",
        timestamp="2026-10-03T10:00:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="HIGH_LATENCY_CONGESTION",
        ground_truth_fault_label="HIGH_LATENCY_CONGESTION",
        predicted_fault_label="HIGH_LATENCY_CONGESTION",
        ground_truth_location="netops-rtr1",
        predicted_location="netops-rtr1",
        start_time="2026-10-03T10:00:00Z",
        end_time="2026-10-03T10:00:01Z",
        diagnosis_latency_ms=100.0,
        evidence_selected=["rtt_ms", "packet_loss_pct"],
        evidence_count=2,
        total_raw_evidence_count=10,
        token_count=100,
        raw_token_count=500,
        llm_invocation_count=0,
        llm_escalated=False,
        pre_llm_diagnosis="HIGH_LATENCY_CONGESTION",
        post_llm_diagnosis="HIGH_LATENCY_CONGESTION",
        verification_scope="INTER_ROUTER_LINK",
        remediation_decision="APPROVED",
        remediation_status="EXECUTED",
        verification_result="VERIFIED_HEALTHY",
        is_completed=True
    )

    run2 = ExperimentRun(
        run_id="run-2",
        timestamp="2026-10-03T10:05:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="PACKET_LOSS",
        ground_truth_fault_label="PACKET_LOSS",
        predicted_fault_label="HIGH_LATENCY_CONGESTION",
        ground_truth_location="netops-rtr1",
        predicted_location="netops-rtr2",
        start_time="2026-10-03T10:05:00Z",
        end_time="2026-10-03T10:05:01Z",
        diagnosis_latency_ms=200.0,
        evidence_selected=["packet_loss_pct"],
        evidence_count=1,
        total_raw_evidence_count=10,
        token_count=150,
        raw_token_count=500,
        llm_invocation_count=1,
        llm_escalated=True,
        pre_llm_diagnosis="PACKET_LOSS",
        post_llm_diagnosis="HIGH_LATENCY_CONGESTION",
        verification_scope="INTER_ROUTER_LINK",
        remediation_decision="REJECTED_UNSAFE",
        remediation_status="BLOCKED",
        verification_result="SAFETY_POLICY_ENFORCED",
        is_completed=True
    )

    metrics = calculate_evaluation_metrics([run1, run2], EvaluationEnvironment.SIMULATED)

    assert metrics["accuracy"].status == MetricStatus.MEASURED
    assert metrics["accuracy"].value == 50.0

    assert metrics["ecr"].status == MetricStatus.MEASURED
    assert metrics["ecr"].value == 85.0

    assert metrics["trr"].status == MetricStatus.MEASURED
    assert metrics["trr"].value == 75.0

    assert metrics["mttd"].status == MetricStatus.MEASURED
    assert metrics["mttd"].value == 150.0

    assert metrics["lir"].status == MetricStatus.MEASURED
    assert metrics["lir"].value == 50.0

    assert metrics["ee"].status == MetricStatus.MEASURED
    assert metrics["ee"].value == -100.0


def test_metrics_aiops2020_not_measured_safety():
    run = ExperimentRun(
        run_id="run-aiops-1",
        timestamp="2026-10-03T10:00:00Z",
        environment=EvaluationEnvironment.AIOPS_2020,
        dataset_or_scenario_id="AIOps-100",
        ground_truth_fault_label="HIGH_LATENCY_CONGESTION",
        predicted_fault_label="HIGH_LATENCY_CONGESTION",
        start_time="2026-10-03T10:00:00Z",
        end_time="2026-10-03T10:00:00Z",
        is_completed=True
    )

    metrics = calculate_evaluation_metrics([run], EvaluationEnvironment.AIOPS_2020)

    assert metrics["vsr"].status == MetricStatus.NOT_MEASURED
    assert metrics["urr"].status == MetricStatus.NOT_MEASURED
    assert metrics["rsr"].status == MetricStatus.NOT_MEASURED
    assert "No remediation execution loop" in metrics["urr"].exclusion_reason
