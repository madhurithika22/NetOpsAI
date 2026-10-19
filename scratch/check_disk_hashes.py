import hashlib
import subprocess
import os
import json

files = [
    "backend/app/cadd/engine.py",
    "backend/app/cadd/service.py",
    "backend/app/models/cadd_models.py",
    "backend/app/models/ceso_models.py",
    "backend/app/research_v2/guard.py",
    "backend/app/research_v2/testbed/telemetry.py",
    "backend/app/research_v2/testbed/faults.py",
    "backend/app/research_v2/testbed/remediation.py",
    "backend/app/research_v2/testbed/verification.py",
    "backend/app/research_v2/testbed/topology.py",
    "backend/app/research_v2/testbed/models.py",
    "backend/app/research_v2/testbed/executor.py",
    "backend/app/research_v2/testbed/recorder.py",
    "scratch/run_phase2_experiment.py",
    "tests/unit/test_phase2_formula_and_isolation.py",
    "tests/unit/test_phase2_guard.py",
    "scratch/research_v2/phase2/independent_record_verification.md",
    "scratch/research_v2/phase2/final_evidence_check.md",
    "scratch/research_v2/phase2/correction_report.md",
    "scratch/research_v2/phase2/runs/exp-phase2-5c538333.json",
    "scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json",
    "requirements.txt"
]

print("=== ACTUAL DISK HASHES ===")
disk_hashes = {}
for f in files:
    if os.path.exists(f):
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        disk_hashes[f] = h
        print(f"{f}: {h}")
    else:
        print(f"{f}: NOT FOUND")

print("\n=== GIT REVISION AND STATUS ===")
subprocess.run(["git", "config", "--global", "--add", "safe.directory", "/mnt/d/NetOpsAI"], capture_output=True)
res_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
print("git rev-parse HEAD:", res_commit.stdout.strip() if res_commit.returncode == 0 else res_commit.stderr.strip())

res_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
print("git status --porcelain lines:", len(res_status.stdout.splitlines()))
for l in res_status.stdout.splitlines()[:10]:
    print(" ", l)

print("\n=== COMPARISON WITH freeze_manifest.json and freeze_manifest.md ===")
manifest_json = json.load(open("scratch/research_v2/phase2/freeze_manifest.json"))
json_hashes = manifest_json.get("file_checksums_sha256", {})

print("\nJSON vs DISK mismatch analysis:")
for f, h in disk_hashes.items():
    json_h = json_hashes.get(f)
    if json_h != h:
        print(f"  [DISCREPANCY] {f}:")
        print(f"     Disk: {h}")
        print(f"     JSON: {json_h}")
