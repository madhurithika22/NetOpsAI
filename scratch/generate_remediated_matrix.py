import csv
import os

def generate_matrix():
    arms = [
        {"id": "ARM_1_STATIC_THRESHOLD", "index": 1, "status": "NOT_IMPLEMENTED", "reason": "STATIC_DETECTOR_CODE_NOT_IMPLEMENTED"},
        {"id": "ARM_2_ROLLING_STATISTICAL", "index": 2, "status": "NOT_IMPLEMENTED", "reason": "ROLLING_STAT_DETECTOR_CODE_NOT_IMPLEMENTED"},
        {"id": "ARM_3_RULE_BASED", "index": 3, "status": "PLANNED_READY", "reason": "NONE"},
        {"id": "ARM_4_PHASE2_BASELINE", "index": 4, "status": "PLANNED_READY", "reason": "NONE"},
        {"id": "ARM_5_CESO_CADE_NO_LLM", "index": 5, "status": "PLANNED_READY", "reason": "NONE"},
        {"id": "ARM_6_CESO_CADE_OLLAMA_LLM", "index": 6, "status": "BLOCKED_OLLAMA_UNAVAILABLE", "reason": "OLLAMA_SERVICE_UNAVAILABLE_IN_WSL"},
        {"id": "ARM_7_CLOSED_LOOP_NETOPS", "index": 7, "status": "BLOCKED_PHASE4_HOOKS_PENDING", "reason": "LIVE_REMEDIATION_HOOKS_UNIMPLEMENTED"},
    ]

    scenarios = [
        {"id": "SCN_001_HIGH_LATENCY_CONGESTION", "index": 1, "dataset_only": False, "live_remed_supported": True},
        {"id": "SCN_002_INTERFACE_FAILURE", "index": 2, "dataset_only": False, "live_remed_supported": True},
        {"id": "SCN_003_ROUTING_MISCONFIGURATION", "index": 3, "dataset_only": False, "live_remed_supported": True},
        {"id": "SCN_004_FABRIC_MTU_MISMATCH", "index": 4, "dataset_only": True, "live_remed_supported": False},
        {"id": "SCN_005_COMPOSITE_ANOMALY", "index": 5, "dataset_only": True, "live_remed_supported": False},
        {"id": "SCN_006_BASELINE_HEALTHY", "index": 6, "dataset_only": False, "live_remed_supported": False},
    ]

    base_seed = 42
    rows = []

    for arm in arms:
        a_idx = arm["index"]
        arm_id = arm["id"]
        status = arm["status"]
        reason = arm["reason"]

        for sc in scenarios:
            s_idx = sc["index"]
            sc_id = sc["id"]
            is_dataset_only = sc["dataset_only"]
            
            # Remediation is supported ONLY IF it is an arm that does closed-loop remediation (ARM_7)
            # AND the scenario supports live remediation AND is NOT dataset_only.
            remediation_supported = (arm_id == "ARM_7_CLOSED_LOOP_NETOPS" and sc["live_remed_supported"] and not is_dataset_only)

            for r in range(1, 11):
                run_id = f"RUN-A{a_idx}-S{s_idx:02d}-R{r:02d}"
                effective_seed = base_seed + 1000 * a_idx + 100 * s_idx + r
                
                rows.append({
                    "run_id": run_id,
                    "arm_id": arm_id,
                    "scenario_id": sc_id,
                    "repetition": r,
                    "base_seed": base_seed,
                    "effective_seed": effective_seed,
                    "execution_status": status,
                    "remediation_supported": remediation_supported,
                    "dataset_only": is_dataset_only,
                    "exclusion_reason": reason
                })

    target_path = "scratch/research_v2/phase3/experiment_matrix.csv"
    headers = [
        "run_id", "arm_id", "scenario_id", "repetition",
        "base_seed", "effective_seed", "execution_status",
        "remediation_supported", "dataset_only", "exclusion_reason"
    ]

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully wrote {len(rows)} planned rows to {target_path}")

if __name__ == "__main__":
    generate_matrix()
