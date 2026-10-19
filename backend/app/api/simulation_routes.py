from fastapi import APIRouter, HTTPException, Response
from typing import Optional
from pydantic import BaseModel
from app.models.ceso_models import NetworkState
from app.ceso.service import ceso_service
from app.testbed.manager import testbed_manager, TestbedStatus
from app.testbed.faults import testbed_fault_injector
from app.msvs.benchmark import benchmark_runner, Phase3ExperimentReport

router = APIRouter(prefix="/simulation", tags=["Simulation & Testbed Controls"])

class FaultInjectionRequest(BaseModel):
    fault_type: str = "HIGH_LATENCY_CONGESTION"

class EnvironmentSwitchRequest(BaseModel):
    mode: str = "SIMULATED"  # "SIMULATED" or "LINUX_TESTBED"

class BenchmarkRunRequest(BaseModel):
    iterations_per_fault: int = 5
    environment_mode: str = "SIMULATED"

_latest_benchmark_report: Optional[Phase3ExperimentReport] = None

@router.get("/environment")
def get_environment_info():
    """Retrieve active environment mode and host platform info."""
    return {
        "mode": ceso_service.get_provider_mode(),
        "platform": testbed_manager.get_status().platform_name,
        "is_platform_supported": testbed_manager.is_supported_platform(),
        "testbed_status": testbed_manager.get_status()
    }

@router.post("/environment/switch")
def switch_environment_mode(req: EnvironmentSwitchRequest):
    """Switch active provider mode between SIMULATED and LINUX_TESTBED."""
    try:
        active = ceso_service.set_provider_mode(req.mode)
        return {
            "status": "success",
            "active_mode": active,
            "message": f"Switched telemetry provider mode to {active}."
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/testbed/status", response_model=TestbedStatus)
def get_testbed_status():
    """Get current status of Linux network namespace testbed."""
    return testbed_manager.get_status()

@router.post("/testbed/create", response_model=TestbedStatus)
def create_testbed():
    """Create isolated 4-node Linux network namespace testbed."""
    try:
        return testbed_manager.create_testbed()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/testbed/teardown", response_model=TestbedStatus)
def teardown_testbed():
    """Teardown NetOps-owned Linux network namespace testbed."""
    return testbed_manager.teardown_testbed()

@router.post("/inject-fault", response_model=NetworkState)
def inject_fault(req: FaultInjectionRequest):
    """Inject a simulated or testbed network degradation fault."""
    mode = ceso_service.get_provider_mode()
    if mode == "LINUX_TESTBED":
        testbed_fault_injector.inject_testbed_fault(req.fault_type)
    return ceso_service.inject_fault(req.fault_type)

@router.post("/reset", response_model=NetworkState)
def reset_simulation():
    """Reset simulation or testbed back to baseline healthy state."""
    mode = ceso_service.get_provider_mode()
    if mode == "LINUX_TESTBED":
        testbed_fault_injector.reset_testbed_faults()
    return ceso_service.reset_simulation()

@router.post("/benchmark/run", response_model=Phase3ExperimentReport)
def run_benchmark_suite(req: BenchmarkRunRequest):
    """Run Experimental Evaluation suite across all 4 fault profiles & safety tests."""
    global _latest_benchmark_report
    report = benchmark_runner.run_all_experiments(
        iterations_per_fault=req.iterations_per_fault,
        mode=req.environment_mode
    )
    _latest_benchmark_report = report
    return report

@router.get("/benchmark/results", response_model=Phase3ExperimentReport)
def get_benchmark_results():
    """Retrieve latest experimental evaluation report."""
    global _latest_benchmark_report
    if not _latest_benchmark_report:
        _latest_benchmark_report = benchmark_runner.run_all_experiments(iterations_per_fault=3)
    return _latest_benchmark_report

@router.get("/benchmark/export-csv")
def export_benchmark_csv():
    """Download benchmark trial details as a CSV file."""
    global _latest_benchmark_report
    if not _latest_benchmark_report:
        _latest_benchmark_report = benchmark_runner.run_all_experiments(iterations_per_fault=3)
    csv_content = benchmark_runner.export_benchmark_csv(_latest_benchmark_report)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=phase4_experimental_trials.csv"}
    )
