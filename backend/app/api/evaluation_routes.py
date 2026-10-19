import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.evaluation.models import (
    ExperimentRun, EvaluationEnvironment, EvaluationSummary, AIOps2020QualityReport
)
from app.evaluation.recorder import ExperimentRecorder
from app.evaluation.runner import BenchmarkRunner
from app.adapters.aiops2020_adapter import AIOps2020Adapter
from app.scenarios.registry import scenario_registry

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarking"])
recorder = ExperimentRecorder()
runner = BenchmarkRunner(recorder=recorder)


class ExtendedBenchmarkRunRequest(BaseModel):
    environment: EvaluationEnvironment = EvaluationEnvironment.SIMULATED
    scenario_ids: Optional[List[str]] = Field(default=None, description="List of scenario IDs e.g. CASE_01, CASE_02, CASE_03, CASE_04")
    number_of_runs: int = Field(1, ge=1, le=50)
    seed: int = Field(42, description="Random seed for reproducible execution")
    include_llm: bool = Field(True, description="Enable LLM reasoning escalation for low confidence cases")
    run_direct_llm_comparison: bool = Field(True, description="Execute controlled Direct vs NetOps token comparison")
    persist_results: bool = Field(True, description="Persist experiment runs to JSON/CSV records")


@router.get("/scenarios")
def get_evaluation_scenarios():
    """Returns all scenarios available for benchmarking."""
    scs = scenario_registry.list_scenarios()
    return [
        {
            "scenario_id": sc.scenario_id,
            "name": sc.name,
            "category": sc.category,
            "target_node_count": sc.target_node_count,
            "target_link_count": sc.target_link_count,
            "fault_type": sc.fault_definition.fault_type,
            "llm_escalation_required": sc.llm_escalation_required
        }
        for sc in scs
    ]


@router.get("/experiments", response_model=List[ExperimentRun])
def list_experiments(environment: Optional[EvaluationEnvironment] = Query(None)):
    """Lists recorded experiment runs, optionally filtered by environment."""
    return recorder.list_runs(environment=environment)


@router.get("/experiments/{run_id}", response_model=ExperimentRun)
def get_experiment_detail(run_id: str):
    """Retrieves a single experiment run by ID."""
    run = recorder.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Experiment run '{run_id}' not found")
    return run


@router.post("/run-benchmark", response_model=EvaluationSummary)
def run_benchmark(request: ExtendedBenchmarkRunRequest):
    """Triggers controlled benchmark evaluation for requested environment & scenarios."""
    if request.environment == EvaluationEnvironment.SIMULATED:
        return runner.run_simulated_benchmark(
            scenario_ids=request.scenario_ids,
            number_of_runs=request.number_of_runs,
            seed=request.seed,
            include_llm=request.include_llm,
            run_direct_llm_comparison=request.run_direct_llm_comparison
        )
    elif request.environment == EvaluationEnvironment.LINUX_TESTBED:
        return runner.run_linux_testbed_benchmark(scenarios=request.scenario_ids)
    elif request.environment == EvaluationEnvironment.AIOPS_2020:
        return runner.run_aiops2020_benchmark()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported environment: {request.environment}")


@router.get("/llm-comparison")
def get_llm_token_comparison():
    """Retrieves token efficiency comparison results across recorded experiment runs."""
    runs = recorder.list_runs()
    comparison_records = []
    for r in runs:
        if r.direct_token_metrics and r.pipeline_token_metrics:
            comparison_records.append({
                "run_id": r.run_id,
                "scenario_id": r.dataset_or_scenario_id,
                "timestamp": r.timestamp,
                "direct": r.direct_token_metrics,
                "netops_pipeline": r.pipeline_token_metrics,
                "input_token_reduction_pct": r.input_token_reduction_pct,
                "total_token_reduction_pct": r.total_token_reduction_pct
            })
    return {
        "count": len(comparison_records),
        "experiments": comparison_records
    }


@router.get("/feedback")
def get_feedback_records():
    """Retrieves post-remediation verification feedback records."""
    runs = recorder.list_runs()
    feedback_records = []
    for r in runs:
        if r.feedback_package:
            feedback_records.append({
                "run_id": r.run_id,
                "scenario_id": r.dataset_or_scenario_id,
                "verification_result": r.verification_result,
                "feedback_package": r.feedback_package,
                "post_action_llm_assessment": r.post_action_llm_assessment
            })
    return {
        "count": len(feedback_records),
        "records": feedback_records
    }


@router.get("/metrics-summary", response_model=EvaluationSummary)
def get_metrics_summary(environment: EvaluationEnvironment = Query(EvaluationEnvironment.SIMULATED)):
    """Retrieves paper-defined metric summary for an environment group."""
    return recorder.get_summary(environment=environment)


@router.get("/aiops2020/report", response_model=AIOps2020QualityReport)
def get_aiops2020_report():
    """Retrieves schema validation, label mapping, and quality report for AIOps Challenge 2020 dataset."""
    adapter = AIOps2020Adapter()
    return adapter.generate_quality_report()


@router.get("/export/json")
def export_json():
    """Exports all recorded experiment runs in JSON format."""
    json_data = recorder.export_all_json()
    return Response(content=json_data, media_type="application/json", headers={"Content-Disposition": "attachment; filename=netops_experiments_export.json"})


@router.get("/export/csv")
def export_csv():
    """Exports summary CSV table of recorded experiments."""
    csv_path = recorder.summary_csv
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Summary CSV not initialized")
    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=netops_experiments_summary.csv"})
