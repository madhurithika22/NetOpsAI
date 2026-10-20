import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.cadd.engine import ExplainableRuleEngine
from app.cadd.service import cadd_service, build_operational_llm_context
from app.scenarios.registry import scenario_registry
from app.llm.models import LLMStatus, LLMDiagnosisResponse, TokenMetrics
from app.llm.gateway import llm_gateway
from app.evaluation.runner import BenchmarkRunner
from app.evaluation.recorder import ExperimentRecorder
from app.models.cadd_models import ProposedAction, ActionPlan
from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency
from app.msvs.service import msvs_service
from app.ceso.service import ceso_service


client = TestClient(app)


def test_case04_uncertainty_triggers_escalation_signal():
    """
    Verifies that CADE detects uncertainty on CASE_04 and emits
    top_candidate='UNKNOWN_COMPOSITE_ANOMALY' with escalation_required=True
    strictly through internal heuristic candidate evaluation without
    hardcoding on scenario identifiers or ground-truth labels.
    """
    engine = ExplainableRuleEngine()
    telemetry = scenario_registry.generate_telemetry("CASE_04", "NOVEL_COMPOSITE_ANOMALY")
    diag, plan = engine.diagnose_state(telemetry)

    assert diag.fault_type == "UNKNOWN_COMPOSITE_ANOMALY"
    assert diag.escalation_required is True
    assert diag.confidence_score < engine.CONFIDENCE_ESCALATION_THRESHOLD or diag.fault_type == "UNKNOWN_COMPOSITE_ANOMALY"
    assert len(diag.evidence_chain) > 0
    assert "RULE_COMPOSITE_ANOMALY_EVALUATION" in [e.rule_id for e in diag.evidence_chain]


def test_llm_context_package_isolation(monkeypatch, tmp_path):
    """
    Verifies that when operational escalation is triggered, the context package
    sent to the LLM does NOT contain the ground-truth label 'NOVEL_COMPOSITE_ANOMALY',
    injected fault descriptions, or answer-revealing scenario IDs like 'CASE_04'.
    """
    captured_package = None

    def mock_analyze(ctx_package):
        nonlocal captured_package
        captured_package = ctx_package
        return LLMDiagnosisResponse(
            diagnosis="INVESTIGATED_ANOMALY",
            reasoning_summary="Mocked operational reasoning",
            confidence=0.80,
            llm_status=LLMStatus.LLM_AVAILABLE,
            token_metrics=TokenMetrics(input_tokens=100, output_tokens=50, total_tokens=150)
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_analyze)
    monkeypatch.setattr(llm_gateway, "run_controlled_token_experiment", MagicMock())

    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))
    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=4241,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    assert captured_package is not None
    # 1. Neutralized scenario identifier
    assert captured_package.scenario_id != "CASE_04"
    assert "CASE_04" not in captured_package.scenario_id
    # 2. Zero ground truth leakage
    pkg_json = captured_package.model_dump_json()
    assert "NOVEL_COMPOSITE_ANOMALY" not in pkg_json
    # 3. Uses operational CADE findings
    assert captured_package.cadd_diagnosis == "UNKNOWN_COMPOSITE_ANOMALY"
    assert captured_package.diagnosis_confidence < 0.70


