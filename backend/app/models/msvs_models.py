from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timezone

class PolicyViolation(BaseModel):
    policy_id: str = Field(..., description="Violated safety policy ID")
    policy_name: str = Field(..., description="Safety policy name")
    violation_reason: str = Field(..., description="Explanation of why action violated policy")

class ValidationResult(BaseModel):
    plan_id: str = Field(..., description="Associated action plan ID")
    is_valid: bool = Field(..., description="Overall validation status")
    stage1_policy_passed: bool = Field(..., description="Stage 1 static policy filter status")
    stage2_syntax_passed: bool = Field(..., description="Stage 2 dry-run/syntax check status")
    policy_violations: List[PolicyViolation] = Field(default_factory=list, description="List of policy violations")
    requires_human_approval: bool = Field(True, description="Human approval requirement flag")

class ApprovalRequest(BaseModel):
    approval_id: str = Field(..., description="Unique approval request ID")
    plan_id: str = Field(..., description="Target action plan ID")
    diagnosis_summary: str = Field(..., description="Summary of fault being remediated")
    proposed_actions_summary: str = Field(..., description="Summary of actions requested for approval")
    status: str = Field("PENDING", description="Approval status: PENDING, APPROVED, REJECTED")
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Request creation timestamp")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    reviewed_by: Optional[str] = Field(None, description="Reviewer identifier")

class ExecutionLog(BaseModel):
    execution_id: str = Field(..., description="Unique execution log ID")
    plan_id: str = Field(..., description="Executed action plan ID")
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Execution timestamp")
    approved_by: str = Field("SIMULATED_POLICY", description="Approver ID e.g. OPERATOR_ADMIN or AUTOMATED_POLICY")
    status: str = Field("SUCCESS", description="Execution status: SUCCESS, FAILED, ROLLED_BACK")
    commands_run: List[str] = Field(default_factory=list, description="Simulated/executed commands")
    post_verification_passed: bool = Field(True, description="Stage 5 post-action verification result")
    metrics_delta: Dict[str, str] = Field(default_factory=dict, description="Before and after metric comparison")
