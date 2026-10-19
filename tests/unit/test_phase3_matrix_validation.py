import pytest
import os
import csv
from scratch.research_v2.phase3.validate_experiment_matrix import validate_matrix, validate_matrix_v2

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


def test_v2_matrix_exact_seeds_and_arm_names():
    """
    Validates that the 120-row V2 experiment matrix passes all validation rules,
    including exact declared seed equation and arm display names.
    """
    v2_csv = "scratch/research_v2/phase3/experiment_matrix_v2.csv"
    assert os.path.exists(v2_csv), f"V2 Matrix CSV does not exist at {v2_csv}"
    
    success, errors = validate_matrix_v2(v2_csv)
    assert success, f"V2 Matrix validation failed with errors: {errors}"


def test_v2_matrix_detects_incorrect_seed(tmp_path):
    """
    Proves that validate_matrix_v2 detects an incorrect seed that deviates from
    seed = 42 + 1000*a + 100*s + r.
    """
    v2_csv = "scratch/research_v2/phase3/experiment_matrix_v2.csv"
    with open(v2_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Intentionally corrupt the seed of the first row (e.g. legacy seed 3101 instead of 3143)
    rows[0]["seed"] = "3101"

    corrupted_csv = str(tmp_path / "corrupted_seed_matrix.csv")
    with open(corrupted_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    success, errors = validate_matrix_v2(corrupted_csv)
    assert not success, "Validation should have failed for corrupted seed"
    assert any("Seed mismatch" in e for e in errors), f"Expected 'Seed mismatch' error, got: {errors}"


def test_v2_matrix_detects_incorrect_arm4_display_label(tmp_path):
    """
    Proves that validate_matrix_v2 detects an incorrect Arm 4 display label
    (e.g., 'Phase 2 Frozen Baseline' instead of 'Modified Phase 2-Derived Baseline').
    """
    v2_csv = "scratch/research_v2/phase3/experiment_matrix_v2.csv"
    with open(v2_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Corrupt Arm 4's arm_name back to historical "Phase 2 Frozen Baseline"
    arm4_idx = next(i for i, r in enumerate(rows) if r["arm_id"] == "ARM_4_PHASE2_BASELINE")
    rows[arm4_idx]["arm_name"] = "Phase 2 Frozen Baseline"

    corrupted_csv = str(tmp_path / "corrupted_label_matrix.csv")
    with open(corrupted_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    success, errors = validate_matrix_v2(corrupted_csv)
    assert not success, "Validation should have failed for incorrect Arm 4 arm_name"
    assert any("Expected arm_name 'Modified Phase 2-Derived Baseline'" in e for e in errors), f"Expected arm_name error, got: {errors}"

