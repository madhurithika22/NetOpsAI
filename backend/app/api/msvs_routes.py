from fastapi import APIRouter, HTTPException, Response
from typing import List
from pydantic import BaseModel
from app.models.cadd_models import ActionPlan
from app.models.msvs_models import ValidationResult, ApprovalRequest, ExecutionLog
from app.msvs.service import msvs_service
from app.msvs.metrics import evaluation_tracker, EvaluationMetricsSummary

router = APIRouter(prefix="/msvs", tags=["MSVS Layer"])

class ValidateRequest(BaseModel):
    action_plan: ActionPlan
    diagnosis_summary: str = ""

@router.post("/validate", response_model=ValidationResult)
def validate_plan(req: ValidateRequest):
    """Validate an action plan against Stage 1 static policies & Stage 2 syntax checks."""
    return msvs_service.validate_action_plan(req.action_plan, req.diagnosis_summary)

@router.get("/approvals", response_model=List[ApprovalRequest])
def get_pending_approvals():
    """List pending human-in-the-loop approval requests."""
    return msvs_service.get_pending_approvals()

@router.post("/approvals/{approval_id}/approve", response_model=ApprovalRequest)
def approve_request(approval_id: str, reviewer_id: str = "OPERATOR_ADMIN"):
    """Approve a pending action plan."""
    res = msvs_service.approve_request(approval_id, reviewer_id)
    if not res:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return res

@router.post("/approvals/{approval_id}/reject", response_model=ApprovalRequest)
def reject_request(approval_id: str, reviewer_id: str = "OPERATOR_ADMIN"):
    """Reject a pending action plan."""
    res = msvs_service.reject_request(approval_id, reviewer_id)
    if not res:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return res

@router.post("/execute/{plan_id}", response_model=ExecutionLog)
def execute_plan(plan_id: str, operator_id: str = "OPERATOR_ADMIN"):
    """Execute an approved action plan in simulated environment and run Stage 5 post-verification."""
    try:
        return msvs_service.execute_action_plan(plan_id, operator_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))

@router.get("/audit-logs", response_model=List[ExecutionLog])
def get_audit_logs():
    """Retrieve audit history of executed actions."""
    return msvs_service.get_audit_logs()

@router.get("/metrics", response_model=EvaluationMetricsSummary)
def get_evaluation_metrics():
    """Retrieve research evaluation metrics (MTTD, MTTR, Diagnostic Latency, Success Rates)."""
    return evaluation_tracker.compute_summary()

@router.get("/metrics/export-csv")
def export_metrics_csv():
    """Export workflow evaluation records as a downloadable CSV file."""
    csv_data = evaluation_tracker.export_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=netops_metrics_export.csv"}
    )