def test_llm_unavailable_leaves_original_diagnosis_and_blocks_remediation(monkeypatch, tmp_path):
    """
    Verifies that when the LLM is unavailable or errors:
    - Original CADE diagnosis is preserved as pre_llm_diagnosis and predicted_fault_label.
    - llm_status is explicitly recorded as LLM_UNAVAILABLE.
    - Active remediation is blocked and not treated as a successful recovery.
    """
    def mock_unavailable(ctx_package):
        return LLMDiagnosisResponse(
            diagnosis="LLM_UNAVAILABLE",
            reasoning_summary="LLM connection refused",
            confidence=0.0,
            llm_status=LLMStatus.LLM_UNAVAILABLE,
            raw_response="Connection refused"
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_unavailable)

    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))
    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=4241,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    assert run.predicted_fault_label == "UNKNOWN_COMPOSITE_ANOMALY"
    assert run.pre_llm_diagnosis == "UNKNOWN_COMPOSITE_ANOMALY"
    assert run.post_llm_diagnosis == "UNKNOWN_COMPOSITE_ANOMALY"
    assert run.llm_status == "LLM_UNAVAILABLE"
    assert run.llm_escalated is True
    # Active remediation must be blocked, not executed or considered recovered
    assert run.remediation_decision == "BLOCKED_LLM_FAILURE"
    assert run.remediation_status == "NOT_EXECUTED"
    assert run.verification_result == "NOT_EXECUTED"


def test_pre_llm_metrics_not_overwritten_by_post_llm_recovery(monkeypatch, tmp_path):
    """
    Verifies mode separation:
    - predicted_fault_label strictly records the initial pre-LLM diagnosis ('UNKNOWN_COMPOSITE_ANOMALY').
    - post_llm_diagnosis records the supplementary LLM recovery diagnosis.
    - The primary pre-LLM diagnostic score is protected from LLM reasoning substitution.
    """
    def mock_available(ctx_package):
        return LLMDiagnosisResponse(
            diagnosis="RECOVERED_CROSS_DOMAIN_ANOMALY",
            reasoning_summary="Identified edge resolver lock contention and BGP route shift.",
            confidence=0.92,
            recommended_action={
                "action_id": "act-llm-remed-1",
                "command_type": "FLUSH_RESOLVER_CACHE",
                "target_device": "edge-gw-01",
                "parameters": {"cache_name": "dns-cache"}
            },
            llm_status=LLMStatus.LLM_AVAILABLE,
            token_metrics=TokenMetrics(input_tokens=120, output_tokens=60, total_tokens=180)
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_available)

    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))
    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=4241,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    # Primary predicted label is NOT overwritten
    assert run.predicted_fault_label == "UNKNOWN_COMPOSITE_ANOMALY"
    assert run.pre_llm_diagnosis == "UNKNOWN_COMPOSITE_ANOMALY"
    # Post-LLM result is stored separately
    assert run.post_llm_diagnosis == "RECOVERED_CROSS_DOMAIN_ANOMALY"
    assert run.llm_status == "LLM_AVAILABLE"
    assert run.llm_escalated is True


def test_operational_diagnose_calls_llm_when_escalation_required(monkeypatch):
    """
    Verifies that the operational /cadd/diagnose path automatically calls the LLM gateway
    when CADE sets escalation_required=True, and includes the escalation result.
    """
    telemetry = scenario_registry.generate_telemetry("CASE_04", "NOVEL_COMPOSITE_ANOMALY")
    monkeypatch.setattr(ceso_service, "get_latest_state", lambda: telemetry)

    llm_called = False

    def mock_analyze(ctx_pkg):
        nonlocal llm_called
        llm_called = True
        return LLMDiagnosisResponse(
            diagnosis="RECOVERED_CROSS_DOMAIN_ANOMALY",
            reasoning_summary="Operational LLM analysis completed successfully.",
            confidence=0.88,
            recommended_action={
                "action_id": "act-llm-01",
                "command_type": "RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE",
                "target_device": "edge-gw-01",
                "parameters": {
                    "service": "dns-resolver",
                    "target_gateway": "edge-gw-01",
                    "action": "FLUSH_DNS_CACHE_AND_RESTORE_BGP_LOCAL_PREF",
                    "bgp_neighbor": "cloud-gw-01",
                    "local_pref": 200
                }
            },
            llm_status=LLMStatus.LLM_AVAILABLE,
            token_metrics=TokenMetrics(input_tokens=100, output_tokens=50, total_tokens=150)
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_analyze)

    res = client.post("/api/v1/cadd/diagnose")
    assert res.status_code == 200
    data = res.json()

    assert llm_called is True
    # Pre-LLM CADE diagnosis is preserved
    assert data["diagnostic_report"]["fault_type"] == "UNKNOWN_COMPOSITE_ANOMALY"
    assert data["diagnostic_report"]["escalation_required"] is True

    # Secondary diagnosis is separate and present in llm_escalation
    esc = data["llm_escalation"]
    assert esc is not None
    assert esc["escalated"] is True
    assert esc["post_llm_diagnosis"] == "RECOVERED_CROSS_DOMAIN_ANOMALY"
    assert esc["validation_passed"] is True
    assert esc["approval_status"] == "PENDING"
    assert esc["approval_id"] is not None
    assert esc["remediation_status"] == "PENDING"


