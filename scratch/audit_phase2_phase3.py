import json
import hashlib
import subprocess
import os
import sys

def hash_file(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def audit_manifest():
    print("=== 1. AUDIT MANIFEST SHA-256 CHECKSUMS ===")
    manifest_path = "scratch/research_v2/phase2/freeze_manifest.json"
    if not os.path.exists(manifest_path):
        print("ERROR: freeze_manifest.json not found")
        return
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    checksums = manifest.get("sha256_checksums", {})
    mismatches = 0
    for file_path, stored_hash in checksums.items():
        actual_hash = hash_file(file_path)
        match = (actual_hash == stored_hash)
        if not match:
            mismatches += 1
            print(f"  [MISMATCH] {file_path}:")
            print(f"     Stored: {stored_hash}")
            print(f"     Actual: {actual_hash}")
        else:
            print(f"  [PASS] {file_path}: {stored_hash[:12]}...")
            
    print(f"Total checksum mismatches: {mismatches}")
    
    print("\n=== 2. GIT COMMIT AND WORKING TREE CHECK ===")
    commit = manifest.get("git_commit", "")
    print(f"Manifest Git commit: {commit}")
    res = subprocess.run(["git", "cat-file", "-e", commit], capture_output=True)
    print(f"Commit exists in git: {res.returncode == 0}")
    
    status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    dirty_files = [line for line in status_res.stdout.splitlines() if line.strip()]
    print(f"Working tree dirty files count: {len(dirty_files)}")
    for df in dirty_files[:10]:
        print(f"  {df}")
    if len(dirty_files) > 10:
        print(f"  ... and {len(dirty_files) - 10} more")
        
    print("\n=== 3. ENGINE VERSION & ESCALATION PREDICATE CHECK ===")
    from backend.app.cadd.engine import ExplainableRuleEngine
    engine = ExplainableRuleEngine()
    print(f"Engine class: {engine.__class__.__name__}")
    print(f"Manifest algorithm version: {manifest.get('diagnostic_algorithm_version')}")
    print(f"Manifest escalation threshold: {manifest.get('escalation_threshold')}")
    
    # Inspect engine.py source code for version string or class attributes
    with open("backend/app/cadd/engine.py", "r", encoding="utf-8") as f:
        engine_src = f.read()
    print("Searching engine.py for thresholds and escalation logic...")
    for line in engine_src.splitlines():
        if "escalat" in line.lower() or "confidence" in line.lower() or "threshold" in line.lower() or "version" in line.lower() or "unknown" in line.lower():
            if len(line.strip()) < 120 and not line.strip().startswith("#"):
                print(f"  engine.py: {line.strip()}")

def audit_experiments():
    print("\n=== 4. FROZEN EXPERIMENT RECORDS CHECK ===")
    exp1_path = "scratch/research_v2/phase2/runs/exp-phase2-5c538333.json"
    exp2_path = "scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json"
    
    for path in [exp1_path, exp2_path]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            print(f"\nRecord: {os.path.basename(path)}")
            print(f"  Experiment ID: {rec.get('experiment_id')}")
            print(f"  Selected Diagnosis: {rec.get('selected_diagnosis')}")
            print(f"  Confidence: {rec.get('confidence')}")
            print(f"  Escalation Decision: {rec.get('escalation_decision')}")
            print(f"  Escalation Target: {rec.get('escalation_target')}")
            print(f"  Candidate Scores: {rec.get('candidate_scores')}")

def audit_test_output_command():
    print("\n=== 5. FREEZE VALIDATION TEST OUTPUT CHECK ===")
    out_path = "scratch/research_v2/phase2/freeze_validation_test_output.txt"
    manifest_md_path = "scratch/research_v2/phase2/freeze_manifest.md"
    
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"freeze_validation_test_output.txt total lines: {len(lines)}")
        print("Header lines in test output:")
        for l in lines[:10]:
            print(f"  {l.strip()}")
        print("Summary lines in test output:")
        for l in lines[-10:]:
            print(f"  {l.strip()}")
            
    if os.path.exists(manifest_md_path):
        with open(manifest_md_path, "r", encoding="utf-8") as f:
            manifest_md = f.read()
        print("\nChecking test command recorded in freeze_manifest.md:")
        for line in manifest_md.splitlines():
            if "pytest" in line or "command" in line.lower():
                print(f"  manifest.md: {line.strip()}")

def audit_ollama():
    print("\n=== 6. OLLAMA LOCAL LLM CHECK ===")
    import urllib.request
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        tags = json.loads(req.read().decode())
        models = [m.get("name") for m in tags.get("models", [])]
        print(f"Ollama daemon running. Installed models: {models}")
        print(f"Is llama3.2:3b available? {'llama3.2:3b' in models or 'llama3.2:3b:latest' in models or any('llama3.2:3b' in m for m in models)}")
    except Exception as e:
        print(f"Ollama API connection failed: {e}")
        
    try:
        res = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if res.returncode == 0:
            print("ollama list output:")
            print(res.stdout)
        else:
            print(f"ollama CLI exited with code {res.returncode}: {res.stderr}")
    except Exception as e:
        print(f"ollama CLI execution error: {e}")

if __name__ == "__main__":
    audit_manifest()
    audit_experiments()
    audit_test_output_command()
    audit_ollama()
