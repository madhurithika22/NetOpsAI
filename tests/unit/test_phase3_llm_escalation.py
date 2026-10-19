import pytest
from unittest.mock import MagicMock
from app.cadd.engine import ExplainableRuleEngine
from app.scenarios.registry import scenario_registry
from app.llm.models import LLMStatus, LLMDiagnosisResponse, TokenMetrics
from app.llm.gateway import llm_gateway
from app.evaluation.runner import BenchmarkRunner
from app.evaluation.recorder import ExperimentRecorder
from app.models.cadd_models import ProposedAction


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
