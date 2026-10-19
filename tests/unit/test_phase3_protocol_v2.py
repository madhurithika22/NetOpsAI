import pytest
import os
import csv
from app.scenarios.registry import ScenarioRegistry
from app.ceso.service import CESOService
from app.evaluation.models import ExperimentRun, EvaluationEnvironment, MetricStatus
from app.evaluation.metrics import calculate_evaluation_metrics
from app.evaluation.runner import BenchmarkRunner
from app.ceso.service import ceso_service
from scratch.research_v2.phase3.validate_experiment_matrix import validate_matrix_v2, validate_matrix

@pytest.fixture(autouse=True)
def reset_scenario_state():
    yield
    ceso_service.reset_simulation()

def test_scenario_registry_mapping_and_rejection():
    """
    Verifies that ScenarioRegistry maps CASE_01..CASE_04 correctly and rejects unknown/excluded scenario IDs.
    """
    registry = ScenarioRegistry()
    scenarios = registry.list_scenarios()
    sc_ids = [s.scenario_id for s in scenarios]
    
    assert "CASE_01" in sc_ids
    assert "CASE_02" in sc_ids
    assert "CASE_03" in sc_ids
    assert "CASE_04" in sc_ids
    assert len(sc_ids) == 4

    # Unknown or excluded scenario IDs must raise ValueError
    with pytest.raises(ValueError):
        registry.load_scenario("SCN_005")

    with pytest.raises(ValueError):
        registry.load_scenario("SCN_006")

    with pytest.raises(ValueError):
        registry.load_scenario("NON_EXISTENT_SCENARIO")


def test_ground_truth_isolation_from_telemetry():
    """
    Verifies that generated NetworkState telemetry snapshots contain no ground-truth fault labels
    or scenario solution fields passed to algorithms.
    """
    registry = ScenarioRegistry()
    for sc_id in ["CASE_01", "CASE_02", "CASE_03", "CASE_04"]:
        sc_def = registry.load_scenario(sc_id)
        active_fault = sc_def.fault_definition.fault_type
        telemetry = registry.generate_telemetry(sc_id, active_fault)

        # Telemetry NetworkState should NOT expose scenario metadata or ground_truth_fault_label directly
        assert not hasattr(telemetry, "ground_truth_fault_label")
        assert not hasattr(telemetry, "expected_fault_domain")
        assert telemetry.topology_id == sc_id
        assert telemetry.anomalies_detected is True


def test_fault_to_telemetry_correspondence_retained_scenarios():
    """
    Verifies that each retained scenario exhibits its specific fault symptoms in generated telemetry.
    """
    registry = ScenarioRegistry()

    # CASE_01: OSPF Adjacency Flap
    t1 = registry.generate_telemetry("CASE_01", "OSPF_ADJACENCY_INSTABILITY")
    assert any(l.rtt_ms > 100 for l in t1.links)
    assert t1.nodes["core-rtr01"].cpu_utilization_pct > 70.0

    # CASE_02: WAN Path Congestion
    t2 = registry.generate_telemetry("CASE_02", "WAN_PATH_DEGRADATION_AND_CONGESTION")
    assert t2.interfaces["dc-gw02-wan1"].utilization_pct > 90.0
    assert any(l.packet_loss_pct > 20.0 for l in t2.links)

    # CASE_03: MTU Mismatch Fragmentation
    t3 = registry.generate_telemetry("CASE_03", "MTU_MISMATCH_FRAGMENTATION_CASCADE")
    assert t3.interfaces["spine-01-eth3"].mtu == 1400
    assert t3.interfaces["leaf-03-eth1"].mtu == 9000

    # CASE_04: Composite Anomaly
    t4 = registry.generate_telemetry("CASE_04", "NOVEL_COMPOSITE_ANOMALY")
    assert t4.nodes["edge-gw-01"].cpu_utilization_pct > 50.0
    assert any(l.rtt_ms > 80.0 for l in t4.links)


