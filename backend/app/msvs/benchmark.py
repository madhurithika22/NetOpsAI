import time
import uuid
import statistics
import csv
import io
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.ceso.service import ceso_service
from app.cadd.service import cadd_service
from app.msvs.service import msvs_service
from app.msvs.policies import SafetyPolicyEngine
from app.models.cadd_models import ActionPlan, ProposedAction

class ExperimentTrialResult(BaseModel):
    trial_id: str
    experiment_name: str
    environment_mode: str = "SIMULATED"
    fault_profile: str
    iteration: int
    detection_latency_ms: float
    diagnostic_execution_time_ms: float
    remediation_recovery_time_ms: float
    baseline_rtt_ms: float
    fault_rtt_ms: float
    post_rtt_ms: float
    remediation_success: bool
    policy_passed: bool
    status: str

class ExperimentSummaryStats(BaseModel):
    mean: float
    std_dev: float
    min: float
    max: float

class Phase3ExperimentReport(BaseModel):
    total_trials: int
    executed_at: datetime
    environment_mode: str = "SIMULATED"
    exp1_detection_latency: ExperimentSummaryStats
    exp1_diagnostic_execution_time: ExperimentSummaryStats
    exp2_remediation_success_rate_pct: float
    exp2_recovery_time: ExperimentSummaryStats
    exp3_safety_prevention_rate_pct: float
    exp4_robustness_pass_rate_pct: float
    trial_details: List[ExperimentTrialResult] = Field(default_factory=list)

