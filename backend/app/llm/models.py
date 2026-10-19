from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class LLMStatus(str, Enum):
    LLM_AVAILABLE = "LLM_AVAILABLE"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_DISABLED = "LLM_DISABLED"
    LLM_ERROR = "LLM_ERROR"

class TokenMeasurementMethod(str, Enum):
    PROVIDER_REPORTED = "provider-reported"
    ESTIMATED = "estimated"

class LLMConfig(BaseModel):
    enabled: bool = True
    provider: str = "ollama"  # ollama | openai | mock
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    timeout_seconds: int = 120
    temperature: float = 0.1

class LLMHealthStatus(BaseModel):
    enabled: bool
    provider: str
    model: str
    status: LLMStatus
    reachable: bool
    latency_ms: float = 0.0
    error: Optional[str] = None

class LLMContextPackage(BaseModel):
    incident_id: str
    scenario_id: str
    timestamp: str
    topology_summary: Dict[str, Any] = Field(default_factory=dict)
    affected_nodes: List[str] = Field(default_factory=list)
    affected_links: List[str] = Field(default_factory=list)
    ceso_findings: List[str] = Field(default_factory=list)
    relevant_telemetry: Dict[str, Any] = Field(default_factory=dict)
    correlated_anomalies: List[str] = Field(default_factory=list)
    cadd_diagnosis: str
    diagnosis_confidence: float
    candidate_causes: List[str] = Field(default_factory=list)
    msvs_safety_constraints: List[str] = Field(default_factory=list)
    candidate_remediation_actions: List[Dict[str, Any]] = Field(default_factory=list)
    verification_requirements: Dict[str, Any] = Field(default_factory=dict)

class TokenMetrics(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    measurement_method: TokenMeasurementMethod = TokenMeasurementMethod.ESTIMATED

class LLMDiagnosisResponse(BaseModel):
    diagnosis: str
    reasoning_summary: str
    evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    recommended_action: Optional[Dict[str, Any]] = None
    alternatives: List[str] = Field(default_factory=list)
    uncertainty: str = ""
    raw_response: str = ""
    token_metrics: TokenMetrics = Field(default_factory=TokenMetrics)
    llm_status: LLMStatus = LLMStatus.LLM_AVAILABLE

class DirectLLMRequest(BaseModel):
    scenario_id: str
    raw_telemetry: Dict[str, Any]
    raw_logs: List[str] = Field(default_factory=list)
    topology_events: List[str] = Field(default_factory=list)

class LLMPostActionFeedbackRequest(BaseModel):
    action_id: str
    result: str
    verification_passed: bool
    pre_action_metrics: Dict[str, Any] = Field(default_factory=dict)
    post_action_metrics: Dict[str, Any] = Field(default_factory=dict)
    metric_deltas: Dict[str, Any] = Field(default_factory=dict)
    affected_services: List[str] = Field(default_factory=list)
    observed_side_effects: List[str] = Field(default_factory=list)

class LLMPostActionAssessment(BaseModel):
    diagnosis_supported: bool
    remediation_effective: bool
    additional_action_required: bool
    observation_recommended: bool
    assessment_summary: str
    raw_response: str = ""
    token_metrics: TokenMetrics = Field(default_factory=TokenMetrics)

class DirectVsNetOpsExperimentResult(BaseModel):
    scenario_id: str
    model: str
    provider: str
    direct: TokenMetrics
    netops_pipeline: TokenMetrics
    input_token_reduction_pct: float
    total_token_reduction_pct: float
    direct_response_summary: str
    netops_response_summary: str
    token_measurement_method: TokenMeasurementMethod
