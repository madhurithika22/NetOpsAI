from fastapi import APIRouter
from pydantic import BaseModel
from app.models.cadd_models import DiagnosticReport, ActionPlan
from app.ceso.service import ceso_service
from app.cadd.service import cadd_service

router = APIRouter(prefix="/cadd", tags=["CADD Layer"])

class DiagnosisResponse(BaseModel):
    diagnostic_report: DiagnosticReport
    action_plan: ActionPlan

@router.post("/diagnose", response_model=DiagnosisResponse)
def run_diagnosis():
    """Run explainable CADD diagnosis on current CESO state."""
    state = ceso_service.get_latest_state()
    report, plan = cadd_service.diagnose_network_state(state)
    return DiagnosisResponse(diagnostic_report=report, action_plan=plan)

@router.get("/latest", response_model=DiagnosisResponse)
def get_latest_diagnosis():
    """Fetch latest diagnostic report and action plan."""
    report, plan = cadd_service.get_latest_diagnosis()
    if not report or not plan:
        state = ceso_service.get_latest_state()
        report, plan = cadd_service.diagnose_network_state(state)
    return DiagnosisResponse(diagnostic_report=report, action_plan=plan)
