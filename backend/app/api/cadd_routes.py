from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.cadd_models import DiagnosticReport, ActionPlan, LLMEscalationResult
from app.ceso.service import ceso_service
from app.cadd.service import cadd_service

router = APIRouter(prefix="/cadd", tags=["CADD Layer"])

class DiagnosisResponse(BaseModel):
    diagnostic_report: DiagnosticReport
    action_plan: ActionPlan
    llm_escalation: Optional[LLMEscalationResult] = None

@router.post("/diagnose", response_model=DiagnosisResponse)
def run_diagnosis():
    """Run explainable CADD diagnosis on current CESO state with safe operational LLM escalation if uncertain."""
    state = ceso_service.get_latest_state()
    report, plan, escalation = cadd_service.diagnose_and_escalate(state)
    return DiagnosisResponse(
        diagnostic_report=report,
        action_plan=plan,
        llm_escalation=escalation
    )

@router.get("/latest", response_model=DiagnosisResponse)
def get_latest_diagnosis():
    """
    Fetch latest diagnostic report, action plan, and escalation result.
    Strictly read-only: does NOT initiate diagnosis, LLM escalation, or MSVS approval requests.
    Returns 404 if no prior diagnosis has been recorded.
    """
    report, plan, escalation = cadd_service.get_latest_diagnosis_full()
    if not report or not plan:
        raise HTTPException(
            status_code=404,
            detail="No prior diagnosis recorded. Run POST /cadd/diagnose first."
        )
    return DiagnosisResponse(
        diagnostic_report=report,
        action_plan=plan,
        llm_escalation=escalation
    )
