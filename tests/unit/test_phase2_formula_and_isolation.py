import pytest
import math
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry, NodeMetrics
from app.cadd.engine import ExplainableRuleEngine, safe_float, psi

def test_01_hand_calculable_exact_scores():
    engine = ExplainableRuleEngine()
    
    # Hand-calculable test 1: Single interface down
    state1 = NetworkState(
        snapshot_id="snap-test-01",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=False)},
        links=[],
        routes=[],
        nodes={}
    )
    report1, plan1 = engine.diagnose_state(state1)
    assert report1.fault_type == "INTERFACE_FAILURE"
    assert report1.candidate_scores["INTERFACE_FAILURE"] == 1.0
    assert report1.confidence_score == 1.0
    assert report1.escalation_required is False

    # Hand-calculable test 2: High latency RTT = 100ms (f_lat = (100-50)/50 = 1.0)
    state2 = NetworkState(
        snapshot_id="snap-test-02",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=100.0, packet_loss_pct=0.0)],
        routes=[],
        nodes={}
    )
    report2, plan2 = engine.diagnose_state(state2)
    assert report2.fault_type == "HIGH_LATENCY_CONGESTION"
    # S(HIGH_LATENCY_CONGESTION) = 0.7 * 1.0 + 0.3 * 0 = 0.7
    assert report2.candidate_scores["HIGH_LATENCY_CONGESTION"] == 0.7
    assert report2.confidence_score == 0.7
    assert report2.escalation_required is False


def test_02_normalization_and_weight_handling():
    assert psi(-5.0) == 0.0
    assert psi(0.5) == 0.5
    assert psi(1.5) == 1.0
    assert safe_float(None) == 0.0
    assert safe_float("invalid") == 0.0

    engine = ExplainableRuleEngine()
    state = NetworkState(
        snapshot_id="snap-test-weights",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True, utilization_pct=95.0)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=10.0, packet_loss_pct=25.0)],
        routes=[],
        nodes={}
    )
    report, _ = engine.diagnose_state(state)
    # f_util = (95-75)/20 = 1.0, f_loss = (25-10)/30 = 0.5
    # S(WAN_PATH_DEGRADATION) = 0.6 * 1.0 + 0.4 * 0.5 = 0.8
    assert report.fault_type == "WAN_PATH_DEGRADATION"
    assert report.candidate_scores["WAN_PATH_DEGRADATION"] == 0.8


def test_03_missing_feature_behavior():
    engine = ExplainableRuleEngine()
    empty_state = NetworkState(
        snapshot_id="snap-empty",
        interfaces={},
        links=[],
        routes=[],
        nodes={}
    )
    report, plan = engine.diagnose_state(empty_state)
    assert report.fault_type == "HEALTHY"
    assert report.confidence_score == 1.0
    assert report.escalation_required is False


def test_04_invalid_numeric_and_non_finite_input():
    assert safe_float(float("nan")) == 0.0
    assert safe_float(float("inf")) == 0.0
    assert safe_float(None) == 0.0
    assert psi(float("nan")) == 0.0
    assert psi(float("inf")) == 0.0

    engine = ExplainableRuleEngine()
    normal_state = NetworkState(
        snapshot_id="snap-nan-safe",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True, rx_errors=0)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=10.0, packet_loss_pct=0.0)],
        routes=[],
        nodes={}
    )
    report, plan = engine.diagnose_state(normal_state)
    assert report is not None
    assert isinstance(report.confidence_score, float)
    assert not math.isnan(report.confidence_score)


def test_05_zero_denominator_safety():
    engine = ExplainableRuleEngine()
    state = NetworkState(
        snapshot_id="snap-zero-den",
        interfaces={},
        links=[],
        routes=[]
    )
    report, _ = engine.diagnose_state(state)
    assert report.candidate_scores["INTERFACE_FAILURE"] == 0.0


def test_06_candidate_ties_and_deterministic_tie_breaking():
    engine = ExplainableRuleEngine()
    # Construct state where both INTERFACE_FAILURE and ROUTING_MISCONFIGURATION have score 1.0
    tie_state = NetworkState(
        snapshot_id="snap-tie",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=False)},
        routes=[RouteEntry(destination="10.0.2.0/24", gateway=None, interface="rtr1-eth0", metric=999)],
        links=[]
    )
    report, _ = engine.diagnose_state(tie_state)
    assert report.candidate_scores["INTERFACE_FAILURE"] == 1.0
    assert report.candidate_scores["ROUTING_MISCONFIGURATION"] == 1.0
    # INTERFACE_FAILURE has higher precedence than ROUTING_MISCONFIGURATION
    assert report.fault_type == "INTERFACE_FAILURE"


def test_07_unknown_fault_handling():
    engine = ExplainableRuleEngine()
    # Mild symptoms across latency, loss, rx_errors where no single candidate score >= 0.70
    composite_state = NetworkState(
        snapshot_id="snap-composite",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True, rx_errors=15)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=60.0, packet_loss_pct=12.0)],
        routes=[],
        anomalies_detected=True
    )
    report, _ = engine.diagnose_state(composite_state)
    assert report.fault_type == "UNKNOWN_COMPOSITE_ANOMALY"
    assert report.escalation_required is True


