import csv
import os
import re

def audit_matrix():
    print("=== AUDITING EXPERIMENT MATRIX CSV ===")
    csv_path = "scratch/research_v2/phase3/experiment_matrix.csv"
    if not os.path.exists(csv_path):
        print("ERROR: experiment_matrix.csv not found")
        return
        
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    print(f"Total CSV rows: {len(reader)}")
    if not reader:
        return
        
    print(f"Headers: {list(reader[0].keys())}")
    
    arms = set(r.get("arm_id") or r.get("arm") for r in reader)
    scenarios = set(r.get("scenario_id") or r.get("scenario") for r in reader)
    seeds = set(r.get("random_seed") or r.get("seed") for r in reader)
    statuses = set(r.get("status") or r.get("execution_status") for r in reader)
    run_ids = [r.get("run_id") for r in reader]
    
    print(f"Unique Arms ({len(arms)}): {sorted([a for a in arms if a])}")
    print(f"Unique Scenarios ({len(scenarios)}): {sorted([s for s in scenarios if s])}")
    print(f"Unique Seeds ({len(seeds)}): {sorted([s for s in seeds if s])}")
    print(f"Unique Statuses ({len(statuses)}): {sorted([st for st in statuses if st])}")
    print(f"Total Run IDs: {len(run_ids)}, Unique Run IDs: {len(set(run_ids))}")
    
    # Check arm status breakdown
    arm_status = {}
    for r in reader:
        arm = r.get("arm_id") or r.get("arm")
        st = r.get("status") or r.get("execution_status")
        arm_status.setdefault(arm, set()).add(st)
    print("\nArm Status Breakdown:")
    for arm, sts in sorted(arm_status.items()):
        print(f"  {arm}: {sts}")

def audit_protocol_docs():
    print("\n=== AUDITING PROTOCOL MARKDOWN DOCUMENTS ===")
    docs = [
        "scratch/research_v2/phase3/experimental_protocol.md",
        "scratch/research_v2/phase3/metric_specification.md",
        "scratch/research_v2/phase3/phase3_readiness_checklist.md"
    ]
    for d in docs:
        if os.path.exists(d):
            print(f"\nDocument: {d} (Size: {os.path.getsize(d)} bytes)")
            with open(d, "r", encoding="utf-8") as f:
                content = f.read()
            # Search for key terms
            print("  Contains Ollama/llama3.2 reference:", "llama3.2" in content or "ollama" in content.lower())
            print("  Contains Ground Truth Isolation section:", "ground-truth" in content.lower() or "isolation" in content.lower())
            print("  Contains Missing Data / NOT_MEASURED policy:", "NOT_MEASURED" in content or "missing" in content.lower())
            print("  Contains Safety Violations taxonomy:", "SEV-1" in content or "safety" in content.lower())

if __name__ == "__main__":
    audit_matrix()
    audit_protocol_docs()
