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


def test_metrics_predicted_only_class_false_positive_accounting():
    """
    Verifies that a predicted-only label (e.g., UNKNOWN_COMPOSITE_ANOMALY) is
    included in class accounting and correctly counted as a false positive,
    preventing artificial inflation of precision and Macro-F1.
    """
    run_novel = ExperimentRun(
        run_id="run-test-fp-1",
        timestamp="2026-10-20T00:00:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="CASE_04",
        ground_truth_fault_label="NOVEL_COMPOSITE_ANOMALY",
        predicted_fault_label="UNKNOWN_COMPOSITE_ANOMALY",
        start_time="2026-10-20T00:00:00Z",
        end_time="2026-10-20T00:00:01Z",
        is_completed=True
    )
    run_correct = ExperimentRun(
        run_id="run-test-fp-2",
        timestamp="2026-10-20T00:00:02Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="CASE_01",
        ground_truth_fault_label="HIGH_LATENCY_CONGESTION",
        predicted_fault_label="HIGH_LATENCY_CONGESTION",
        start_time="2026-10-20T00:00:02Z",
        end_time="2026-10-20T00:00:03Z",
        is_completed=True
    )

    metrics = calculate_evaluation_metrics([run_novel, run_correct], EvaluationEnvironment.SIMULATED)

    assert metrics["accuracy"].status == MetricStatus.MEASURED
    assert metrics["accuracy"].value == 50.0
    assert metrics["accuracy"].numerator == 1.0
    assert metrics["accuracy"].denominator == 2.0

    # Without the union of classes fix, precision was artificially 100% because UNKNOWN_COMPOSITE_ANOMALY was omitted from FP.
    # With the fix, fp_total = 1 (from UNKNOWN_COMPOSITE_ANOMALY), so precision = 1 / (1 + 1) = 50.0%.
    assert metrics["precision"].status == MetricStatus.MEASURED
    assert metrics["precision"].value == 50.0
    assert metrics["precision"].numerator == 1.0
    assert metrics["precision"].denominator == 2.0

    assert metrics["recall"].status == MetricStatus.MEASURED
    assert metrics["recall"].value == 50.0

    # Macro-F1: 3 classes in union:
    # 1. HIGH_LATENCY_CONGESTION: F1 = 1.0
    # 2. NOVEL_COMPOSITE_ANOMALY: F1 = 0.0 (FN=1)
    # 3. UNKNOWN_COMPOSITE_ANOMALY: F1 = 0.0 (FP=1)
    # Mean F1 = (1.0 + 0.0 + 0.0) / 3 = 33.33%
    assert metrics["macro_f1_score"].status == MetricStatus.MEASURED
    assert metrics["macro_f1_score"].value == 33.33


def test_metrics_literal_mismatch_no_credit_between_novel_and_unknown():
    """
    Verifies that UNKNOWN_COMPOSITE_ANOMALY is not credited as a correct
    diagnosis when ground truth is NOVEL_COMPOSITE_ANOMALY under literal equality.
    """
    run = ExperimentRun(
        run_id="run-mismatch-1",
        timestamp="2026-10-20T00:00:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="CASE_04",
        ground_truth_fault_label="NOVEL_COMPOSITE_ANOMALY",
        predicted_fault_label="UNKNOWN_COMPOSITE_ANOMALY",
        start_time="2026-10-20T00:00:00Z",
        end_time="2026-10-20T00:00:01Z",
        is_completed=True
    )

    metrics = calculate_evaluation_metrics([run], EvaluationEnvironment.SIMULATED)

    assert metrics["accuracy"].status == MetricStatus.MEASURED
    assert metrics["accuracy"].value == 0.0
    assert metrics["accuracy"].numerator == 0.0
    assert metrics["precision"].value == 0.0
    assert metrics["recall"].value == 0.0
    assert metrics["f1_score"].value == 0.0
    assert metrics["macro_f1_score"].value == 0.0
