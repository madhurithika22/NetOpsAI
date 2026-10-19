from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    MEASURED = "MEASURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_MEASURED = "NOT_MEASURED"
    INVALID_RUN = "INVALID_RUN"


class EvaluationEnvironment(str, Enum):
    SIMULATED = "SIMULATED"
    LINUX_TESTBED = "LINUX_TESTBED"
    AIOPS_2020 = "AIOPS_2020"


class MetricValue(BaseModel):
    name: str
    status: MetricStatus
    value: Optional[float] = None
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    unit: Optional[str] = None
    sample_count: int = 0
    description: str = ""
    exclusion_reason: Optional[str] = None


class ExperimentRun(BaseModel):
    run_id: str
    timestamp: str
    environment: EvaluationEnvironment
    dataset_or_scenario_id: str
    ground_truth_fault_label: str
    predicted_fault_label: Optional[str] = None
    ground_truth_location: Optional[str] = None
    predicted_location: Optional[str] = None
    start_time: str
    end_time: str
    arm_id: Optional[str] = "ARM_4_PHASE2_BASELINE"
    algorithm_version: Optional[str] = None
    telemetry_collection_latency_ms: float = 0.0
    diagnosis_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    total_elapsed_ms: float = 0.0
    evidence_selected: List[str] = Field(default_factory=list)
    evidence_count: int = 0
    total_raw_evidence_count: int = 0
    token_count: Optional[int] = None
    raw_token_count: Optional[int] = None
    llm_invocation_count: int = 0
    llm_escalated: bool = False
    pre_llm_diagnosis: Optional[str] = None
    post_llm_diagnosis: Optional[str] = None
    llm_status: Optional[str] = None
    verification_scope: Optional[str] = None
    remediation_decision: Optional[str] = None
    remediation_status: Optional[str] = None
    verification_result: Optional[str] = None
    pre_remediation_rtt_ms: Optional[float] = None
    post_remediation_rtt_ms: Optional[float] = None
    pre_remediation_loss_pct: Optional[float] = None
    post_remediation_loss_pct: Optional[float] = None
    seed: int = 42
    raw_telemetry_count: int = 0
    ceso_context: Optional[Dict[str, Any]] = None
    cadd_confidence: Optional[float] = None
    escalation_decision: bool = False
    msvs_decision: Optional[str] = None
    llm_request_payload: Optional[str] = None
    llm_response_payload: Optional[str] = None
    direct_token_metrics: Optional[Dict[str, Any]] = None
    pipeline_token_metrics: Optional[Dict[str, Any]] = None
    input_token_reduction_pct: Optional[float] = None
    total_token_reduction_pct: Optional[float] = None
    feedback_package: Optional[Dict[str, Any]] = None
    post_action_llm_assessment: Optional[Dict[str, Any]] = None
    is_completed: bool = True
    error_message: Optional[str] = None
    metrics: Dict[str, MetricValue] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    environment: str
    total_runs: int = 0
    completed_runs: int = 0
    excluded_runs: int = 0
    metrics: Dict[str, MetricValue] = Field(default_factory=dict)


class AIOps2020QualityReport(BaseModel):
    total_records: int = 0
    usable_records: int = 0
    excluded_records: int = 0
    exclusion_reasons: Dict[str, int] = Field(default_factory=dict)
    label_mapping_counts: Dict[str, int] = Field(default_factory=dict)
    adapter_version: str = "1.0.0"
    processing_config: Dict[str, Any] = Field(default_factory=dict)
