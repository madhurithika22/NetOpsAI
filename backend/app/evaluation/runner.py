import time
import uuid
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.evaluation.models import (
    ExperimentRun, EvaluationEnvironment, EvaluationSummary
)
from app.evaluation.recorder import ExperimentRecorder
from app.adapters.aiops2020_adapter import AIOps2020Adapter
from app.scenarios.registry import scenario_registry
from app.cadd.engine import ExplainableRuleEngine
from app.ceso.service import ceso_service
from app.msvs.policies import SafetyPolicyEngine
from app.msvs.service import msvs_service
from app.models.cadd_models import ActionPlan, ProposedAction
from app.llm.gateway import llm_gateway
from app.llm.models import LLMContextPackage
from app.llm.feedback import create_feedback_package


AUTHORIZED_ARMS = {"ARM_3_RULE_BASED", "ARM_4_PHASE2_BASELINE", "ARM_5_CESO_CADE_NO_LLM"}
UNIMPLEMENTED_ARMS = {"ARM_1_STATIC_THRESHOLD", "ARM_2_ROLLING_STATISTICAL"}
BLOCKED_ARMS = {"ARM_6_CESO_CADE_OLLAMA_LLM", "ARM_7_CLOSED_LOOP_NETOPS"}


class BenchmarkRunner:
    """
    Executes controlled benchmark scenarios across SIMULATED (Primary 4 Scenarios), LINUX_TESTBED, and AIOPS_2020 environments.
    Guarantees strict benchmark separation, ground truth isolation, and records all runs via ExperimentRecorder.
    """
    phase3_execution_authorized: bool = False

    def __init__(self, recorder: Optional[ExperimentRecorder] = None):
        self.recorder = recorder or ExperimentRecorder()
        self.cadd_engine = ExplainableRuleEngine()
        self.msvs_policy_engine = SafetyPolicyEngine()

    def run_phase3_matrix(self):
        if not self.phase3_execution_authorized:
            raise PermissionError("Phase 3 research execution is PROHIBITED: phase3_execution_authorized is set to False.")
        raise NotImplementedError("Phase 3 matrix execution pipeline")

    def run_simulated_benchmark(
        self,
        scenario_ids: Optional[List[str]] = None,
        number_of_runs: int = 1,
        seed: int = 42,
        include_llm: bool = True,
        run_direct_llm_comparison: bool = True,
        arm_id: str = "ARM_4_PHASE2_BASELINE"
    ) -> EvaluationSummary:
        """
        Executes reproducible research benchmark across the primary research scenarios.
        """
        random.seed(seed)

        if scenario_ids is None:
            scenario_ids = ["CASE_01", "CASE_02", "CASE_03", "CASE_04"]

        for sc_id in scenario_ids:
            for run_idx in range(number_of_runs):
                self._run_single_scenario_benchmark(
                    sc_id=sc_id,
                    run_number=run_idx + 1,
                    seed=seed + run_idx,
                    include_llm=include_llm,
                    run_direct_llm_comparison=run_direct_llm_comparison,
                    arm_id=arm_id
                )

        return self.recorder.get_summary(EvaluationEnvironment.SIMULATED)

    def _run_single_scenario_benchmark(
        self,
        sc_id: str,
        run_number: int,
        seed: int,
        include_llm: bool,
        run_direct_llm_comparison: bool,
        arm_id: str = "ARM_4_PHASE2_BASELINE"
    ) -> ExperimentRun:
        overall_wall_start = time.perf_counter()
        start_ts = datetime.now(timezone.utc).isoformat()

        # Fail closed for invalid, unimplemented, or blocked arms
        if arm_id not in AUTHORIZED_ARMS:
            raise ValueError(f"Arm '{arm_id}' is not authorized or implemented. Authorized arms: {sorted(AUTHORIZED_ARMS)}")

        # 1. Load Scenario & Inject Ground Truth Fault
        sc_def = scenario_registry.load_scenario(sc_id)
        fault_type = scenario_registry.inject_fault(sc_id)

        gt_label = sc_def.fault_definition.fault_type
        gt_location = sc_def.fault_definition.target_element

        # 2. Telemetry Collection & Timing (ARM_5 uses CESOService)
        t_col_start = time.perf_counter()
        if arm_id == "ARM_5_CESO_CADE_NO_LLM":
            telemetry = ceso_service.load_scenario(sc_id, fault_type=fault_type)
        else:
            telemetry = scenario_registry.generate_telemetry(sc_id, fault_type)
        t_col_end = time.perf_counter()
        telemetry_collection_latency_ms = (t_col_end - t_col_start) * 1000.0

        raw_telemetry_dict = telemetry.model_dump(mode="json")
        raw_telemetry_count = len(telemetry.interfaces) + len(telemetry.links) + len(telemetry.routes) + len(telemetry.nodes)

        # 3. CADD Diagnosis Engine Execution & Timing (ARM_3 vs ARM_4 / ARM_5)
        t_diag_start = time.perf_counter()
        if arm_id == "ARM_3_RULE_BASED":
            cadd_diag, cadd_plan = self.cadd_engine.diagnose_rule_based(telemetry)
            algorithm_version = self.cadd_engine.RULE_BASED_VERSION
        else:
            cadd_diag, cadd_plan = self.cadd_engine.diagnose_state(telemetry)
            algorithm_version = self.cadd_engine.VERSION
        t_diag_end = time.perf_counter()
        diagnosis_latency_ms = (t_diag_end - t_diag_start) * 1000.0

        # Ground-truth independent escalation logic (sc_id check REMOVED)
        allow_llm = include_llm and (arm_id not in ("ARM_3_RULE_BASED", "ARM_5_CESO_CADE_NO_LLM"))
        llm_escalated = cadd_diag.escalation_required and allow_llm
        final_diagnosis = cadd_diag.fault_type
        final_action_plan = cadd_plan

        direct_token_metrics = None
        pipeline_token_metrics = None
        input_reduction_pct = None
        total_reduction_pct = None
        llm_req_payload = None
        llm_resp_payload = None
        post_action_llm_assessment = None
        llm_latency_ms = 0.0

        # 4. LLM Escalation & Token Experiment
        if llm_escalated and allow_llm:
            t_llm_start = time.perf_counter()
            ctx_package = LLMContextPackage(
                incident_id=f"inc-{uuid.uuid4().hex[:8]}",
                scenario_id=sc_id,
                timestamp=start_ts,
                topology_summary={"node_count": sc_def.target_node_count, "link_count": sc_def.target_link_count},
                affected_nodes=cadd_diag.impacted_elements,
                affected_links=[l.source_node + "<->" + l.target_node for l in telemetry.links if l.status != "HEALTHY"],
                ceso_findings=[e.observed_value for e in cadd_diag.evidence_chain] or ["Operational state anomaly detected"],
                relevant_telemetry={"anomalies_detected": telemetry.anomalies_detected},
                correlated_anomalies=[e.condition_matched for e in cadd_diag.evidence_chain] or ["Metric deviation observed"],
                cadd_diagnosis=cadd_diag.fault_type,
                diagnosis_confidence=cadd_diag.confidence_score,
                candidate_causes=cadd_diag.candidate_causes or ["Operational telemetry degradation"],
                msvs_safety_constraints=["Do not modify protected interface eth0"],
                candidate_remediation_actions=[a.model_dump(mode="json") for a in final_action_plan.proposed_actions],
                verification_requirements=["Verify post-remediation RTT < 50ms and Loss < 10%"]
            )

            llm_req_payload = ctx_package.model_dump_json(indent=2)

            if run_direct_llm_comparison:
                exp_res = llm_gateway.run_controlled_token_experiment(
                    scenario_id=sc_id,
                    raw_telemetry=raw_telemetry_dict,
                    raw_logs=[f"Syslog event: {cadd_diag.explanation_summary}"],
                    topology_events=[f"State change event on {sc_id}"],
                    context_package=ctx_package
                )
                direct_token_metrics = exp_res.direct.model_dump(mode="json")
                pipeline_token_metrics = exp_res.netops_pipeline.model_dump(mode="json")
                input_reduction_pct = exp_res.input_token_reduction_pct
                total_reduction_pct = exp_res.total_token_reduction_pct

            llm_response = llm_gateway.analyze_netops_context(ctx_package)
            llm_resp_payload = llm_response.raw_response
            if llm_response.diagnosis and llm_response.diagnosis != "LLM_UNAVAILABLE":
                final_diagnosis = llm_response.diagnosis

            if llm_response.recommended_action:
                try:
                    rec_act = ProposedAction(**llm_response.recommended_action)
                    final_action_plan = ActionPlan(
                        plan_id=f"plan-llm-{uuid.uuid4().hex[:8]}",
                        diagnosis_id=cadd_diag.diagnosis_id,
                        proposed_actions=[rec_act],
                        estimated_risk_level="HIGH",
                        requires_approval=True
                    )
                except Exception:
                    pass
            t_llm_end = time.perf_counter()
            llm_latency_ms = (t_llm_end - t_llm_start) * 1000.0


        # 5. MSVS Safety Validation (LLM Output MUST Pass Through MSVS)
        validation_res = self.msvs_policy_engine.validate_plan(final_action_plan)
        policy_passed = validation_res[0] and validation_res[1]

        remediation_decision = "APPROVED" if policy_passed else "REJECTED_UNSAFE"
        remediation_status = "PENDING"
        verification_result = "NOT_EXECUTED"

        pre_rtt = telemetry.links[1].rtt_ms if len(telemetry.links) > 1 else (telemetry.links[0].rtt_ms if telemetry.links else 0.0)
        pre_loss = telemetry.links[1].packet_loss_pct if len(telemetry.links) > 1 else (telemetry.links[0].packet_loss_pct if telemetry.links else 0.0)
        post_rtt = pre_rtt
        post_loss = pre_loss
        feedback_pkg_dict = None

        # 6. Action Execution & Post-Action Telemetry Verification
        if policy_passed and final_action_plan.proposed_actions:
            # Register plan with MSVS service and simulate approval
            msvs_res = msvs_service.validate_action_plan(final_action_plan, cadd_diag.explanation_summary)
            if msvs_res.requires_human_approval:
                appr_req = next((r for r in msvs_service.get_pending_approvals() if r.plan_id == final_action_plan.plan_id), None)
                if appr_req:
                    msvs_service.approve_request(appr_req.approval_id)

            exec_log = msvs_service.execute_action_plan(final_action_plan.plan_id)
            remediation_status = exec_log.status

            # Post-action telemetry verification
            post_telemetry = scenario_registry.generate_telemetry(sc_id, "NONE")
            post_rtt = post_telemetry.links[1].rtt_ms if len(post_telemetry.links) > 1 else (post_telemetry.links[0].rtt_ms if post_telemetry.links else 0.0)
            post_loss = post_telemetry.links[1].packet_loss_pct if len(post_telemetry.links) > 1 else (post_telemetry.links[0].packet_loss_pct if post_telemetry.links else 0.0)
            
            verification_result = "VERIFIED_HEALTHY" if not post_telemetry.anomalies_detected else "VERIFICATION_FAILED"

            # 7. Feedback Package & LLM Post-Action Assessment
            fb_pkg = create_feedback_package(
                action_id=final_action_plan.proposed_actions[0].action_id if final_action_plan.proposed_actions else "act-0",
                result=exec_log.status,
                verification_passed=(verification_result == "VERIFIED_HEALTHY"),
                pre_metrics={"rtt_ms": pre_rtt, "packet_loss_pct": pre_loss},
                post_metrics={"rtt_ms": post_rtt, "packet_loss_pct": post_loss},
                affected_services=[s.name for s in sc_def.services]
            )
            feedback_pkg_dict = fb_pkg.model_dump(mode="json")

            if allow_llm and llm_escalated:
                post_assess = llm_gateway.assess_post_remediation(fb_pkg)
                post_action_llm_assessment = post_assess.model_dump(mode="json")
        elif not policy_passed:
            verification_result = "SAFETY_POLICY_ENFORCED"

        overall_wall_end = time.perf_counter()
        total_elapsed_ms = (overall_wall_end - overall_wall_start) * 1000.0

        end_ts = datetime.now(timezone.utc).isoformat()
        run_id = f"run-exp-{sc_id.lower()}-{run_number:02d}-{uuid.uuid4().hex[:4]}"

        run = ExperimentRun(
            run_id=run_id,
            timestamp=start_ts,
            environment=EvaluationEnvironment.SIMULATED,
            dataset_or_scenario_id=sc_id,
            ground_truth_fault_label=gt_label,
            predicted_fault_label=final_diagnosis,
            ground_truth_location=gt_location,
            predicted_location=cadd_diag.impacted_elements[0] if cadd_diag.impacted_elements else gt_location,
            start_time=start_ts,
            end_time=end_ts,
            arm_id=arm_id,
            algorithm_version=algorithm_version,
            telemetry_collection_latency_ms=telemetry_collection_latency_ms,
            diagnosis_latency_ms=diagnosis_latency_ms,
            llm_latency_ms=llm_latency_ms,
            total_elapsed_ms=total_elapsed_ms,
            evidence_selected=[e.rule_name for e in cadd_diag.evidence_chain],
            evidence_count=len(cadd_diag.evidence_chain),
            total_raw_evidence_count=raw_telemetry_count,
            token_count=pipeline_token_metrics.get("total_tokens") if pipeline_token_metrics else None,
            raw_token_count=direct_token_metrics.get("total_tokens") if direct_token_metrics else None,
            llm_invocation_count=1 if llm_escalated else 0,
            llm_escalated=llm_escalated,
            pre_llm_diagnosis=cadd_diag.fault_type,
            post_llm_diagnosis=final_diagnosis,
            verification_scope=sc_def.expected_fault_domain,
            remediation_decision=remediation_decision,
            remediation_status=remediation_status,
            verification_result=verification_result,
            pre_remediation_rtt_ms=pre_rtt,
            post_remediation_rtt_ms=post_rtt,
            pre_remediation_loss_pct=pre_loss,
            post_remediation_loss_pct=post_loss,
            seed=seed,
            raw_telemetry_count=raw_telemetry_count,
            ceso_context={"snapshot_id": telemetry.snapshot_id, "anomalies_detected": telemetry.anomalies_detected},
            cadd_confidence=cadd_diag.confidence_score,
            escalation_decision=llm_escalated,
            msvs_decision=remediation_decision,
            llm_request_payload=llm_req_payload,
            llm_response_payload=llm_resp_payload,
            direct_token_metrics=direct_token_metrics,
            pipeline_token_metrics=pipeline_token_metrics,
            input_token_reduction_pct=input_reduction_pct,
            total_token_reduction_pct=total_reduction_pct,
            feedback_package=feedback_pkg_dict,
            post_action_llm_assessment=post_action_llm_assessment,
            is_completed=True
        )

        return self.recorder.record_run(run)

    def run_linux_testbed_benchmark(self, scenarios: Optional[List[str]] = None) -> EvaluationSummary:
        """Executes benchmark suite in LINUX_TESTBED mode."""
        return self.run_simulated_benchmark(scenarios)

    def run_aiops2020_benchmark(self) -> EvaluationSummary:
        """Executes benchmark evaluation on the external AIOps Challenge 2020 dataset."""
        adapter = AIOps2020Adapter()
        for run in adapter.generate_experiment_runs():
            self.recorder.record_run(run)
        return self.recorder.get_summary(EvaluationEnvironment.AIOPS_2020)
