import json
from app.scenarios.registry import scenario_registry
from app.cadd.engine import ExplainableRuleEngine
from app.msvs.policies import SafetyPolicyEngine
from app.msvs.service import msvs_service
from app.llm.gateway import llm_gateway
from app.llm.models import LLMConfig, LLMContextPackage
from app.llm.feedback import create_feedback_package
from app.evaluation.runner import BenchmarkRunner
from app.evaluation.recorder import ExperimentRecorder

def main():
    print("=== NETOPS PHASE 6 LIVE VALIDATION ===")
    
    # 1. Health check
    llm_gateway.set_config(LLMConfig(enabled=True, provider="mock", model="llama3"))
    health = llm_gateway.get_health()
    print(f"LLM Gateway Health: provider={health.provider}, model={health.model}, status={health.status}, reachable={health.reachable}")

    # 2. Check 4 scenarios loading
    scenarios = scenario_registry.list_scenarios()
    print(f"\nLoaded {len(scenarios)} Scenarios:")
    for sc in scenarios:
        print(f" - [{sc.scenario_id}] {sc.name} ({sc.target_node_count} nodes, {sc.target_link_count} links)")

    # 3. Run Benchmark
    recorder = ExperimentRecorder(base_dir="scratch/experiments_val")
    runner = BenchmarkRunner(recorder=recorder)

    summary = runner.run_simulated_benchmark(
        scenario_ids=["CASE_01", "CASE_02", "CASE_03", "CASE_04"],
        number_of_runs=1,
        seed=42,
        include_llm=True,
        run_direct_llm_comparison=True
    )

    print("\n=== BENCHMARK EXECUTION SUMMARY ===")
    print(f"Total Runs: {summary.total_runs}")
    print(f"Completed Runs: {summary.completed_runs}")
    for k, v in summary.metrics.items():
        if v.status == "MEASURED":
            print(f" - {v.name}: {v.value} {v.unit or ''}")

    # 4. Token Experiment Output for Case 4
    runs = recorder.list_runs()
    case4_run = next(r for r in runs if r.dataset_or_scenario_id == "CASE_04")
    token_exp_output = {
        "scenario_id": case4_run.dataset_or_scenario_id,
        "model": llm_gateway.config.model,
        "direct": case4_run.direct_token_metrics,
        "netops_pipeline": case4_run.pipeline_token_metrics,
        "input_token_reduction_pct": case4_run.input_token_reduction_pct,
        "total_token_reduction_pct": case4_run.total_token_reduction_pct,
        "token_measurement_method": case4_run.direct_token_metrics.get("measurement_method") if case4_run.direct_token_metrics else "estimated"
    }

    print("\n=== CONTROLLED TOKEN EXPERIMENT RESULT (CASE 04) ===")
    print(json.dumps(token_exp_output, indent=2))

if __name__ == "__main__":
    main()
