import pytest
import os
import csv
from scratch.research_v2.phase3.validate_experiment_matrix import validate_matrix

def test_experiment_matrix_structure_and_constraints():
    """
    Automated pytest validation for Phase 3 experiment_matrix.csv.
    Verifies 420 planned rows, unique run IDs, seed uniqueness, dataset guardrails,
    and blocked/unimplemented arm status flags.
    """
    csv_path = "scratch/research_v2/phase3/experiment_matrix.csv"
    assert os.path.exists(csv_path), f"Matrix CSV file does not exist at {csv_path}"
    
    success, errors = validate_matrix(csv_path)
    assert success, f"Matrix validation failed with errors: {errors[:5]}"

def test_experiment_matrix_exact_counts():
    """
    Verifies that the CSV contains exactly 420 planned rows, 7 arms, 6 scenarios, and 10 repetitions per pairing.
    """
    csv_path = "scratch/research_v2/phase3/experiment_matrix.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    assert len(reader) == 420, f"Expected 420 rows, got {len(reader)}"
    
    arms = set(r["arm_id"] for r in reader)
    scenarios = set(r["scenario_id"] for r in reader)
    assert len(arms) == 7, f"Expected 7 distinct arms, got {len(arms)}"
    assert len(scenarios) == 6, f"Expected 6 distinct scenarios, got {len(scenarios)}"
    
    # Check that each (arm, scenario) pair has exactly 10 repetitions
    pair_counts = {}
    for r in reader:
        key = (r["arm_id"], r["scenario_id"])
        pair_counts[key] = pair_counts.get(key, 0) + 1
        
    assert len(pair_counts) == 42, f"Expected 42 arm-scenario pairs, got {len(pair_counts)}"
    for key, count in pair_counts.items():
        assert count == 10, f"Pair {key} expected 10 repetitions, got {count}"
