import json
import statistics
from app.scenarios.registry import scenario_registry
from app.cadd.engine import ExplainableRuleEngine
from app.msvs.policies import SafetyPolicyEngine
from app.msvs.service import msvs_service
from app.llm.gateway import llm_gateway
from app.llm.models import LLMConfig, LLMContextPackage
from app.llm.feedback import create_feedback_package
from app.evaluation.runner import BenchmarkRunner
from app.evaluation.recorder import ExperimentRecorder
from app.models.cadd_models import ActionPlan, ProposedAction

def run_real_ollama_validation():
    print("============================================================")
    print(" NETOPS PHASE 6.1 / 6.2 — REAL OLLAMA QWEN3:4B LIVE VALIDATION")
    print("============================================================")

    # 1. Configure LLM Gateway to connect to REAL Ollama qwen3:4b
    llm_gateway.set_config(LLMConfig(
        enabled=True,
        provider="ollama",
        base_url="http://localhost:11434",
        model="qwen3:4b",
        timeout_seconds=120,
        temperature=0.1
    ))

    # 2. Health check
    health = llm_gateway.get_health()
    print(f"\n1. LLM HEALTH CHECK:")
    print(f"   Provider: {health.provider}")
    print(f"   Model: {health.model}")
    print(f"   Reachable: {health.reachable}")
    print(f"   Status: {health.status}")
    print(f"   Latency: {health.latency_ms} ms")

    if not health.reachable or health.status != "LLM_AVAILABLE":
        raise RuntimeError(f"Ollama server or model qwen3:4b unavailable: {health.error}")

    # 3. Real Single Inference Test
    print("\n2. REAL INFERENCE TEST (qwen3:4b):")
    test_res = llm_gateway.analyze_direct_raw_logs(
        scenario_id="CASE_04",
        raw_telemetry={"edge_gw_01_cpu": 58.0, "wan_rtt_ms": 85.0, "packet_loss_pct": 7.5},
        raw_logs=["SYS-5-CACHE: DNS resolver lock contention on edge-gw-01"],
        topology_events=["BGP metric route preference shift to 150"]
    )
    print(f"   LLM Status: {test_res.llm_status}")
    print(f"   Diagnosis Output: {test_res.diagnosis}")
    print(f"   Reasoning Summary: {test_res.reasoning_summary[:150]}...")
    print(f"   Token Usage (Provider-Reported): Input={test_res.token_metrics.input_tokens}, Output={test_res.token_metrics.output_tokens}, Total={test_res.token_metrics.total_tokens}")
    print(f"   Measurement Method: {test_res.token_metrics.measurement_method.value}")

    # 4. Five Independent Case 4 Token Experiments
    print("\n3. FIVE INDEPENDENT CASE 04 TOKEN EXPERIMENTS (REAL qwen3:4b):")
    token_runs = []
    
    recorder = ExperimentRecorder(base_dir="scratch/experiments_ollama")
    runner = BenchmarkRunner(recorder=recorder)

    for run_idx in range(1, 6):
        seed = 42 + run_idx
        sc_def = scenario_registry.load_scenario("CASE_04")
        telemetry = scenario_registry.generate_telemetry("CASE_04", f"FAULT_SEED_{seed}")
        raw_telemetry_dict = telemetry.model_dump(mode="json")
        
        ctx_package = LLMContextPackage(
            incident_id=f"inc-seed-{seed}",
            scenario_id="CASE_04",
            timestamp="2026-10-07T22:30:00Z",
            topology_summary={"node_count": 48, "link_count": 48},
            affected_nodes=["edge-gw-01", "dc-leaf-01"],
            affected_links=["edge-gw-01<->wan-rtr-01"],
            ceso_findings=["DNS lock contention on edge-gw-01", "BGP metric route preference shift to 150"],
            relevant_telemetry={"edge_gw_01_cpu": 58.0 + run_idx, "wan_rtt_ms": 85.0 + run_idx*2},
            correlated_anomalies=["Composite Edge-DataCenter Anomaly"],
            cadd_diagnosis="UNKNOWN_COMPOSITE_ANOMALY",
            diagnosis_confidence=0.47,
            candidate_causes=["Edge Gateway Lock Contention", "Spine Switch Latency Degradation"],
            msvs_safety_constraints=["Do not modify protected interface eth0"],
            candidate_remediation_actions=[a.model_dump(mode="json") for a in sc_def.remediation_candidates],
            verification_requirements=sc_def.verification_criteria
        )

        exp_res = llm_gateway.run_controlled_token_experiment(
            scenario_id="CASE_04",
            raw_telemetry=raw_telemetry_dict,
            raw_logs=[f"SYS-5-CACHE: DNS resolver lock contention on edge-gw-01 (Seed {seed})"],
            topology_events=[f"BGP metric route preference shift to 150 on wan-rtr-01 (Seed {seed})"],
            context_package=ctx_package
        )

        in_red = exp_res.input_token_reduction_pct
        tot_red = exp_res.total_token_reduction_pct

        token_runs.append({
            "run_index": run_idx,
            "seed": seed,
            "direct_input_tokens": exp_res.direct.input_tokens,
            "direct_output_tokens": exp_res.direct.output_tokens,
            "direct_total_tokens": exp_res.direct.total_tokens,
            "direct_latency_ms": exp_res.direct.latency_ms,
            "pipeline_input_tokens": exp_res.netops_pipeline.input_tokens,
            "pipeline_output_tokens": exp_res.netops_pipeline.output_tokens,
            "pipeline_total_tokens": exp_res.netops_pipeline.total_tokens,
            "pipeline_latency_ms": exp_res.netops_pipeline.latency_ms,
            "input_reduction_pct": in_red,
            "total_reduction_pct": tot_red,
            "measurement_method": exp_res.direct.measurement_method.value
        })
        print(f"   Run {run_idx} (Seed {seed}): Direct In={token_runs[-1]['direct_input_tokens']} | Pipeline In={token_runs[-1]['pipeline_input_tokens']} | In Reduction={in_red:.2f}% | Total Reduction={tot_red:.2f}% | Method={token_runs[-1]['measurement_method']}", flush=True)

    # 5. Statistical Aggregation
    in_reds = [r["input_reduction_pct"] for r in token_runs]
    tot_reds = [r["total_reduction_pct"] for r in token_runs]

    stats_output = {
        "mean_input_reduction_pct": round(statistics.mean(in_reds), 2),
        "median_input_reduction_pct": round(statistics.median(in_reds), 2),
        "min_input_reduction_pct": round(min(in_reds), 2),
        "max_input_reduction_pct": round(max(in_reds), 2),
        "std_dev_input_reduction_pct": round(statistics.stdev(in_reds), 2) if len(in_reds) > 1 else 0.0,
        "mean_total_reduction_pct": round(statistics.mean(tot_reds), 2),
        "median_total_reduction_pct": round(statistics.median(tot_reds), 2),
        "min_total_reduction_pct": round(min(tot_reds), 2),
        "max_total_reduction_pct": round(max(tot_reds), 2),
        "std_dev_total_reduction_pct": round(statistics.stdev(tot_reds), 2) if len(tot_reds) > 1 else 0.0
    }

    print("\n4. TOKEN REDUCTION STATISTICAL SUMMARY:")
    print(json.dumps(stats_output, indent=2))

    # 6. Negative MSVS Safety Test
    print("\n5. NEGATIVE MSVS SAFETY TEST:")
    policy_engine = SafetyPolicyEngine()
    unsafe_action = ProposedAction(
        action_id="act-unsafe-test",
        command_type="SET_INTERFACE_STATE",
        target_device="edge-gw-01",
        parameters={"interface": "eth0", "target_state": "DOWN"}
    )
    unsafe_plan = ActionPlan(plan_id="plan-unsafe", diagnosis_id="diag-unsafe", proposed_actions=[unsafe_action])
    st1, st2, violations = policy_engine.validate_plan(unsafe_plan)
    print(f"   Unsafe LLM Action targeting protected interface 'eth0':")
    print(f"   Stage 1 Policy Passed: {st1} | Stage 2 Syntax Passed: {st2}")
    print(f"   Violations Caught: {[v.violation_reason for v in violations]}")
    assert not (st1 and st2), "MSVS failed to block unsafe LLM action!"
    print("   [PASSED] MSVS successfully blocked unsafe LLM action from executing!")

    # 7. Feedback Loop Assessment with Real qwen3:4b
    print("\n6. REAL QWEN3:4B POST-ACTION FEEDBACK ASSESSMENT:")
    fb_req = create_feedback_package(
        action_id="act-case04-remed",
        result="SUCCESS",
        verification_passed=True,
        pre_metrics={"rtt_ms": 45.0, "packet_loss_pct": 3.2},
        post_metrics={"rtt_ms": 8.0, "packet_loss_pct": 0.0},
        affected_services=["Real-Time Telemetry Analytics Engine", "Hybrid Cloud Database Sync"]
    )
    post_assess = llm_gateway.assess_post_remediation(fb_req)
    print(f"   Diagnosis Supported: {post_assess.diagnosis_supported}")
    print(f"   Remediation Effective: {post_assess.remediation_effective}")
    print(f"   Additional Action Required: {post_assess.additional_action_required}")
    out_summary = {
        "health": {
            "provider": health.provider,
            "model": health.model,
            "reachable": health.reachable,
            "status": health.status,
            "latency_ms": health.latency_ms
        },
        "inference_test": {
            "llm_status": test_res.llm_status,
            "diagnosis": test_res.diagnosis,
            "reasoning_summary": test_res.reasoning_summary,
            "input_tokens": test_res.token_metrics.input_tokens,
            "output_tokens": test_res.token_metrics.output_tokens,
            "total_tokens": test_res.token_metrics.total_tokens,
            "measurement_method": test_res.token_metrics.measurement_method.value
        },
        "runs": token_runs,
        "statistical_summary": stats_output,
        "msvs_negative_test": {
            "stage1_passed": st1,
            "stage2_passed": st2,
            "blocked": not (st1 and st2),
            "violations": [v.violation_reason for v in violations]
        },
        "feedback_assessment": {
            "diagnosis_supported": post_assess.diagnosis_supported,
            "remediation_effective": post_assess.remediation_effective,
            "additional_action_required": post_assess.additional_action_required,
            "summary": post_assess.assessment_summary
        }
    }

    with open("scratch/real_ollama_results.json", "w") as f:
        json.dump(out_summary, f, indent=2)

    print("\n   [SUCCESS] Saved full validation output to scratch/real_ollama_results.json", flush=True)

if __name__ == "__main__":
    run_real_ollama_validation()
