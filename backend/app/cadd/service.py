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

INVALID_DIAGNOSES = {
    "", "NONE", "NULL", "UNKNOWN", "N/A", "NA", "ERROR",
    "LLM_ERROR", "LLM_UNAVAILABLE", "LLM_DISABLED", "INVALID_RESPONSE"
}

GENERIC_SAFETY_CONSTRAINTS = [
    "Do not modify protected host management interfaces (eth0, wlan0, lo, mgmt0, docker0)",
    "Command type must belong to permitted NetOps safety policy whitelist (e.g., traffic reroute, interface state, metric adjustment, QoS policy, or service reset)",
    "Destructive or state-changing actions require explicit human operator approval before execution",
    "Ensure action target device matches observed affected network nodes or egress gateways"
]


def extract_sanitized_telemetry(state: NetworkState) -> Dict[str, Any]:
    """
    Extracts an allowlisted, sanitized representation of observed operational telemetry
    from NetworkState without benchmark identifiers, ground-truth labels, or injected fault descriptions.
    Includes only structured, observed fields that are actually available from NetworkState.
    """
    telemetry: Dict[str, Any] = {
        "anomalies_detected": bool(state.anomalies_detected)
    }

    if state.interfaces:
        if_summary = {}
        for if_name, if_state in state.interfaces.items():
            if_summary[if_name] = {
                "is_up": if_state.is_up,
                "mtu": if_state.mtu,
                "rx_errors": if_state.rx_errors,
                "tx_errors": if_state.tx_errors,
                "rx_drops": if_state.rx_drops,
                "tx_drops": if_state.tx_drops,
                "utilization_pct": round(if_state.utilization_pct, 2),
                "throughput_bps": round(if_state.throughput_bps, 2),
            }
        telemetry["interfaces"] = if_summary

    if state.links:
        link_list = []
        for l in state.links:
            link_list.append({
                "source": l.source_node,
                "target": l.target_node,
                "status": l.status,
                "rtt_ms": round(l.rtt_ms, 2),
                "packet_loss_pct": round(l.packet_loss_pct, 2),
            })
        telemetry["links"] = link_list

    if state.routes:
        route_list = []
        for r in state.routes:
            route_list.append({
                "destination": r.destination,
                "gateway": r.gateway,
                "interface": r.interface,
                "metric": r.metric,
            })
        telemetry["routes"] = route_list

    if state.nodes:
        node_summary = {}
        for n_id, n_metrics in state.nodes.items():
            node_summary[n_id] = {
                "cpu_utilization_pct": round(n_metrics.cpu_utilization_pct, 2),
                "memory_utilization_pct": round(n_metrics.memory_utilization_pct, 2),
            }
        telemetry["nodes"] = node_summary

    return telemetry


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
    Provides complete sanitized operational telemetry and empty candidate actions
    so the LLM makes an independent recommendation without recovery-answer leakage.
    """
    inc_id = incident_id or f"inc-{uuid.uuid4().hex[:8]}"
    start_ts = datetime.now(timezone.utc).isoformat()
    affected_links = [
        f"{l.source_node}<->{l.target_node}"
        for l in (state.links or [])
        if getattr(l, "status", None) != "HEALTHY"
    ]
    findings = [
        f"{e.rule_name}: observed {e.observed_value} (threshold {e.threshold_value})"
        for e in report.evidence_chain
    ] or [e.observed_value for e in report.evidence_chain] or ["Operational state anomaly detected"]
    anomalies = [e.condition_matched for e in report.evidence_chain] or ["Metric deviation observed"]

    # Recovery-answer isolation: do NOT pass CADE's scenario-conditioned action or parameters to the LLM.
    # Provide an empty candidate action list; the LLM must recommend from generic permitted actions.
    candidate_actions: List[Dict[str, Any]] = []

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
        relevant_telemetry=extract_sanitized_telemetry(state),
        correlated_anomalies=anomalies,
        cadd_diagnosis=report.fault_type,
        diagnosis_confidence=float(report.confidence_score),
        candidate_causes=list(report.candidate_causes or ["Operational telemetry degradation"]),
        msvs_safety_constraints=list(GENERIC_SAFETY_CONSTRAINTS),
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
        - Keeps pre-LLM CADE diagnosis/plan and secondary LLM diagnosis/plan separate.
        - Validates the diagnosis response BEFORE processing any proposed action.
        - If diagnosis is empty, malformed, or an error/placeholder, sets llm_status=INVALID_RESPONSE,
          preserves the original CADE diagnosis, sets remediation to NOT_EXECUTED, and does not validate,
          queue, or return the proposed action as an actionable plan.
        - If the LLM proposes a valid corrective action for a valid diagnosis, wraps it in an ActionPlan
          with requires_approval=True and passes it through MSVS validation.
        - Leaves valid actions PENDING in the MSVS approval queue.
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

        # 1. Handle provider-level LLM failure or unavailability
        if llm_status_str != LLMStatus.LLM_AVAILABLE.value:
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=report.fault_type,
                reasoning_summary=getattr(llm_response, "reasoning_summary", "") or f"LLM unavailable: status={llm_status_str}",
                confidence=float(getattr(llm_response, "confidence", 0.0) or 0.0),
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

        # 2. Block invalid LLM diagnosis responses BEFORE action validation
        diag = getattr(llm_response, "diagnosis", None)
        if not diag or not str(diag).strip() or str(diag).strip().upper() in INVALID_DIAGNOSES:
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=LLMStatus.INVALID_RESPONSE.value,
                post_llm_diagnosis=report.fault_type,
                reasoning_summary=getattr(llm_response, "reasoning_summary", "") or "Invalid or placeholder diagnosis returned by LLM",
                confidence=float(getattr(llm_response, "confidence", 0.0) or 0.0),
                suggested_action=None,
                proposed_plan=None,
                validation_passed=None,
                policy_violations=[],
                approval_id=None,
                approval_status=None,
                remediation_decision="BLOCKED_INVALID_DIAGNOSIS",
                remediation_status="NOT_EXECUTED",
                raw_response=getattr(llm_response, "raw_response", "")
            )

        post_llm_diag = str(diag).strip()

        # 3. Process proposed action only if secondary diagnosis is valid
        rec = getattr(llm_response, "recommended_action", None)
        if not rec or not isinstance(rec, dict):
            # Diagnosis returned without action proposal
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0) or 0.0),
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
            # Action conversion failed: preserve valid post_llm_diag
            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=LLMStatus.INVALID_RESPONSE.value,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0) or 0.0),
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

            return cadd_plan, LLMEscalationResult(
                escalated=True,
                llm_status=llm_status_str,
                post_llm_diagnosis=post_llm_diag,
                reasoning_summary=getattr(llm_response, "reasoning_summary", ""),
                confidence=float(getattr(llm_response, "confidence", 0.0) or 0.0),
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
                confidence=float(getattr(llm_response, "confidence", 0.0) or 0.0),
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
        Preserves original CADE report and CADE action plan separately from the
        secondary LLM diagnosis and proposed plan.
        """
        report, plan = self.engine.diagnose_state(state)
        escalation_result: Optional[LLMEscalationResult] = None

        if report.escalation_required:
            _, escalation_result = self.escalate_to_llm(state, report, plan)

        self.latest_report = report
        self.latest_plan = plan
        self.latest_escalation = escalation_result

        if ceso_service.active_record_id and report.fault_type != "HEALTHY":
            evaluation_tracker.record_diagnosis(ceso_service.active_record_id)

        return report, plan, escalation_result

    def diagnose_network_state(self, state: NetworkState) -> Tuple[DiagnosticReport, ActionPlan]:
        """
        Standard diagnosis interface. Automatically coordinates operational escalation
        if CADE requires escalation, returning the original DiagnosticReport and the
        original CADE ActionPlan.
        """
        report, plan, _ = self.diagnose_and_escalate(state)
        return report, plan

    def get_latest_diagnosis(self) -> Tuple[DiagnosticReport | None, ActionPlan | None]:
        return self.latest_report, self.latest_plan

    def get_latest_diagnosis_full(self) -> Tuple[DiagnosticReport | None, ActionPlan | None, Optional[LLMEscalationResult]]:
        return self.latest_report, self.latest_plan, self.latest_escalation

    def clear_latest(self) -> None:
        """Clears the cached latest diagnosis and escalation results."""
        self.latest_report = None
        self.latest_plan = None
        self.latest_escalation = None

# Singleton instance
cadd_service = CADDService()

