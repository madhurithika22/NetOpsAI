import uuid
from datetime import datetime, timezone
from typing import Tuple, Optional, List, Dict, Any

from app.models.ceso_models import NetworkState
from app.models.cadd_models import DiagnosticReport, ActionPlan, ProposedAction, LLMEscalationResult
from app.cadd.engine import ExplainableRuleEngine
from app.msvs.metrics import evaluation_tracker
from app.msvs.service import msvs_service
from app.ceso.service import ceso_service
from app.llm.gateway import llm_gateway, LLMGateway
from app.llm.models import LLMContextPackage, LLMStatus


def build_operational_llm_context(
    state: NetworkState,
    report: DiagnosticReport,
    plan: Optional[ActionPlan] = None,
    incident_id: Optional[str] = None
) -> LLMContextPackage:
    """
    Constructs an LLMContextPackage strictly from operational evidence.
    Neutralizes benchmark scenario identifiers and excludes ground-truth labels,
    answer keys, or injected fault descriptions.
    """
    inc_id = incident_id or f"inc-{uuid.uuid4().hex[:8]}"
    start_ts = datetime.now(timezone.utc).isoformat()
    affected_links = [
        f"{l.source_node}<->{l.target_node}"
        for l in (state.links or [])
        if getattr(l, "status", None) != "HEALTHY"
    ]
    findings = [e.observed_value for e in report.evidence_chain] or ["Operational state anomaly detected"]
    anomalies = [e.condition_matched for e in report.evidence_chain] or ["Metric deviation observed"]
    candidate_actions = [a.model_dump(mode="json") for a in plan.proposed_actions] if plan and plan.proposed_actions else []

    return LLMContextPackage(
        incident_id=inc_id,
        scenario_id="operational-session",
        timestamp=start_ts,
        topology_summary={
            "node_count": len(state.nodes) if state.nodes else 0,
            "link_count": len(state.links) if state.links else 0
        },
        affected_nodes=list(report.impacted_elements or []),
        affected_links=affected_links,
        ceso_findings=findings,
        relevant_telemetry={"anomalies_detected": bool(state.anomalies_detected)},
        correlated_anomalies=anomalies,
        cadd_diagnosis=report.fault_type,
        diagnosis_confidence=float(report.confidence_score),
        candidate_causes=list(report.candidate_causes or ["Operational telemetry degradation"]),
        msvs_safety_constraints=[
            "Do not modify protected host interface eth0",
            "Command type must belong to permitted NetOps safety whitelist"
        ],
        candidate_remediation_actions=candidate_actions,
        verification_requirements={"rtt_max_ms": 50.0, "loss_max_pct": 10.0}
    )