def test_operational_diagnose_does_not_call_llm_when_no_escalation(monkeypatch):
    """
    Verifies that the normal /cadd/diagnose path does not call the LLM gateway
    when CADE diagnosis does not require escalation (e.g., standard high-confidence fault).
    """
    telemetry = NetworkState(
        snapshot_id="snap-high-conf-interface",
        interfaces={"eth0": InterfaceState(name="eth0", is_up=False)},
        links=[],
        routes=[],
        anomalies_detected=True
    )
    monkeypatch.setattr(ceso_service, "get_latest_state", lambda: telemetry)

    llm_called = False

    def mock_analyze(ctx_pkg):
        nonlocal llm_called
        llm_called = True
        return LLMDiagnosisResponse(
            diagnosis="SHOULD_NOT_BE_CALLED",
            reasoning_summary="",
            confidence=0.0,
            llm_status=LLMStatus.LLM_AVAILABLE
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_analyze)

    res = client.post("/api/v1/cadd/diagnose")
    assert res.status_code == 200
    data = res.json()

    assert llm_called is False
    assert data["diagnostic_report"]["fault_type"] == "INTERFACE_FAILURE"
    assert data["diagnostic_report"]["escalation_required"] is False
    assert data["llm_escalation"] is None


def test_valid_llm_action_msvs_validated_and_queued_pending_never_auto_executed(monkeypatch, tmp_path):
    """
    CRITICAL SAFETY TEST:
    Tests with a VALID action allowed by MSVS policy (RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE).
    Proves that:
    - The proposal is validated and queued for human approval in PENDING state.
    - No approval is automatically granted.
    - No action is automatically executed, including when the proposal passes MSVS validation.
    - No ceso_service.reset_simulation() is triggered.
    """
    valid_action_payload = {
        "action_id": "act-valid-01",
        "command_type": "RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE",
        "target_device": "edge-gw-01",
        "parameters": {
            "service": "dns-resolver",
            "target_gateway": "edge-gw-01",
            "action": "FLUSH_DNS_CACHE_AND_RESTORE_BGP_LOCAL_PREF",
            "bgp_neighbor": "cloud-gw-01",
            "local_pref": 200
        }
    }

    def mock_valid_llm(ctx_pkg):
        return LLMDiagnosisResponse(
            diagnosis="CONFIRMED_CROSS_DOMAIN_ANOMALY",
            reasoning_summary="Valid recovery plan proposed",
            confidence=0.90,
            recommended_action=valid_action_payload,
            llm_status=LLMStatus.LLM_AVAILABLE,
            token_metrics=TokenMetrics(input_tokens=150, output_tokens=75, total_tokens=225)
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_valid_llm)
    monkeypatch.setattr(llm_gateway, "run_controlled_token_experiment", MagicMock())

    # 1. Operational /cadd/diagnose path test
    telemetry = scenario_registry.generate_telemetry("CASE_04", "NOVEL_COMPOSITE_ANOMALY")
    monkeypatch.setattr(ceso_service, "get_latest_state", lambda: telemetry)

    exec_calls = 0
    orig_execute = msvs_service.execute_action_plan

    def tracked_execute(plan_id, operator_id="OPERATOR_ADMIN"):
        nonlocal exec_calls
        exec_calls += 1
        return orig_execute(plan_id, operator_id)

    monkeypatch.setattr(msvs_service, "execute_action_plan", tracked_execute)

    res = client.post("/api/v1/cadd/diagnose")
    assert res.status_code == 200
    data = res.json()

    esc = data["llm_escalation"]
    assert esc["validation_passed"] is True
    assert esc["approval_status"] == "PENDING"
    assert esc["remediation_status"] == "PENDING"
    assert exec_calls == 0, "msvs_service.execute_action_plan() was invoked from the operational diagnosis route!"

    # Verify that the approval request exists in the pending approvals queue
    pending = msvs_service.get_pending_approvals()
    matching_appr = next((a for a in pending if a.approval_id == esc["approval_id"]), None)
    assert matching_appr is not None
    assert matching_appr.status == "PENDING", "Action proposal was automatically approved!"

    # 2. BenchmarkRunner evaluation path test
    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))
    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=4241,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    # In BenchmarkRunner, the escalated run must remain PENDING and NOT executed
    assert run.remediation_decision == "PENDING_APPROVAL"
    assert run.remediation_status == "PENDING"
    assert run.verification_result == "NOT_EXECUTED"
    assert exec_calls == 0, "msvs_service.execute_action_plan() was automatically invoked in the evaluation runner!"


