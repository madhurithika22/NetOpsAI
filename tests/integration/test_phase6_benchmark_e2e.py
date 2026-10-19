import pytest
from app.evaluation.runner import BenchmarkRunner
from app.evaluation.recorder import ExperimentRecorder
from app.evaluation.models import EvaluationEnvironment
from app.llm.gateway import llm_gateway
from app.llm.models import LLMConfig
from app.llm.providers.mock import MockLLMProvider

def test_full_phase6_benchmark_e2e(tmp_path):
    # Configure mock LLM provider for predictable test execution
    llm_gateway.set_config(LLMConfig(enabled=True, provider="mock", model="test-llama3"))

    test_dir = str(tmp_path / "experiments")
    recorder = ExperimentRecorder(base_dir=test_dir)
    runner = BenchmarkRunner(recorder=recorder)

    # Run full simulated benchmark across all 4 research scenarios
    summary = runner.run_simulated_benchmark(
        scenario_ids=["CASE_01", "CASE_02", "CASE_03", "CASE_04"],
        number_of_runs=1,
        seed=100,
        include_llm=True,
        run_direct_llm_comparison=True
    )

    assert summary.total_runs == 4
    assert summary.completed_runs == 4

    runs = recorder.list_runs()
    assert len(runs) == 4

    # Verify Case 4 LLM escalation and Token Experiment
    case4_run = next(r for r in runs if r.dataset_or_scenario_id == "CASE_04")
    assert case4_run.llm_escalated
    assert case4_run.cadd_confidence < 0.70
    assert case4_run.pre_llm_diagnosis == "UNKNOWN_COMPOSITE_ANOMALY"
    assert case4_run.direct_token_metrics is not None
    assert case4_run.pipeline_token_metrics is not None
    assert case4_run.input_token_reduction_pct > 0.0
    assert case4_run.total_token_reduction_pct > 0.0

    # Verify MSVS and Post-Action Verification
    for r in runs:
        assert r.remediation_decision == "APPROVED"
        assert r.remediation_status == "SUCCESS"
        assert r.verification_result == "VERIFIED_HEALTHY"
        assert r.feedback_package is not None

    # Verify metrics recomputation
    assert "accuracy" in summary.metrics
    assert summary.metrics["accuracy"].value == 100.0
