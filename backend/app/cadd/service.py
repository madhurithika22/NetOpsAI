from typing import Tuple
from app.models.ceso_models import NetworkState
from app.models.cadd_models import DiagnosticReport, ActionPlan
from app.cadd.engine import ExplainableRuleEngine
from app.msvs.metrics import evaluation_tracker
from app.ceso.service import ceso_service

class CADDService:
    """
    Context-Aware Diagnosis & Decision Service Coordinator.
    """
    def __init__(self):
        self.engine = ExplainableRuleEngine()
        self.latest_report: DiagnosticReport | None = None
        self.latest_plan: ActionPlan | None = None

    def diagnose_network_state(self, state: NetworkState) -> Tuple[DiagnosticReport, ActionPlan]:
        report, plan = self.engine.diagnose_state(state)
        self.latest_report = report
        self.latest_plan = plan
        if ceso_service.active_record_id and report.fault_type != "HEALTHY":
            evaluation_tracker.record_diagnosis(ceso_service.active_record_id)
        return report, plan

    def get_latest_diagnosis(self) -> Tuple[DiagnosticReport | None, ActionPlan | None]:
        return self.latest_report, self.latest_plan

# Singleton instance
cadd_service = CADDService()
