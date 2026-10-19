import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class WorkflowMetricRecord(BaseModel):
    record_id: str
    fault_profile: str
    fault_injection_time: Optional[datetime] = None
    detection_time: Optional[datetime] = None
    diagnosis_time: Optional[datetime] = None
    approval_time: Optional[datetime] = None
    execution_time: Optional[datetime] = None
    verification_time: Optional[datetime] = None
    initial_rtt_ms: Optional[float] = None
    final_rtt_ms: Optional[float] = None
    initial_loss_pct: Optional[float] = None
    final_loss_pct: Optional[float] = None
    remediation_status: str = "PENDING"  # SUCCESS, FAILED, REJECTED, BLOCKED
    policy_passed: bool = True

class EvaluationMetricsSummary(BaseModel):
    total_incidents: int = 0
    completed_workflows: int = 0
    mean_mttd_seconds: float = 0.0
    mean_mttr_seconds: float = 0.0
    mean_diagnostic_latency_seconds: float = 0.0
    remediation_success_rate_pct: float = 0.0
    policy_prevention_rate_pct: float = 0.0
    records: List[WorkflowMetricRecord] = Field(default_factory=list)

class EvaluationTracker:
    """
    Tracks workflow lifecycle timestamps and computes research metrics (MTTD, MTTR, Success Rate, Policy Prevention).
    """
    def __init__(self):
        self.records: List[WorkflowMetricRecord] = []
        self.policy_checks_count: int = 0
        self.policy_blocked_count: int = 0

    def record_fault_injection(self, record_id: str, fault_profile: str, rtt: float = 0.0, loss: float = 0.0) -> WorkflowMetricRecord:
        rec = WorkflowMetricRecord(
            record_id=record_id,
            fault_profile=fault_profile,
            fault_injection_time=datetime.now(timezone.utc),
            initial_rtt_ms=rtt,
            initial_loss_pct=loss
        )
        self.records.append(rec)
        return rec

    def record_detection(self, record_id: str):
        rec = self._get_record(record_id)
        if rec and not rec.detection_time:
            rec.detection_time = datetime.now(timezone.utc)

    def record_diagnosis(self, record_id: str):
        rec = self._get_record(record_id)
        if rec and not rec.diagnosis_time:
            rec.diagnosis_time = datetime.now(timezone.utc)

    def record_policy_check(self, record_id: str, is_valid: bool):
        self.policy_checks_count += 1
        if not is_valid:
            self.policy_blocked_count += 1
        rec = self._get_record(record_id)
        if rec:
            rec.policy_passed = is_valid

    def record_approval(self, record_id: str):
        rec = self._get_record(record_id)
        if rec:
            rec.approval_time = datetime.now(timezone.utc)

    def record_execution(self, record_id: str):
        rec = self._get_record(record_id)
        if rec:
            rec.execution_time = datetime.now(timezone.utc)

    def record_verification(self, record_id: str, success: bool, final_rtt: float = 0.0, final_loss: float = 0.0):
        rec = self._get_record(record_id)
        if rec:
            rec.verification_time = datetime.now(timezone.utc)
            rec.remediation_status = "SUCCESS" if success else "FAILED"
            rec.final_rtt_ms = final_rtt
            rec.final_loss_pct = final_loss

    def compute_summary(self) -> EvaluationMetricsSummary:
        mttd_list: List[float] = []
        mttr_list: List[float] = []
        diag_latency_list: List[float] = []
        success_count = 0
        completed_workflows = 0

        for r in self.records:
            # MTTD = detection_time - fault_injection_time
            if r.fault_injection_time and r.detection_time:
                mttd_list.append((r.detection_time - r.fault_injection_time).total_seconds())

            # Diagnostic Latency = diagnosis_time - detection_time
            if r.detection_time and r.diagnosis_time:
                diag_latency_list.append((r.diagnosis_time - r.detection_time).total_seconds())

            # MTTR = verification_time - fault_injection_time
            if r.fault_injection_time and r.verification_time:
                mttr_list.append((r.verification_time - r.fault_injection_time).total_seconds())
                completed_workflows += 1

            if r.remediation_status == "SUCCESS":
                success_count += 1

        mean_mttd = sum(mttd_list) / len(mttd_list) if mttd_list else 0.0
        mean_mttr = sum(mttr_list) / len(mttr_list) if mttr_list else 0.0
        mean_diag = sum(diag_latency_list) / len(diag_latency_list) if diag_latency_list else 0.0
        success_rate = (success_count / completed_workflows * 100.0) if completed_workflows > 0 else 0.0
        policy_prevention_rate = (self.policy_blocked_count / self.policy_checks_count * 100.0) if self.policy_checks_count > 0 else 0.0

        return EvaluationMetricsSummary(
            total_incidents=len(self.records),
            completed_workflows=completed_workflows,
            mean_mttd_seconds=round(mean_mttd, 3),
            mean_mttr_seconds=round(mean_mttr, 3),
            mean_diagnostic_latency_seconds=round(mean_diag, 3),
            remediation_success_rate_pct=round(success_rate, 2),
            policy_prevention_rate_pct=round(policy_prevention_rate, 2),
            records=self.records
        )

    def export_csv(self) -> str:
        summary = self.compute_summary()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Record ID", "Fault Profile", "Fault Injection Time", "Detection Time",
            "Diagnosis Time", "Approval Time", "Execution Time", "Verification Time",
            "Initial RTT (ms)", "Final RTT (ms)", "Status", "Policy Passed"
        ])

        for r in summary.records:
            writer.writerow([
                r.record_id,
                r.fault_profile,
                r.fault_injection_time.isoformat() if r.fault_injection_time else "",
                r.detection_time.isoformat() if r.detection_time else "",
                r.diagnosis_time.isoformat() if r.diagnosis_time else "",
                r.approval_time.isoformat() if r.approval_time else "",
                r.execution_time.isoformat() if r.execution_time else "",
                r.verification_time.isoformat() if r.verification_time else "",
                r.initial_rtt_ms if r.initial_rtt_ms is not None else "",
                r.final_rtt_ms if r.final_rtt_ms is not None else "",
                r.remediation_status,
                r.policy_passed
            ])
        return output.getvalue()

    def _get_record(self, record_id: str) -> Optional[WorkflowMetricRecord]:
        return next((r for r in self.records if r.record_id == record_id), None)

# Singleton tracker instance
evaluation_tracker = EvaluationTracker()