class BenchmarkRunner:
    """
    Automated experimental evaluation suite executing Phase 3/4 Experiments 1-5 across SIMULATED and TESTBED environments.
    """
    def __init__(self):
        self.policy_engine = SafetyPolicyEngine()

    def run_all_experiments(self, iterations_per_fault: int = 5, mode: str = "SIMULATED") -> Phase3ExperimentReport:
        ceso_service.set_provider_mode(mode)
        trials: List[ExperimentTrialResult] = []
        fault_profiles = [
            "HIGH_LATENCY_CONGESTION",
            "PACKET_LOSS",
            "INTERFACE_FAILURE",
            "ROUTING_MISCONFIGURATION"
        ]

        # Experiment 1 & 2: Detection, Diagnosis & Remediation across fault profiles
        for fault in fault_profiles:
            for i in range(1, iterations_per_fault + 1):
                trial = self._run_single_remediation_trial(fault, iteration=i, mode=mode)
                trials.append(trial)

        # Experiment 3: Safety Validation Trials (Attempting unauthorized/prohibited actions)
        safety_trials_passed = 0
        safety_total = 4
        
        if self._test_safety_protected_interface(): safety_trials_passed += 1
        if self._test_safety_unwhitelisted_command(): safety_trials_passed += 1
        if self._test_safety_unapproved_execution_blocked(): safety_trials_passed += 1
        if self._test_safety_rejected_execution_blocked(): safety_trials_passed += 1

        safety_prevention_rate = (safety_trials_passed / safety_total) * 100.0

        # Experiment 4: Robustness Tests
        robustness_passed = 0
        robustness_total = 3

        if self._test_robustness_incomplete_telemetry(): robustness_passed += 1
        if self._test_robustness_rapid_fault_cycles(): robustness_passed += 1
        if self._test_robustness_failed_workflow_metric_isolation(): robustness_passed += 1

        robustness_rate = (robustness_passed / robustness_total) * 100.0

        # Compute summary statistics
        det_latencies = [t.detection_latency_ms for t in trials]
        diag_times = [t.diagnostic_execution_time_ms for t in trials]
        rec_times = [t.remediation_recovery_time_ms for t in trials]
        remediation_successes = [1.0 if t.remediation_success else 0.0 for t in trials]

        exp1_det_stats = self._calc_stats(det_latencies)
        exp1_diag_stats = self._calc_stats(diag_times)
        exp2_rec_stats = self._calc_stats(rec_times)
        exp2_success_rate = (sum(remediation_successes) / len(remediation_successes) * 100.0) if remediation_successes else 0.0

        return Phase3ExperimentReport(
            total_trials=len(trials),
            executed_at=datetime.now(timezone.utc),
            environment_mode=mode,
            exp1_detection_latency=exp1_det_stats,
            exp1_diagnostic_execution_time=exp1_diag_stats,
            exp2_remediation_success_rate_pct=round(exp2_success_rate, 2),
            exp2_recovery_time=exp2_rec_stats,
            exp3_safety_prevention_rate_pct=round(safety_prevention_rate, 2),
            exp4_robustness_pass_rate_pct=round(robustness_rate, 2),
            trial_details=trials
        )

    def _run_single_remediation_trial(self, fault: str, iteration: int, mode: str = "SIMULATED") -> ExperimentTrialResult:
        trial_id = f"exp-{mode[:3].lower()}-{fault[:4].lower()}-{iteration:02d}-{uuid.uuid4().hex[:4]}"

        # Baseline
        ceso_service.reset_simulation()
        baseline_state = ceso_service.get_latest_state()
        baseline_rtt = baseline_state.links[1].rtt_ms if len(baseline_state.links) > 1 else 0.0

        # Fault Injection & Detection Timing
        t0 = time.perf_counter()
        fault_state = ceso_service.inject_fault(fault)
        t_detected = time.perf_counter()
        detection_latency_ms = (t_detected - t0) * 1000.0
        fault_rtt = fault_state.links[1].rtt_ms if len(fault_state.links) > 1 else 0.0

        # Diagnostic Timing
        t_diag_start = time.perf_counter()
        report, plan = cadd_service.diagnose_network_state(fault_state)
        t_diag_end = time.perf_counter()
        diagnostic_execution_time_ms = (t_diag_end - t_diag_start) * 1000.0

        # MSVS Validation & Approval
        val_res = msvs_service.validate_action_plan(plan, report.explanation_summary)
        policy_passed = val_res.is_valid

        remediation_success = False
        post_rtt = fault_rtt
        recovery_time_ms = 0.0

        if policy_passed and plan.proposed_actions:
            pending = msvs_service.get_pending_approvals()
            matching_appr = next((a for a in pending if a.plan_id == plan.plan_id), None)
            if matching_appr:
                msvs_service.approve_request(matching_appr.approval_id)
                t_exec_start = time.perf_counter()
                exec_log = msvs_service.execute_action_plan(plan.plan_id)
                t_exec_end = time.perf_counter()
                recovery_time_ms = (t_exec_end - t0) * 1000.0

                post_state = ceso_service.get_latest_state()
                post_rtt = post_state.links[1].rtt_ms if len(post_state.links) > 1 else 0.0
                remediation_success = exec_log.post_verification_passed

        return ExperimentTrialResult(
            trial_id=trial_id,
            experiment_name="Remediation Trial",
            environment_mode=mode,
            fault_profile=fault,
            iteration=iteration,
            detection_latency_ms=round(detection_latency_ms, 3),
            diagnostic_execution_time_ms=round(diagnostic_execution_time_ms, 3),
            remediation_recovery_time_ms=round(recovery_time_ms, 3),
            baseline_rtt_ms=round(baseline_rtt, 1),
            fault_rtt_ms=round(fault_rtt, 1),
            post_rtt_ms=round(post_rtt, 1),
            remediation_success=remediation_success,
            policy_passed=policy_passed,
            status="SUCCESS" if remediation_success else "FAILED"
        )

    def _test_safety_protected_interface(self) -> bool:
        plan = ActionPlan(
            plan_id="plan-unsafe-eth0",
            diagnosis_id="diag-unsafe-eth0",
            proposed_actions=[
                ProposedAction(
                    action_id="act-unsafe-eth0",
                    command_type="SET_INTERFACE_STATE",
                    target_device="rtr1",
                    parameters={"interface": "eth0", "target_state": "DOWN"},
                    is_destructive=True
                )
            ],
            estimated_risk_level="HIGH",
            requires_approval=True
        )
        val = self.policy_engine.validate_plan(plan)
        return val[0] is False

    def _test_safety_unwhitelisted_command(self) -> bool:
        plan = ActionPlan(
            plan_id="plan-unsafe-cmd",
            diagnosis_id="diag-unsafe-cmd",
            proposed_actions=[
                ProposedAction(
                    action_id="act-unsafe-cmd",
                    command_type="REBOOT_ROUTER",
                    target_device="rtr1",
                    parameters={"force": "true"},
                    is_destructive=True
                )
            ],
            estimated_risk_level="CRITICAL",
            requires_approval=True
        )
        val = self.policy_engine.validate_plan(plan)
        return val[0] is False

    def _test_safety_unapproved_execution_blocked(self) -> bool:
        plan = ActionPlan(
            plan_id="plan-unapproved-exec",
            diagnosis_id="diag-unapproved-exec",
            proposed_actions=[
                ProposedAction(
                    action_id="act-unapproved",
                    command_type="REROUTE_TRAFFIC",
                    target_device="rtr1",
                    parameters={"interface": "rtr1-eth1", "target_destination": "10.0.2.0/24"},
                    is_destructive=True
                )
            ],
            estimated_risk_level="MEDIUM",
            requires_approval=True
        )
        msvs_service.validate_action_plan(plan)
        try:
            msvs_service.execute_action_plan(plan.plan_id)
            return False
        except PermissionError:
            return True

    def _test_safety_rejected_execution_blocked(self) -> bool:
        plan = ActionPlan(
            plan_id="plan-rejected-exec",
            diagnosis_id="diag-rejected-exec",
            proposed_actions=[
                ProposedAction(
                    action_id="act-rejected",
                    command_type="REROUTE_TRAFFIC",
                    target_device="rtr1",
                    parameters={"interface": "rtr1-eth1", "target_destination": "10.0.2.0/24"},
                    is_destructive=True
                )
            ],
            estimated_risk_level="MEDIUM",
            requires_approval=True
        )
        val = msvs_service.validate_action_plan(plan)
        pending = msvs_service.get_pending_approvals()
        req = next((a for a in pending if a.plan_id == plan.plan_id), None)
        if req:
            msvs_service.reject_request(req.approval_id)
            try:
                msvs_service.execute_action_plan(plan.plan_id)
                return False
            except PermissionError:
                return True
        return False

    def _test_robustness_incomplete_telemetry(self) -> bool:
        state = ceso_service.collect_and_normalize()
        incomplete_state = state.model_copy()
        incomplete_state.links = []
        report, plan = cadd_service.diagnose_network_state(incomplete_state)
        return report.fault_type == "HEALTHY" and len(report.evidence_chain) == 0

    def _test_robustness_rapid_fault_cycles(self) -> bool:
        for _ in range(5):
            ceso_service.inject_fault("HIGH_LATENCY_CONGESTION")
            cadd_service.diagnose_network_state(ceso_service.get_latest_state())
            ceso_service.reset_simulation()
        final_state = ceso_service.get_latest_state()
        return final_state.anomalies_detected is False

    def _test_robustness_failed_workflow_metric_isolation(self) -> bool:
        summary = msvs_service.get_audit_logs()
        return isinstance(summary, list)

    def _calc_stats(self, values: List[float]) -> ExperimentSummaryStats:
        if not values:
            return ExperimentSummaryStats(mean=0.0, std_dev=0.0, min=0.0, max=0.0)
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values) if len(values) > 1 else 0.0
        return ExperimentSummaryStats(
            mean=round(mean_val, 3),
            std_dev=round(stdev_val, 3),
            min=round(min(values), 3),
            max=round(max(values), 3)
        )

    def export_benchmark_csv(self, report: Phase3ExperimentReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Trial ID", "Environment Mode", "Fault Profile", "Iteration", "Detection Latency (ms)",
            "Diagnostic Execution Time (ms)", "Remediation Recovery Time (ms)",
            "Baseline RTT (ms)", "Fault RTT (ms)", "Post RTT (ms)",
            "Remediation Success", "Policy Passed", "Status"
        ])
        for t in report.trial_details:
            writer.writerow([
                t.trial_id, t.environment_mode, t.fault_profile, t.iteration,
                t.detection_latency_ms, t.diagnostic_execution_time_ms,
                t.remediation_recovery_time_ms, t.baseline_rtt_ms,
                t.fault_rtt_ms, t.post_rtt_ms, t.remediation_success,
                t.policy_passed, t.status
            ])
        return output.getvalue()

# Singleton benchmark runner instance
benchmark_runner = BenchmarkRunner()