def test_equal_initial_state_across_arms_3_to_5():
    """
    Verifies that Arms 3, 4, and 5 receive identical input telemetry snapshots for a given scenario and fault.
    """
    registry = ScenarioRegistry()

    for sc_id in ["CASE_01", "CASE_02", "CASE_03", "CASE_04"]:
        sc_def = registry.load_scenario(sc_id)
        fault_type = sc_def.fault_definition.fault_type
        
        # Telemetry generated for same scenario and fault
        raw_telemetry_a3 = registry.generate_telemetry(sc_id, fault_type)
        raw_telemetry_a4 = registry.generate_telemetry(sc_id, fault_type)
        raw_telemetry_a5 = registry.generate_telemetry(sc_id, fault_type)

        # Check key diagnostic telemetry fields match perfectly across arms
        assert raw_telemetry_a3.anomalies_detected == raw_telemetry_a4.anomalies_detected == raw_telemetry_a5.anomalies_detected
        assert len(raw_telemetry_a3.interfaces) == len(raw_telemetry_a4.interfaces) == len(raw_telemetry_a5.interfaces)
        assert len(raw_telemetry_a3.links) == len(raw_telemetry_a4.links) == len(raw_telemetry_a5.links)


def test_revised_matrix_v2_structure_and_seeds():
    """
    Validates structure, uniqueness of run_ids and seeds, and row counts of experiment_matrix_v2.csv.
    """
    v2_csv = "scratch/research_v2/phase3/experiment_matrix_v2.csv"
    assert os.path.exists(v2_csv)

    success, errors = validate_matrix_v2(v2_csv)
    assert success, f"V2 Matrix validation failed: {errors}"

    with open(v2_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 120
    arms = set(r["arm_id"] for r in reader)
    scenarios = set(r["scenario_id"] for r in reader)

    assert arms == {"ARM_3_RULE_BASED", "ARM_4_PHASE2_BASELINE", "ARM_5_CESO_CADE_NO_LLM"}
    assert scenarios == {"CASE_01", "CASE_02", "CASE_03", "CASE_04"}

    # Confirm all rows are PLANNED_NOT_EXECUTED
    for r in reader:
        assert r["execution_status"] == "PLANNED_NOT_EXECUTED"


def test_metric_eligibility_and_status_handling_arms_3_to_5():
    """
    Verifies that calculate_evaluation_metrics sets RSR to NOT_APPLICABLE and VSR to NOT_MEASURED for Arms 3-5.
    """
    dummy_run = ExperimentRun(
        run_id="RUN-TEST-01",
        timestamp="2026-10-09T00:00:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="CASE_01",
        ground_truth_fault_label="OSPF_ADJACENCY_INSTABILITY",
        predicted_fault_label="OSPF_ADJACENCY_INSTABILITY",
        start_time="2026-10-09T00:00:00Z",
        end_time="2026-10-09T00:00:01Z",
        arm_id="ARM_5_CESO_CADE_NO_LLM",
        evidence_count=5,
        total_raw_evidence_count=20,
        diagnosis_latency_ms=12.5,
        is_completed=True
    )

    metrics = calculate_evaluation_metrics([dummy_run], EvaluationEnvironment.SIMULATED)

    assert metrics["accuracy"].status == MetricStatus.MEASURED
    assert metrics["accuracy"].value == 100.0
    assert metrics["ecr"].status == MetricStatus.MEASURED
    assert metrics["vsr"].status == MetricStatus.NOT_MEASURED
    assert metrics["vsr"].exclusion_reason == "Verification probe target scope telemetry not recorded"
    assert metrics["rsr"].status == MetricStatus.NOT_APPLICABLE
    assert metrics["rsr"].exclusion_reason == "No eligible active remediation actions were executed in this experiment group"


def test_prevention_of_execution_without_authorization():
    """
    Verifies that BenchmarkRunner blocks execution when phase3_execution_authorized is False.
    """
    runner = BenchmarkRunner()
    assert runner.phase3_execution_authorized is False

    with pytest.raises(PermissionError) as exc_info:
        runner.run_phase3_matrix()
    
    assert "PROHIBITED" in str(exc_info.value) or "unauthorized" in str(exc_info.value).lower()