def test_llm_no_action_proposal_does_not_execute_cade_fallback(monkeypatch, tmp_path):
    """
    Verifies that if the LLM returns no action proposal during escalation:
    - The original CADE plan and diagnosis are retained for inspection.
    - An existing CADE proposal is NOT automatically executed as a fallback.
    - remediation_decision is NO_ACTION_PROPOSED and remediation_status is NOT_EXECUTED.
    """
    def mock_no_action(ctx_pkg):
        return LLMDiagnosisResponse(
            diagnosis="OBSERVED_ANOMALY_NO_ACTION",
            reasoning_summary="No safe automated action recommended; human observation requested.",
            confidence=0.85,
            recommended_action=None,  # No action proposed
            llm_status=LLMStatus.LLM_AVAILABLE,
            token_metrics=TokenMetrics(input_tokens=100, output_tokens=40, total_tokens=140)
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_no_action)
    monkeypatch.setattr(llm_gateway, "run_controlled_token_experiment", MagicMock())

    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))
    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=4241,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    # Must NOT fall back to executing CADE's action plan
    assert run.remediation_decision == "NO_ACTION_PROPOSED"
    assert run.remediation_status == "NOT_EXECUTED"
    assert run.verification_result == "NOT_EXECUTED"
    assert run.post_llm_diagnosis == "OBSERVED_ANOMALY_NO_ACTION"
    assert run.predicted_fault_label == "UNKNOWN_COMPOSITE_ANOMALY"


def test_invalid_llm_action_does_not_erase_valid_post_llm_diagnosis(monkeypatch, tmp_path):
    """
    Verifies that if the LLM response contains a valid diagnosis but an invalid or
    unwhitelisted proposed action:
    - Diagnosis validity is distinguished from action validity.
    - The valid post-LLM diagnosis is retained and not erased.
    - The action fails validation and is marked non-executable.
    """
    def mock_invalid_action(ctx_pkg):
        return LLMDiagnosisResponse(
            diagnosis="VALID_DIAGNOSIS_UNSAFE_ACTION",
            reasoning_summary="Identified issue correctly but recommended unauthorized action.",
            confidence=0.91,
            recommended_action={
                "action_id": "act-unsafe",
                "command_type": "DROP_ALL_FIREWALL_RULES",  # Not in whitelist
                "target_device": "fw-edge01",
                "parameters": {}
            },
            llm_status=LLMStatus.LLM_AVAILABLE,
            token_metrics=TokenMetrics(input_tokens=100, output_tokens=50, total_tokens=150)
        )

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_invalid_action)
    monkeypatch.setattr(llm_gateway, "run_controlled_token_experiment", MagicMock())

    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))
    run = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=4241,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_4_PHASE2_BASELINE"
    )

    # Valid post-LLM diagnosis is NOT erased
    assert run.post_llm_diagnosis == "VALID_DIAGNOSIS_UNSAFE_ACTION"
    # Action validation fails and is rejected
    assert run.remediation_decision == "REJECTED_UNSAFE"
    assert run.remediation_status == "NOT_EXECUTED"
    assert run.verification_result == "SAFETY_POLICY_ENFORCED"


