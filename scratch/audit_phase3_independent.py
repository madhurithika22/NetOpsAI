import csv
import json
import hashlib
import os
import subprocess
import sys

def audit_matrix():
    print("=== 1. INDEPENDENT EXPERIMENT MATRIX AUDIT ===")
    matrix_path = "scratch/research_v2/phase3/experiment_matrix.csv"
    if not os.path.exists(matrix_path):
        print("FAIL: Matrix file missing")
        return False
        
    with open(matrix_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    print(f"Total CSV rows: {len(rows)}")
    
    # Verify 420 rows
    if len(rows) != 420:
        print(f"FAIL: Row count is {len(rows)}, expected 420")
        
    expected_arms = {
        "ARM_1_STATIC_THRESHOLD": 1,
        "ARM_2_ROLLING_STATISTICAL": 2,
        "ARM_3_RULE_BASED": 3,
        "ARM_4_PHASE2_BASELINE": 4,
        "ARM_5_CESO_CADE_NO_LLM": 5,
        "ARM_6_CESO_CADE_OLLAMA_LLM": 6,
        "ARM_7_CLOSED_LOOP_NETOPS": 7
    }
    
    expected_scenarios = {
        "SCN_001_HIGH_LATENCY_CONGESTION": 1,
        "SCN_002_INTERFACE_FAILURE": 2,
        "SCN_003_ROUTING_MISCONFIGURATION": 3,
        "SCN_004_FABRIC_MTU_MISMATCH": 4,
        "SCN_005_COMPOSITE_ANOMALY": 5,
        "SCN_006_BASELINE_HEALTHY": 6
    }
    
    combos = set()
    run_ids = set()
    seeds = set()
    seed_errors = 0
    dataset_remed_errors = 0
    status_counts = {}

    for idx, r in enumerate(rows, start=1):
        arm = r["arm_id"]
        sc = r["scenario_id"]
        rep = int(r["repetition"])
        run_id = r["run_id"]
        base_seed = int(r["base_seed"])
        eff_seed = int(r["effective_seed"])
        status = r["execution_status"]
        remed_supp = (r["remediation_supported"].lower() == "true")
        ds_only = (r["dataset_only"].lower() == "true")

        status_counts[status] = status_counts.get(status, 0) + 1

        # Combo uniqueness
        combo_key = (arm, sc, rep)
        if combo_key in combos:
            print(f"FAIL: Duplicate combination {combo_key} at row {idx}")
        combos.add(combo_key)

        # Run ID check
        if run_id in run_ids:
            print(f"FAIL: Duplicate run_id {run_id} at row {idx}")
        run_ids.add(run_id)

        # Seed formula check: seed(a,s,r) = 42 + 1000*a + 100*s + r
        a_idx = expected_arms.get(arm, 0)
        s_idx = expected_scenarios.get(sc, 0)
        expected_seed = 42 + 1000 * a_idx + 100 * s_idx + rep
        if eff_seed != expected_seed:
            seed_errors += 1
            print(f"FAIL: Seed mismatch at row {idx} ({run_id}): calculated {eff_seed}, expected {expected_seed}")
        seeds.add(eff_seed)

        # Dataset guardrail
        if ds_only and remed_supp:
            dataset_remed_errors += 1
            print(f"FAIL: Dataset-only row {idx} ({run_id}) has remediation_supported=True")

    print(f"Unique Combinations: {len(combos)} / 420")
    print(f"Unique Run IDs: {len(run_ids)} / 420")
    print(f"Unique Effective Seeds: {len(seeds)} / 420")
    print(f"Seed Formula Errors: {seed_errors}")
    print(f"Dataset-Only Remediation Violations: {dataset_remed_errors}")
    print("Status Breakdown:")
    for st, count in sorted(status_counts.items()):
        print(f"  {st}: {count}")


def audit_phase2_records_and_confidence():
    print("\n=== 2. PHASE 2 EXPERIMENT RECORDS & CONFIDENCE DISCREPANCY INVESTIGATION ===")
    
    rec1_path = "scratch/research_v2/phase2/runs/exp-phase2-5c538333.json"
    rec2_path = "scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json"
    
    with open(rec1_path, "r", encoding="utf-8") as f:
        rec1 = json.load(f)
    with open(rec2_path, "r", encoding="utf-8") as f:
        rec2 = json.load(f)
        
    print(f"\nRecord 1: {os.path.basename(rec1_path)}")
    print(f"  Top-level keys: {list(rec1.keys())}")
    
    # Search for diagnosis and confidence in rec1
    diag1 = rec1.get("diagnosis_record", {}) or rec1.get("cadd_diagnosis", {}) or rec1
    print("  Diagnosis Record Keys:", list(diag1.keys()) if isinstance(diag1, dict) else type(diag1))
    print("  exp-phase2-5c538333 diagnosis:", rec1.get("selected_diagnosis") or diag1.get("selected_diagnosis") or rec1.get("diagnosis"))
    print("  exp-phase2-5c538333 confidence:", rec1.get("confidence") or diag1.get("confidence") or diag1.get("confidence_score") or rec1.get("confidence_score"))
    print("  exp-phase2-5c538333 candidate_scores:", diag1.get("candidate_scores"))
    
    print(f"\nRecord 2: {os.path.basename(rec2_path)}")
    print(f"  Top-level keys: {list(rec2.keys())}")
    diag2 = rec2.get("diagnosis_record", {}) or rec2.get("cadd_diagnosis", {}) or rec2
    print("  exp-phase2-04052fa5 diagnosis:", rec2.get("selected_diagnosis") or diag2.get("selected_diagnosis") or rec2.get("diagnosis"))
    print("  exp-phase2-04052fa5 confidence:", rec2.get("confidence") or diag2.get("confidence") or diag2.get("confidence_score") or rec2.get("confidence_score"))
    print("  exp-phase2-04052fa5 candidate_scores:", diag2.get("candidate_scores"))

    # Search for "0.78" in all phase2 markdown reports to locate historical source of 0.78 vs 0.5950
    print("\n--- Investigating Provenance of 0.78 vs 0.5950 ---")
    p2_dir = "scratch/research_v2/phase2"
    for fname in os.listdir(p2_dir):
        fpath = os.path.join(p2_dir, fname)
        if os.path.isfile(fpath):
            content = open(fpath, "r", encoding="utf-8", errors="ignore").read()
            if "0.78" in content or "0.5950" in content:
                print(f"Found occurrence in {fname}:")
                for line in content.splitlines():
                    if "0.78" in line or "0.5950" in line or "0.8" in line:
                        if len(line.strip()) < 140:
                            print(f"  {fname}: {line.strip()}")

def audit_manifest_checksums():
    print("\n=== 3. MANIFEST & DISK CHECKSUM COMPARISON ===")
    json_manifest_path = "scratch/research_v2/phase2/freeze_manifest.json"
    md_manifest_path = "scratch/research_v2/phase2/freeze_manifest.md"
    
    with open(json_manifest_path, "r", encoding="utf-8") as f:
        jm = json.load(f)
        
    json_checksums = jm.get("file_checksums_sha256", {})
    
    print("Hashing disk files and comparing to freeze_manifest.json...")
    mismatches = 0
    for relpath, stored_sha in json_checksums.items():
        if os.path.exists(relpath):
            disk_sha = hashlib.sha256(open(relpath, "rb").read()).hexdigest()
            if disk_sha != stored_sha:
                mismatches += 1
                print(f"  MISMATCH {relpath}: disk={disk_sha} json={stored_sha}")
        else:
            if stored_sha is not None:
                mismatches += 1
                print(f"  MISSING FILE {relpath}: stored={stored_sha}")
            else:
                print(f"  OMITTED FILE {relpath}: stored=null (correct)")
                
    print(f"Total disk vs JSON manifest mismatches: {mismatches}")
    
    print("\nChecking freeze_manifest.md table hashes vs disk...")
    with open(md_manifest_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    md_mismatches = 0
    for line in md_text.splitlines():
        if "|" in line and "`" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                file_code = parts[1].replace("`", "").strip()
                hash_code = parts[3].replace("`", "").strip()
                if os.path.exists(file_code):
                    actual_sha = hashlib.sha256(open(file_code, "rb").read()).hexdigest()
                    if hash_code != actual_sha and len(hash_code) == 64:
                        md_mismatches += 1
                        print(f"  MD TABLE MISMATCH {file_code}: md={hash_code} actual={actual_sha}")
    print(f"Total MD table vs disk mismatches: {md_mismatches}")

if __name__ == "__main__":
    audit_matrix()
    audit_phase2_records_and_confidence()
    audit_manifest_checksums()