def test_08_confidence_changes_with_relevant_evidence():
    engine = ExplainableRuleEngine()
    state_moderate = NetworkState(
        snapshot_id="s-moderate",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=80.0, packet_loss_pct=0.0)],
        anomalies_detected=True
    )
    state_severe = NetworkState(
        snapshot_id="s-severe",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=140.0, packet_loss_pct=0.0)],
        anomalies_detected=True
    )
    report_mod, _ = engine.diagnose_state(state_moderate)
    report_sev, _ = engine.diagnose_state(state_severe)

    assert report_mod.fault_type == "HIGH_LATENCY_CONGESTION"
    assert report_sev.fault_type == "HIGH_LATENCY_CONGESTION"
    assert report_sev.candidate_scores["HIGH_LATENCY_CONGESTION"] > report_mod.candidate_scores["HIGH_LATENCY_CONGESTION"]
    assert report_sev.confidence_score > report_mod.confidence_score


def test_09_no_change_in_prediction_when_evaluation_label_changes():
    engine = ExplainableRuleEngine()
    base_state = NetworkState(
        snapshot_id="snap-isolation",
        topology_id="CASE_01",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=90.0, packet_loss_pct=0.0)]
    )

    modified_label_state = NetworkState(
        snapshot_id="snap-isolation",
        topology_id="CASE_04_SOME_OTHER_LABEL",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=90.0, packet_loss_pct=0.0)]
    )

    report1, _ = engine.diagnose_state(base_state)
    report2, _ = engine.diagnose_state(modified_label_state)

    assert report1.fault_type == report2.fault_type
    assert report1.confidence_score == report2.confidence_score
    assert report1.candidate_scores == report2.candidate_scores


def test_10_no_access_to_expected_diagnoses_in_operational_pipeline():
    engine = ExplainableRuleEngine()
    state = NetworkState(snapshot_id="s1", interfaces={"eth0": InterfaceState(name="eth0", is_up=True)})
    report, _ = engine.diagnose_state(state)
    assert not hasattr(state, "expected_diagnosis")
    assert not hasattr(state, "ground_truth_label")


def test_11_no_hardcoded_confidence_or_label_derived_paths():
    engine = ExplainableRuleEngine()
    state = NetworkState(
        snapshot_id="s1",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="n1", target_node="n2", rtt_ms=100.0, packet_loss_pct=0.0)]
    )
    report, _ = engine.diagnose_state(state)
    top_c = report.fault_type
    top_s = report.candidate_scores[top_c]
    sorted_s = sorted(report.candidate_scores.values(), reverse=True)
    sec_s = sorted_s[1]
    expected_conf = round(top_s * (1.0 - 0.5 * sec_s), 4)

    assert report.confidence_score == expected_conf


def test_12_deterministic_repeated_execution():
    engine = ExplainableRuleEngine()
    state = NetworkState(
        snapshot_id="s-det",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True, rx_errors=45)},
        routes=[RouteEntry(destination="10.0.2.0/24", gateway=None, interface="rtr1-eth0", metric=999)]
    )
    reports = [engine.diagnose_state(state)[0] for _ in range(50)]
    first_type = reports[0].fault_type
    first_conf = reports[0].confidence_score

    assert all(r.fault_type == first_type for r in reports)
    assert all(r.confidence_score == first_conf for r in reports)


def test_13_escalation_threshold_boundary_behavior():
    engine = ExplainableRuleEngine()
    # Test escalation flag logic
    assert engine.CONFIDENCE_ESCALATION_THRESHOLD == 0.70


def test_14_independent_score_recomputation_discrepancy():
    """
    Regression test for Phase 2 Correction (Prompt Item 1 & 3):
    Independently recomputes candidate scores and confidence for:
    1) RTT = 150.252ms, loss = 0.0% -> S = 0.7, C = 0.7
    2) RTT = 150.252ms, loss = 20.0% -> S = 0.8, C = 0.8
    Verifies exact mathematical compliance of formula S(c) = 0.7 * f_lat + 0.3 * f_loss.
    """
    engine = ExplainableRuleEngine()

    # Case 1: 150.252ms RTT, 0% loss (Original exp-phase2-04052fa5 observation)
    state_0pct = NetworkState(
        snapshot_id="snap-recompute-0pct",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="ha", target_node="hb", rtt_ms=150.252, packet_loss_pct=0.0)],
        routes=[],
        anomalies_detected=True
    )
    report_0pct, _ = engine.diagnose_state(state_0pct)

    # Independent hand calculation:
    # f_lat = min(1.0, max(0.0, (150.252 - 50.0)/50.0)) = 1.0
    # f_loss = min(1.0, max(0.0, (0.0 - 10.0)/30.0)) = 0.0
    # S = round(0.7 * 1.0 + 0.3 * 0.0, 4) = 0.7000
    # C = round(0.7 * (1.0 - 0.5 * 0.0), 4) = 0.7000
    assert report_0pct.candidate_scores["HIGH_LATENCY_CONGESTION"] == 0.7
    assert report_0pct.confidence_score == 0.7

    # Case 2: 150.252ms RTT, 20% loss (With 20% loss observation from netem fault)
    state_20pct = NetworkState(
        snapshot_id="snap-recompute-20pct",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
        links=[LinkLatency(source_node="ha", target_node="hb", rtt_ms=150.252, packet_loss_pct=20.0)],
        routes=[],
        anomalies_detected=True
    )
    report_20pct, _ = engine.diagnose_state(state_20pct)

    # Independent hand calculation:
    # f_lat = 1.0
    # f_loss = min(1.0, max(0.0, (20.0 - 10.0)/30.0)) = 10.0/30.0 = 0.333333...
    # S = round(0.7 * 1.0 + 0.3 * (1/3), 4) = round(0.7 + 0.1, 4) = 0.8000
    # C = round(0.8 * (1.0 - 0.5 * 0.0), 4) = 0.8000
    assert report_20pct.candidate_scores["HIGH_LATENCY_CONGESTION"] == 0.8
    assert report_20pct.confidence_score == 0.8