class CADDService:
    """
    Context-Aware Diagnosis & Decision Service Coordinator.
    Coordinates CADE heuristic diagnosis, safe operational LLM escalation when uncertain,
    and MSVS Stage 1/2 validation handoff for pending human approval.
    """
    def __init__(self):
        self.engine = ExplainableRuleEngine()
        self.latest_report: DiagnosticReport | None = None
        self.latest_plan: ActionPlan | None = None
        self.latest_escalation: LLMEscalationResult | None = None

    def escalate_to_llm(
        self,
        state: NetworkState,
        report: DiagnosticReport,
        cadd_plan: ActionPlan,
        gateway: Optional[LLMGateway] = None
    ) -> Tuple[ActionPlan, LLMEscalationResult]:
        """
        Escalates observed operational evidence to the LLM for secondary root cause diagnosis
        and remediation planning.
        - Keeps pre-LLM diagnosis and secondary LLM diagnosis separate.
        - If LLM proposes a valid corrective action, wraps it in an ActionPlan with requires_approval=True
          and passes it through MSVS validation.
        - If valid, leaves it PENDING in the MSVS approval queue.
        - NEVER automatically approves or executes any proposal.
        """
        ctx_pkg = build_operational_llm_context(state, report, cadd_plan)
        gw = gateway or llm_gateway

        try:
            llm_response = gw.analyze_netops_context(ctx_pkg)
        except Exception as e:
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=LLMStatus.LLM_ERROR.value,
                post_llm_diagnosis=report.fault_type,
                reasoning_summary=f"LLM gateway invocation exception: {str(e)}",
                confidence=0.0,
                suggested_action=None,
                proposed_plan=None,
                validation_passed=None,
                policy_violations=[],
                approval_id=None,
                approval_status=None,
                remediation_decision="BLOCKED_LLM_FAILURE",
                remediation_status="NOT_EXECUTED",
                raw_response=str(e)
            )

        status_enum = getattr(llm_response, "llm_status", None)
        llm_status_str = status_enum.value if hasattr(status_enum, "value") else str(status_enum or "UNKNOWN")

        # Handle LLM failure or unavailability
        if llm_status_str != LLMStatus.LLM_AVAILABLE.value:
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=report.fault_type,
                reasoning_summary=getattr(llm_response, "reasoning_summary", "") or f"LLM unavailable: status={llm_status_str}",
                confidence=float(getattr(llm_response, "confidence", 0.0)),
                suggested_action=None,
                proposed_plan=None,
                validation_passed=None,
                policy_violations=[],
                approval_id=None,
                approval_status=None,
                remediation_decision="BLOCKED_LLM_FAILURE",
                remediation_status="NOT_EXECUTED",
                raw_response=getattr(llm_response, "raw_response", "")
            )

        # Validate secondary diagnosis
        diag = getattr(llm_response, "diagnosis", None)
        if not diag or diag in ("LLM_UNAVAILABLE", "LLM_ERROR", "LLM_DISABLED"):
            post_llm_diag = report.fault_type
            llm_status_str = LLMStatus.INVALID_RESPONSE.value
        else:
            post_llm_diag = diag

        rec = getattr(llm_response, "recommended_action", None)
        if not rec or not isinstance(rec, dict):
            # Diagnosis returned without action proposal
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0)),
                suggested_action=None,
                proposed_plan=None,
                validation_passed=None,
                policy_violations=[],
                approval_id=None,
                approval_status=None,
                remediation_decision="NO_ACTION_PROPOSED",
                remediation_status="NOT_EXECUTED",
                raw_response=getattr(llm_response, "raw_response", "")
            )

        # Convert recommended_action to ProposedAction
        proposed_act = None
        if "command_type" in rec and "target_device" in rec:
            try:
                proposed_act = ProposedAction(
                    action_id=rec.get("action_id", f"act-llm-{uuid.uuid4().hex[:6]}"),
                    command_type=rec["command_type"],
                    target_device=rec["target_device"],
                    parameters=rec.get("parameters", {}),
                    is_destructive=rec.get("is_destructive", True),
                    reversion_action=rec.get("reversion_action")
                )
            except Exception:
                proposed_act = None

        if not proposed_act:
            # Action conversion failed: preserve valid post_llm_diag!
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=LLMStatus.INVALID_RESPONSE.value,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0)),
                suggested_action=None,
                proposed_plan=None,
                validation_passed=None,
                policy_violations=[],
                approval_id=None,
                approval_status=None,
                remediation_decision="INVALID_ACTION_PROPOSAL",
                remediation_status="NOT_EXECUTED",
                raw_response=getattr(llm_response, "raw_response", "")
            )

        # Construct ActionPlan with requires_approval=True
        llm_action_plan = ActionPlan(
            plan_id=f"plan-llm-{uuid.uuid4().hex[:8]}",
            diagnosis_id=report.diagnosis_id,
            proposed_actions=[proposed_act],
            estimated_risk_level="HIGH",
            requires_approval=True
        )

        # Pass through MSVS validation
        summary_for_msvs = report.explanation_summary or f"LLM secondary diagnosis: {post_llm_diag}"
        validation_res = msvs_service.validate_action_plan(llm_action_plan, summary_for_msvs)

        if validation_res.is_valid:
            # Find the pending approval request created by MSVS
            appr_req = next(
                (r for r in msvs_service.get_pending_approvals() if r.plan_id == llm_action_plan.plan_id),
                None
            )
            appr_id = appr_req.approval_id if appr_req else None

            return llm_action_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0)),
                suggested_action=proposed_act,
                proposed_plan=llm_action_plan,
                validation_passed=True,
                policy_violations=[],
                approval_id=appr_id,
                approval_status="PENDING",
                remediation_decision="PENDING_APPROVAL",
                remediation_status="PENDING",
                raw_response=getattr(llm_response, "raw_response", "")
            )
        else:
            violations = [v.violation_reason for v in validation_res.policy_violations]
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0)),
                suggested_action=proposed_act,
                proposed_plan=llm_action_plan,
                validation_passed=False,
                policy_violations=violations,
                approval_id=None,
                approval_status=None,
                remediation_decision="REJECTED_UNSAFE",
                remediation_status="NOT_EXECUTED",
                raw_response=getattr(llm_response, "raw_response", "")
            )

    def diagnose_and_escalate(
        self,
        state: NetworkState
    ) -> Tuple[DiagnosticReport, ActionPlan, Optional[LLMEscalationResult]]:
        """
        Runs CADE diagnosis on network state, automatically escalating to LLM if CADE
        signals uncertainty (escalation_required=True).
        """
        report, plan = self.engine.diagnose_state(state)
        escalation_result: Optional[LLMEscalationResult] = None
        effective_plan = plan

        if report.escalation_required:
            effective_plan, escalation_result = self.escalate_to_llm(state, report, plan)

        self.latest_report = report
        self.latest_plan = effective_plan
        self.latest_escalation = escalation_result

        if ceso_service.active_record_id and report.fault_type != "HEALTHY":
            evaluation_tracker.record_diagnosis(ceso_service.active_record_id)

        return report, effective_plan, escalation_result

    def diagnose_network_state(self, state: NetworkState) -> Tuple[DiagnosticReport, ActionPlan]:
        """
        Standard diagnosis interface. Automatically coordinates operational escalation
        if CADE requires escalation, returning the original DiagnosticReport and the
        effective ActionPlan.
        """
        report, plan, _ = self.diagnose_and_escalate(state)
        return report, plan

    def get_latest_diagnosis(self) -> Tuple[DiagnosticReport | None, ActionPlan | None]:
        return self.latest_report, self.latest_plan

    def get_latest_diagnosis_full(self) -> Tuple[DiagnosticReport | None, ActionPlan | None, Optional[LLMEscalationResult]]:
        return self.latest_report, self.latest_plan, self.latest_escalation

# Singleton instance
cadd_service = CADDService()

