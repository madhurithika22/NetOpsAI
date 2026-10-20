import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models.cadd_models import ActionPlan
from app.models.msvs_models import ValidationResult, ApprovalRequest, ExecutionLog
from app.msvs.policies import SafetyPolicyEngine
from app.msvs.metrics import evaluation_tracker
from app.ceso.service import ceso_service

class MSVSService:
    """
    Multi-Stage Validation and Safety Service Coordinator.
    Manages validation, approval queue, simulated execution, and post-action verification.
    """
    def __init__(self):
        self.policy_engine = SafetyPolicyEngine()
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.action_plans: Dict[str, ActionPlan] = {}
        self.execution_logs: List[ExecutionLog] = []

    def validate_action_plan(self, plan: ActionPlan, diagnosis_summary: str = "") -> ValidationResult:
        self.action_plans[plan.plan_id] = plan
        stage1, stage2, violations = self.policy_engine.validate_plan(plan)
        is_valid = stage1 and stage2

        if ceso_service.active_record_id:
            evaluation_tracker.record_policy_check(ceso_service.active_record_id, is_valid)

        result = ValidationResult(
            plan_id=plan.plan_id,
            is_valid=is_valid,
            stage1_policy_passed=stage1,
            stage2_syntax_passed=stage2,
            policy_violations=violations,
            requires_human_approval=plan.requires_approval
        )

        # If valid and requires human approval, queue it
        if is_valid and plan.requires_approval:
            existing_req = next(
                (req for req in self.pending_approvals.values() if req.plan_id == plan.plan_id and req.status == "PENDING"),
                None
            )
            if not existing_req:
                approval_id = f"appr-{uuid.uuid4().hex[:8]}"
                actions_summary = "; ".join(
                    [f"{a.command_type} on {a.target_device} ({a.parameters})" for a in plan.proposed_actions]
                )
                req = ApprovalRequest(
                    approval_id=approval_id,
                    plan_id=plan.plan_id,
                    diagnosis_summary=diagnosis_summary or "Network degradation requiring remediation",
                    proposed_actions_summary=actions_summary,
                    status="PENDING",
                    requested_at=datetime.now(timezone.utc)
                )
                self.pending_approvals[approval_id] = req

        return result

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        return [req for req in self.pending_approvals.values() if req.status == "PENDING"]

    def approve_request(self, approval_id: str, reviewer_id: str = "OPERATOR_ADMIN") -> Optional[ApprovalRequest]:
        if approval_id in self.pending_approvals:
            req = self.pending_approvals[approval_id]
            req.status = "APPROVED"
            req.reviewed_at = datetime.now(timezone.utc)
            req.reviewed_by = reviewer_id
            if ceso_service.active_record_id:
                evaluation_tracker.record_approval(ceso_service.active_record_id)
            return req
        return None

    def reject_request(self, approval_id: str, reviewer_id: str = "OPERATOR_ADMIN") -> Optional[ApprovalRequest]:
        if approval_id in self.pending_approvals:
            req = self.pending_approvals[approval_id]
            req.status = "REJECTED"
            req.reviewed_at = datetime.now(timezone.utc)
            req.reviewed_by = reviewer_id
            return req
        return None

    def execute_action_plan(self, plan_id: str, operator_id: str = "OPERATOR_ADMIN") -> ExecutionLog:
        plan = self.action_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Action plan '{plan_id}' not found.")

        # Verify approval if required
        approval_req = next((req for req in self.pending_approvals.values() if req.plan_id == plan_id), None)
        if plan.requires_approval and (not approval_req or approval_req.status != "APPROVED"):
            raise PermissionError(f"Action plan '{plan_id}' has not been approved by an operator.")

        if ceso_service.active_record_id:
            evaluation_tracker.record_execution(ceso_service.active_record_id)

        # Stage 4: Controlled Simulated Execution
        commands_simulated = []
        for action in plan.proposed_actions:
            cmd = f"[SIMULATED EXECUTION] {action.command_type} target={action.target_device} params={action.parameters}"
            commands_simulated.append(cmd)

        pre_state = ceso_service.get_latest_state()

        # Trigger remediation state reset in CESO
        post_state = ceso_service.reset_simulation()

        # Stage 5: Post-Action Verification using actual post-action telemetry
        rtt_verified = not post_state.anomalies_detected
        post_rtt = post_state.links[1].rtt_ms if len(post_state.links) > 1 else (post_state.links[0].rtt_ms if post_state.links else 0.0)
        post_loss = post_state.links[1].packet_loss_pct if len(post_state.links) > 1 else (post_state.links[0].packet_loss_pct if post_state.links else 0.0)

        pre_rtt = pre_state.links[1].rtt_ms if len(pre_state.links) > 1 else (pre_state.links[0].rtt_ms if pre_state.links else 0.0)

        if ceso_service.active_record_id:
            evaluation_tracker.record_verification(
                ceso_service.active_record_id,
                success=rtt_verified,
                final_rtt=post_rtt,
                final_loss=post_loss
            )

        log = ExecutionLog(
            execution_id=f"exec-{uuid.uuid4().hex[:8]}",
            plan_id=plan_id,
            executed_at=datetime.now(timezone.utc),
            approved_by=operator_id,
            status="SUCCESS" if rtt_verified else "FAILED",
            commands_run=commands_simulated,
            post_verification_passed=rtt_verified,
            metrics_delta={
                "previous_rtt_ms": str(pre_rtt),
                "post_remediation_rtt_ms": str(post_rtt),
                "previous_packet_loss_pct": str(pre_state.links[1].packet_loss_pct if len(pre_state.links) > 1 else 0.0),
                "post_remediation_packet_loss_pct": str(post_loss),
                "status": "REMEDIATED" if rtt_verified else "UNRESOLVED"
            }
        )
        self.execution_logs.append(log)
        return log

    def get_audit_logs(self) -> List[ExecutionLog]:
        return self.execution_logs

# Singleton instance
msvs_service = MSVSService()
