import os
import json
import csv
from typing import List, Optional, Dict
from app.evaluation.models import ExperimentRun, EvaluationEnvironment, EvaluationSummary, MetricValue
from app.evaluation.metrics import calculate_evaluation_metrics


class ExperimentRecorder:
    """
    Handles recording, persistence, retrieval, and export of experiment runs.
    Ensures complete data integrity across backend restarts.
    """

    def __init__(self, base_dir: str = "data/experiments"):
        self.base_dir = base_dir
        self.runs_dir = os.path.join(self.base_dir, "runs")
        self.summary_csv = os.path.join(self.base_dir, "summary.csv")
        os.makedirs(self.runs_dir, exist_ok=True)
        self._init_csv()

    def _init_csv(self):
        if not os.path.exists(self.summary_csv):
            headers = [
                "run_id", "timestamp", "environment", "arm_id", "algorithm_version", "dataset_or_scenario_id",
                "ground_truth_fault_label", "predicted_fault_label",
                "ground_truth_location", "predicted_location",
                "diagnosis_latency_ms", "telemetry_collection_latency_ms", "total_elapsed_ms",
                "evidence_count", "total_raw_evidence_count",
                "llm_escalated", "remediation_decision", "remediation_status",
                "verification_result", "is_completed", "error_message"
            ]
            with open(self.summary_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def record_run(self, run: ExperimentRun) -> ExperimentRun:
        """Saves an experiment run to JSON file and appends to CSV summary."""
        json_path = os.path.join(self.runs_dir, f"{run.run_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(run.model_dump_json(indent=2))

        row = [
            run.run_id, run.timestamp, run.environment.value if isinstance(run.environment, EvaluationEnvironment) else str(run.environment),
            run.arm_id or "", run.algorithm_version or "",
            run.dataset_or_scenario_id, run.ground_truth_fault_label, run.predicted_fault_label or "",
            run.ground_truth_location or "", run.predicted_location or "",
            run.diagnosis_latency_ms, run.telemetry_collection_latency_ms, run.total_elapsed_ms,
            run.evidence_count, run.total_raw_evidence_count,
            run.llm_escalated, run.remediation_decision or "", run.remediation_status or "",
            run.verification_result or "", run.is_completed, run.error_message or ""
        ]
        with open(self.summary_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        return run

    def list_runs(self, environment: Optional[EvaluationEnvironment] = None) -> List[ExperimentRun]:
        """Lists all recorded experiment runs, optionally filtered by environment."""
        runs = []
        if not os.path.exists(self.runs_dir):
            return runs

        for fname in sorted(os.listdir(self.runs_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(self.runs_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        run = ExperimentRun(**data)
                        if environment is None or run.environment == environment:
                            runs.append(run)
                except Exception as e:
                    print(f"Error loading run {fname}: {e}")
        return runs

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        """Retrieves a single experiment run by ID."""
        json_path = os.path.join(self.runs_dir, f"{run_id}.json")
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return ExperimentRun(**json.load(f))
        except Exception:
            return None

    def get_summary(self, environment: EvaluationEnvironment) -> EvaluationSummary:
        """Calculates paper evaluation metrics summary for a specific environment group."""
        runs = self.list_runs(environment=environment)
        completed = [r for r in runs if r.is_completed]
        excluded = [r for r in runs if not r.is_completed or r.ground_truth_fault_label in ("UNSUPPORTED_INFRA_FAULT", "UNSUPPORTED_APP_FAULT")]
        
        metrics = calculate_evaluation_metrics(runs, environment)
        
        return EvaluationSummary(
            environment=environment.value,
            total_runs=len(runs),
            completed_runs=len(completed),
            excluded_runs=len(excluded),
            metrics=metrics
        )

    def export_all_json(self) -> str:
        """Returns JSON representation of all runs."""
        runs = self.list_runs()
        return json.dumps([r.model_dump() for r in runs], indent=2)
