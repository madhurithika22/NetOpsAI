from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from app.llm.gateway import llm_gateway
from app.llm.models import (
    LLMHealthStatus, LLMContextPackage, LLMDiagnosisResponse,
    DirectVsNetOpsExperimentResult, DirectLLMRequest
)
from app.scenarios.registry import scenario_registry
from app.cadd.engine import ExplainableRuleEngine

router = APIRouter(prefix="/llm", tags=["LLM Gateway"])

cadd_engine = ExplainableRuleEngine()

class LLMTestRequest(BaseModel):
    prompt: str = "Perform a quick diagnostic test of the local network LLM inference service."

@router.get("/health", response_model=LLMHealthStatus)
def llm_health_check():
    return llm_gateway.get_health()

@router.post("/test")
def llm_test_inference(req: Optional[LLMTestRequest] = None):
    health = llm_gateway.get_health()
    if not health.reachable:
        return {
            "status": "LLM_UNAVAILABLE",
            "health": health,
            "message": "Local LLM inference server is unreachable. Check provider configuration."
        }

    test_prompt = req.prompt if req else "Test connection."
    try:
        raw_resp, metrics = llm_gateway.provider.generate(
            "You are a network diagnostic assistant.", test_prompt
        )
        return {
            "status": "SUCCESS",
            "health": health,
            "response": raw_resp,
            "token_metrics": metrics.model_dump(mode="json")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/direct-analysis", response_model=LLMDiagnosisResponse)
def direct_llm_analysis(req: DirectLLMRequest):
    return llm_gateway.analyze_direct_raw_logs(
        scenario_id=req.scenario_id,
        raw_telemetry=req.raw_telemetry,
        raw_logs=req.raw_logs,
        topology_events=req.topology_events
    )

@router.post("/netops-analysis", response_model=LLMDiagnosisResponse)
def netops_llm_analysis(context_package: LLMContextPackage):
    return llm_gateway.analyze_netops_context(context_package)

@router.post("/token-experiment", response_model=DirectVsNetOpsExperimentResult)
def run_token_experiment(scenario_id: str = "CASE_04"):
    sc_def = scenario_registry.load_scenario(scenario_id)
    fault = scenario_registry.inject_fault(scenario_id)
    telemetry = scenario_registry.generate_telemetry(scenario_id, fault)
    cadd_report, _ = cadd_engine.diagnose_state(telemetry)

    raw_telemetry_dict = telemetry.model_dump(mode="json")

    ctx_package = LLMContextPackage(
        incident_id="inc-exp-04",
        scenario_id=scenario_id,
        timestamp=telemetry.timestamp.isoformat(),
        topology_summary={"node_count": sc_def.target_node_count, "link_count": sc_def.target_link_count},
        affected_nodes=cadd_report.impacted_elements,
        affected_links=[l.source_node + "<->" + l.target_node for l in telemetry.links if l.status != "HEALTHY"],
        ceso_findings=[f"Anomaly detected on {sc_def.name}"],
        relevant_telemetry={"anomalies_detected": telemetry.anomalies_detected},
        correlated_anomalies=[sc_def.fault_definition.description],
        cadd_diagnosis=cadd_report.fault_type,
        diagnosis_confidence=cadd_report.confidence_score,
        candidate_causes=cadd_report.candidate_causes or [sc_def.expected_fault_domain],
        msvs_safety_constraints=["Do not touch eth0"],
        candidate_remediation_actions=[a.model_dump(mode="json") for a in sc_def.remediation_candidates],
        verification_requirements=sc_def.verification_criteria
    )

    return llm_gateway.run_controlled_token_experiment(
        scenario_id=scenario_id,
        raw_telemetry=raw_telemetry_dict,
        raw_logs=[f"Syslog: {cadd_report.explanation_summary}"],
        topology_events=[f"Event on {scenario_id}"],
        context_package=ctx_package
    )
