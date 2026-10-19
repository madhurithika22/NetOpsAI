import pytest
from app.llm.models import (
    LLMConfig, LLMStatus, LLMContextPackage, TokenMetrics, TokenMeasurementMethod
)
from app.llm.gateway import llm_gateway
from app.llm.providers.mock import MockLLMProvider
from app.llm.token_metrics import estimate_tokens, calculate_token_reduction
from app.msvs.policies import SafetyPolicyEngine
from app.models.cadd_models import ActionPlan, ProposedAction

def test_token_estimation_and_reduction():
    text_short = "Short message"
    text_long = "This is a much longer network telemetry report containing multiple interface statistics and routing entries."

    tokens_short = estimate_tokens(text_short)
    tokens_long = estimate_tokens(text_long)

    assert tokens_long > tokens_short

    direct_m = TokenMetrics(input_tokens=1000, output_tokens=200, total_tokens=1200)
    pipeline_m = TokenMetrics(input_tokens=200, output_tokens=150, total_tokens=350)

    in_red, tot_red = calculate_token_reduction(direct_m, pipeline_m)
    assert in_red == 80.0
    assert tot_red == 70.83

def test_mock_llm_gateway_flow():
    cfg = LLMConfig(enabled=True, provider="mock", model="mock-llama3")
    llm_gateway.set_config(cfg)

    health = llm_gateway.get_health()
    assert health.reachable
    assert health.status == LLMStatus.LLM_AVAILABLE

    ctx = LLMContextPackage(
        incident_id="inc-test",
        scenario_id="CASE_04",
        timestamp="2026-10-07T20:00:00Z",
        topology_summary={"node_count": 48, "link_count": 96},
        affected_nodes=["edge-gw-01"],
        affected_links=["edge-gw-01<->wan-rtr-01"],
        ceso_findings=["DNS resolver cache lock contention"],
        relevant_telemetry={"anomalies_detected": True},
        correlated_anomalies=["Novel composite cross-layer anomaly"],
        cadd_diagnosis="UNKNOWN_COMPOSITE_ANOMALY",
        diagnosis_confidence=0.47,
        candidate_causes=["Edge resolver cache contention", "BGP metric drift"],
        msvs_safety_constraints=["Do not touch eth0"],
        candidate_remediation_actions=[{"command_type": "RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE"}],
        verification_requirements={"max_rtt_ms": 15.0}
    )

    res = llm_gateway.analyze_netops_context(ctx)
    assert res.llm_status == LLMStatus.LLM_AVAILABLE
    assert res.recommended_action is not None
    assert res.confidence > 0.80

def test_llm_recommendation_must_pass_msvs():
    policy_engine = SafetyPolicyEngine()

    valid_action = ProposedAction(
        action_id="act-llm-1",
        command_type="RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE",
        target_device="edge-gw-01",
        parameters={"service": "dns-resolver", "interface": "wan0"}
    )
    valid_plan = ActionPlan(plan_id="plan-valid", diagnosis_id="diag-1", proposed_actions=[valid_action])
    st1, st2, violations = policy_engine.validate_plan(valid_plan)
    assert st1 and st2

    unsafe_action = ProposedAction(
        action_id="act-llm-unsafe",
        command_type="SET_INTERFACE_STATE",
        target_device="edge-gw-01",
        parameters={"interface": "eth0", "target_state": "DOWN"}
    )
    unsafe_plan = ActionPlan(plan_id="plan-unsafe", diagnosis_id="diag-2", proposed_actions=[unsafe_action])
    st1_u, st2_u, violations_u = policy_engine.validate_plan(unsafe_plan)
    assert not st1_u
    assert any("eth0" in v.violation_reason for v in violations_u)
