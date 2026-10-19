import pytest
from app.research_v2.guard import Phase2ResearchValidator, Phase2ResearchViolationError

def test_phase2_validator_linux_check():
    valid_record = {
        "experiment_id": "exp-phase2-12345678",
        "run_id": "run-87654321",
        "system_info": {"platform": "linux"},
        "topology_definition": {"topology_id": "netops-linux-testbed"},
        "diagnosis_record": {
            "algorithm_version": "2.0.0-phase2",
            "algorithm_config": {"latency_threshold_ms": 50.0},
            "candidate_scores": {"HIGH_LATENCY_CONGESTION": 0.8},
            "confidence_score": 0.8
        },
        "raw_command_history": [{"command": "ping -c 5 10.0.3.10", "stdout": "5 received", "return_code": 0}]
    }
    assert Phase2ResearchValidator.validate_record(valid_record) is True

    # Windows platform rejection
    win_record = dict(valid_record)
    win_record["system_info"] = {"platform": "win32"}
    with pytest.raises(Phase2ResearchViolationError, match="not Linux"):
        Phase2ResearchValidator.validate_record(win_record)


def test_phase2_validator_unit_test_rejection():
    test_record = {
        "experiment_id": "exp-unit-test-123",
        "run_id": "run-test-456",
        "system_info": {"platform": "linux"},
        "topology_definition": {"topology_id": "netops-linux-testbed"},
        "diagnosis_record": {
            "algorithm_version": "2.0.0-phase2",
            "algorithm_config": {"latency_threshold_ms": 50.0},
            "candidate_scores": {"HIGH_LATENCY_CONGESTION": 0.8},
            "confidence_score": 0.8
        },
        "raw_command_history": [{"command": "ping", "stdout": "ok", "return_code": 0}]
    }
    with pytest.raises(Phase2ResearchViolationError, match="originates from a test/fixture"):
        Phase2ResearchValidator.validate_record(test_record)


def test_phase2_validator_ground_truth_leakage_rejection():
    leak_record = {
        "experiment_id": "exp-phase2-99999999",
        "run_id": "run-99999999",
        "system_info": {"platform": "linux"},
        "topology_definition": {"topology_id": "CASE_01"},  # LEAK!
        "diagnosis_record": {
            "algorithm_version": "2.0.0-phase2",
            "algorithm_config": {"latency_threshold_ms": 50.0},
            "candidate_scores": {"OSPF_ADJACENCY_FLAP": 0.9},
            "confidence_score": 0.9
        },
        "raw_command_history": [{"command": "ping", "stdout": "ok", "return_code": 0}]
    }
    with pytest.raises(Phase2ResearchViolationError, match="answer-leaking topology ID"):
        Phase2ResearchValidator.validate_record(leak_record)


def test_phase2_validator_missing_raw_evidence_rejection():
    no_raw_record = {
        "experiment_id": "exp-phase2-77777777",
        "run_id": "run-77777777",
        "system_info": {"platform": "linux"},
        "topology_definition": {"topology_id": "netops-linux-testbed"},
        "diagnosis_record": {
            "algorithm_version": "2.0.0-phase2",
            "algorithm_config": {"latency_threshold_ms": 50.0},
            "candidate_scores": {"HIGH_LATENCY_CONGESTION": 0.8},
            "confidence_score": 0.8
        },
        "raw_command_history": []  # Missing raw command history!
    }
    with pytest.raises(Phase2ResearchViolationError, match="Raw execution command evidence history is missing"):
        Phase2ResearchValidator.validate_record(no_raw_record)
