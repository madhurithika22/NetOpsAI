from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.scenarios.base import ScenarioDefinition
from app.scenarios.registry import scenario_registry
from app.ceso.service import ceso_service

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

class FaultInjectRequest(BaseModel):
    fault_type: Optional[str] = None

@router.get("", response_model=List[ScenarioDefinition])
def list_scenarios():
    return scenario_registry.list_scenarios()

@router.get("/{scenario_id}", response_model=ScenarioDefinition)
def get_scenario(scenario_id: str):
    sc = scenario_registry.get_scenario(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return sc

@router.post("/{scenario_id}/load")
def load_scenario(scenario_id: str):
    try:
        sc = ceso_service.load_scenario(scenario_id)
        return {
            "status": "loaded",
            "scenario_id": scenario_id,
            "name": sc.name,
            "target_node_count": sc.target_node_count,
            "target_link_count": sc.target_link_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{scenario_id}/inject-fault")
def inject_fault(scenario_id: str, req: Optional[FaultInjectRequest] = None):
    try:
        fault_type = req.fault_type if req else None
        active_fault = ceso_service.inject_fault(fault_type or "HIGH_LATENCY_CONGESTION")
        latest_state = ceso_service.get_latest_state()
        return {
            "status": "fault_injected",
            "scenario_id": scenario_id,
            "active_fault": active_fault,
            "snapshot_id": latest_state.snapshot_id,
            "anomalies_detected": latest_state.anomalies_detected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{scenario_id}/reset")
def reset_scenario(scenario_id: str):
    try:
        state = ceso_service.reset_simulation()
        return {
            "status": "reset",
            "scenario_id": scenario_id,
            "snapshot_id": state.snapshot_id,
            "anomalies_detected": state.anomalies_detected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
