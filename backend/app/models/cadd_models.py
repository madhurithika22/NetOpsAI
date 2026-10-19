from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

class DiagnosticEvidence(BaseModel):
    rule_id: str = Field(..., description="Unique rule ID e.g. RULE_HIGH_LATENCY")
    rule_name: str = Field(..., description="Human-readable rule name")
    condition_matched: str = Field(..., description="Condition expression matched e.g. rtt_ms > 100")
    observed_value: str = Field(..., description="Observed metric value e.g. 145.2 ms")
    threshold_value: str = Field(..., description="Configured rule threshold e.g. 100.0 ms")

class DiagnosticReport(BaseModel):
    diagnosis_id: str = Field(..., description="Unique diagnosis identifier")
    snapshot_id: str = Field(..., description="Associated state snapshot ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Diagnosis timestamp")
    fault_type: str = Field(..., description="Fault classification e.g. LINK_DEGRADED, INTERFACE_DOWN, BLACKHOLE_ROUTE")
    impacted_elements: List[str] = Field(default_factory=list, description="Nodes or links impacted")
    severity: str = Field("HIGH", description="Fault severity: LOW, MEDIUM, HIGH, CRITICAL")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Diagnostic confidence score 0.0 - 1.0")
    evidence_chain: List[DiagnosticEvidence] = Field(default_factory=list, description="Explainable rule evidence chain")
    explanation_summary: str = Field(..., description="Clear natural language explanation of diagnosis")
    escalation_required: bool = Field(False, description="Flag indicating if LLM escalation is required")
    candidate_causes: List[str] = Field(default_factory=list, description="List of possible candidate root causes")
    algorithm_version: str = Field("2.0.0-phase2", description="Version of CADE diagnostic engine")
    algorithm_config: Dict[str, float] = Field(default_factory=dict, description="Configuration parameters used during diagnosis")
    candidate_scores: Dict[str, float] = Field(default_factory=dict, description="Computed evidence scores for all diagnostic candidates")

class ProposedAction(BaseModel):
    action_id: str = Field(..., description="Unique action ID")
    command_type: str = Field(..., description="Action type e.g. REROUTE_TRAFFIC, SET_INTERFACE_STATE, ADJUST_METRIC")
    target_device: str = Field(..., description="Target device/node/interface")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    is_destructive: bool = Field(False, description="Flag for state-changing or high-risk actions")
    reversion_action: Optional[Dict[str, Any]] = Field(None, description="Rollback command parameters")

class ActionPlan(BaseModel):
    plan_id: str = Field(..., description="Unique action plan ID")
    diagnosis_id: str = Field(..., description="Associated diagnosis ID")
    proposed_actions: List[ProposedAction] = Field(default_factory=list, description="Ordered list of proposed remediation steps")
    estimated_risk_level: str = Field("MEDIUM", description="Risk assessment: LOW, MEDIUM, HIGH")
    requires_approval: bool = Field(True, description="Human-in-the-loop approval requirement flag")
