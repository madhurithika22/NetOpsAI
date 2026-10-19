import csv
import os
import sys

def validate_matrix(csv_path="scratch/research_v2/phase3/experiment_matrix.csv"):
    if not os.path.exists(csv_path):
        print(f"FAIL: Matrix file missing at {csv_path}")
        return False, ["Matrix file missing"]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    errors = []
    
    # 1. Row count check
    if len(reader) != 420:
        errors.append(f"Expected exactly 420 planned rows, found {len(reader)}")

    # 2. Field check
    required_fields = [
        "run_id", "arm_id", "scenario_id", "repetition",
        "base_seed", "effective_seed", "execution_status",
        "remediation_supported", "dataset_only", "exclusion_reason"
    ]
    if reader and not all(f in reader[0] for f in required_fields):
        errors.append(f"Missing required header fields. Expected: {required_fields}")

    seen_run_ids = set()
    seen_seeds = set()
    valid_arms = {
        "ARM_1_STATIC_THRESHOLD", "ARM_2_ROLLING_STATISTICAL",
        "ARM_3_RULE_BASED", "ARM_4_PHASE2_BASELINE",
        "ARM_5_CESO_CADE_NO_LLM", "ARM_6_CESO_CADE_OLLAMA_LLM",
        "ARM_7_CLOSED_LOOP_NETOPS"
    }
    valid_scenarios = {
        "SCN_001_HIGH_LATENCY_CONGESTION", "SCN_002_INTERFACE_FAILURE",
        "SCN_003_ROUTING_MISCONFIGURATION", "SCN_004_FABRIC_MTU_MISMATCH",
        "SCN_005_COMPOSITE_ANOMALY", "SCN_006_BASELINE_HEALTHY"
    }
    unimplemented_or_blocked_arms = {
        "ARM_1_STATIC_THRESHOLD", "ARM_2_ROLLING_STATISTICAL",
        "ARM_6_CESO_CADE_OLLAMA_LLM", "ARM_7_CLOSED_LOOP_NETOPS"
    }

    for idx, row in enumerate(reader, start=1):
        run_id = row.get("run_id")
        arm_id = row.get("arm_id")
        scenario_id = row.get("scenario_id")
        rep = row.get("repetition")
        eff_seed = row.get("effective_seed")
        status = row.get("execution_status")
        remed_supp = row.get("remediation_supported", "").lower() in ("true", "1")
        dataset_only = row.get("dataset_only", "").lower() in ("true", "1")

        if not run_id or run_id in seen_run_ids:
            errors.append(f"Row {idx}: Duplicate or missing run_id '{run_id}'")
        seen_run_ids.add(run_id)

        if not eff_seed or eff_seed in seen_seeds:
            errors.append(f"Row {idx}: Duplicate or missing effective_seed '{eff_seed}'")
        seen_seeds.add(eff_seed)

        if arm_id not in valid_arms:
            errors.append(f"Row {idx}: Invalid arm_id '{arm_id}'")
        if scenario_id not in valid_scenarios:
            errors.append(f"Row {idx}: Invalid scenario_id '{scenario_id}'")

        if dataset_only and remed_supp:
            errors.append(f"Row {idx} ({run_id}): Dataset-only scenario '{scenario_id}' cannot claim remediation_supported=True")

        if arm_id in unimplemented_or_blocked_arms and status in ("PLANNED_READY", "READY", "COMPLETED"):
            errors.append(f"Row {idx} ({run_id}): Blocked/Unimplemented arm '{arm_id}' cannot be marked '{status}'")

        if status in ("COMPLETED", "EXECUTED", "DONE"):
            errors.append(f"Row {idx} ({run_id}): Row claims completed research execution '{status}'")

    success = len(errors) == 0
    return success, errors

def validate_matrix_v2(csv_path="scratch/research_v2/phase3/experiment_matrix_v2.csv"):
    """
    Validates the revised Phase 3 primary experiment matrix (120 rows).
    Includes Arms 3, 4, 5 and retained scenarios CASE_01, CASE_02, CASE_03, CASE_04.
    """
    if not os.path.exists(csv_path):
        print(f"FAIL: V2 Matrix file missing at {csv_path}")
        return False, ["V2 Matrix file missing"]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    errors = []
    
    if len(reader) != 120:
        errors.append(f"Expected exactly 120 planned rows in V2 matrix, found {len(reader)}")

    required_fields = ["run_id", "arm_id", "scenario_id", "repetition", "seed", "dataset_only", "remediation_supported", "execution_status"]
    if reader and not all(f in reader[0] for f in required_fields):
        errors.append(f"Missing required header fields in V2 matrix. Expected: {required_fields}")

    seen_run_ids = set()
    seen_seeds = set()
    valid_arms = {"ARM_3_RULE_BASED", "ARM_4_PHASE2_BASELINE", "ARM_5_CESO_CADE_NO_LLM"}
    valid_scenarios = {"CASE_01", "CASE_02", "CASE_03", "CASE_04"}

    for idx, row in enumerate(reader, start=1):
        run_id = row.get("run_id")
        arm_id = row.get("arm_id")
        scenario_id = row.get("scenario_id")
        seed = row.get("seed")
        status = row.get("execution_status")
        remed_supp = row.get("remediation_supported", "").lower() in ("true", "1")
        dataset_only = row.get("dataset_only", "").lower() in ("true", "1")

        if not run_id or run_id in seen_run_ids:
            errors.append(f"V2 Row {idx}: Duplicate or missing run_id '{run_id}'")
        seen_run_ids.add(run_id)

        if not seed or seed in seen_seeds:
            errors.append(f"V2 Row {idx}: Duplicate or missing seed '{seed}'")
        seen_seeds.add(seed)

        if arm_id not in valid_arms:
            errors.append(f"V2 Row {idx}: Invalid primary arm_id '{arm_id}'")
        if scenario_id not in valid_scenarios:
            errors.append(f"V2 Row {idx}: Invalid retained scenario_id '{scenario_id}'")

        if dataset_only and remed_supp:
            errors.append(f"V2 Row {idx} ({run_id}): Dataset-only scenario '{scenario_id}' cannot claim remediation_supported=True")

        if status != "PLANNED_NOT_EXECUTED":
            errors.append(f"V2 Row {idx} ({run_id}): Expected status 'PLANNED_NOT_EXECUTED', got '{status}'")

    success = len(errors) == 0
    if success:
        print("PASS: V2 Matrix validation passed with zero errors.")
        print(f"Verified {len(reader)} rows, {len(seen_run_ids)} unique run_ids, {len(seen_seeds)} unique seeds.")
    else:
        print(f"FAIL: V2 Matrix validation found {len(errors)} errors:")
        for err in errors[:10]:
            print(f"  - {err}")

    return success, errors

if __name__ == "__main__":
    ok, _ = validate_matrix_v2()
    sys.exit(0 if ok else 1)