def test_operator_approval_and_execution_endpoints_enforce_explicit_gate():
    """
    Verifies that the separate operator approval and execution endpoints in msvs_routes.py
    strictly enforce the human approval gate before allowing execution.
    """
    plan = ActionPlan(
        plan_id="plan-gate-test-01",
        diagnosis_id="diag-gate-01",
        proposed_actions=[
            ProposedAction(
                action_id="act-gate-01",
                command_type="REROUTE_TRAFFIC",
                target_device="rtr1",
                parameters={"interface": "veth-r1-r2", "target_destination": "10.0.2.0/24"}
            )
        ],
        requires_approval=True
    )

    val_res = msvs_service.validate_action_plan(plan, "Test human approval gate")
    assert val_res.is_valid is True

    # 1. Attempt execution before approval -> MUST raise 403 Forbidden
    res_exec_unapproved = client.post(f"/api/v1/msvs/execute/{plan.plan_id}")
    assert res_exec_unapproved.status_code == 403
    assert "has not been approved" in res_exec_unapproved.json()["detail"]

    # 2. Fetch pending approvals
    pending = msvs_service.get_pending_approvals()
    matching = next((r for r in pending if r.plan_id == plan.plan_id), None)
    assert matching is not None
    assert matching.status == "PENDING"

    # 3. Explicit operator approval
    res_appr = client.post(f"/api/v1/msvs/approvals/{matching.approval_id}/approve")
    assert res_appr.status_code == 200
    assert res_appr.json()["status"] == "APPROVED"

    # 4. Now execute approved plan -> MUST succeed
    res_exec_approved = client.post(f"/api/v1/msvs/execute/{plan.plan_id}")
    assert res_exec_approved.status_code == 200
    assert res_exec_approved.json()["status"] == "SUCCESS"


def test_primary_research_arms_remain_strictly_llm_free(monkeypatch, tmp_path):
    """
    Verifies that the primary Phase 3 research arms (ARM_3_RULE_BASED, ARM_5_CESO_CADE_NO_LLM)
    remain strictly LLM-free:
    - Never invoke the LLM gateway even on CASE_04 with include_llm=True.
    - llm_invocation_count is 0.
    """
    def mock_fail_if_called(ctx_pkg):
        raise AssertionError("LLM Gateway was invoked by a research arm that must remain LLM-free!")

    monkeypatch.setattr(llm_gateway, "analyze_netops_context", mock_fail_if_called)

    runner = BenchmarkRunner(recorder=ExperimentRecorder(base_dir=str(tmp_path)))

    # Arm 3: Rule-Based
    run3 = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=42,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_3_RULE_BASED"
    )
    assert run3.llm_invocation_count == 0
    assert run3.llm_status == "LLM_DISABLED_FOR_ARM"
    assert run3.llm_escalated is False

    # Arm 5: CESO + CADE No-LLM
    run5 = runner._run_single_scenario_benchmark(
        sc_id="CASE_04",
        run_number=1,
        seed=42,
        include_llm=True,
        run_direct_llm_comparison=False,
        arm_id="ARM_5_CESO_CADE_NO_LLM"
    )
    assert run5.llm_invocation_count == 0
    assert run5.llm_status == "LLM_DISABLED_FOR_ARM"
    assert run5.llm_escalated is False
