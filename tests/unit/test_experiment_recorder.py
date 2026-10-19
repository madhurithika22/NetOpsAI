import os
import shutil
import pytest
from app.evaluation.recorder import ExperimentRecorder
from app.evaluation.models import ExperimentRun, EvaluationEnvironment


@pytest.fixture
def temp_recorder(tmp_path):
    test_dir = tmp_path / "experiments"
    recorder = ExperimentRecorder(base_dir=str(test_dir))
    yield recorder


def test_record_and_retrieve_run(temp_recorder):
    run = ExperimentRun(
        run_id="test-run-001",
        timestamp="2026-10-03T12:00:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="HIGH_LATENCY_CONGESTION",
        ground_truth_fault_label="HIGH_LATENCY_CONGESTION",
        predicted_fault_label="HIGH_LATENCY_CONGESTION",
        start_time="2026-10-03T12:00:00Z",
        end_time="2026-10-03T12:00:01Z",
        is_completed=True
    )

    saved = temp_recorder.record_run(run)
    assert saved.run_id == "test-run-001"

    retrieved = temp_recorder.get_run("test-run-001")
    assert retrieved is not None
    assert retrieved.dataset_or_scenario_id == "HIGH_LATENCY_CONGESTION"

    listed = temp_recorder.list_runs(environment=EvaluationEnvironment.SIMULATED)
    assert len(listed) == 1
    assert listed[0].run_id == "test-run-001"


def test_csv_summary_persistence(temp_recorder):
    run = ExperimentRun(
        run_id="test-run-002",
        timestamp="2026-10-03T12:05:00Z",
        environment=EvaluationEnvironment.SIMULATED,
        dataset_or_scenario_id="PACKET_LOSS",
        ground_truth_fault_label="PACKET_LOSS",
        predicted_fault_label="PACKET_LOSS",
        start_time="2026-10-03T12:05:00Z",
        end_time="2026-10-03T12:05:01Z",
        is_completed=True
    )
    temp_recorder.record_run(run)
    assert os.path.exists(temp_recorder.summary_csv)
    with open(temp_recorder.summary_csv, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert "test-run-002" in lines[1]
