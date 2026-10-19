import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone

def sha256_file(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_git_commit():
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        commit = res.stdout.strip()
        status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        is_dirty = bool(status_res.stdout.strip())
        return {"commit": commit, "is_dirty": is_dirty, "status_summary": "Uncommitted working tree changes present" if is_dirty else "Clean"}
    except Exception as e:
        return {"commit": "unpinned", "is_dirty": True, "error": str(e)}

def build_manifest():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    files_to_hash = [
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
        "scratch/research_v2/phase2/algorithm_spec.md",
        "scratch/research_v2/phase2/independent_record_verification.md",
        "scratch/research_v2/phase2/independent_record_verification_summary.md",
        "scratch/research_v2/phase2/correction_report.md",
        "scratch/research_v2/phase2/final_evidence_check.md",
        "scratch/research_v2/phase2/runs/exp-phase2-5c538333.json",
        "scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json",
        "tests/unit/test_phase2_formula_and_isolation.py",
        "tests/unit/test_phase2_guard.py",
        "requirements.txt"
    ]

    file_hashes = {}
    for rel_path in files_to_hash:
        full_path = os.path.join(project_root, rel_path)
        h = sha256_file(full_path)
        file_hashes[rel_path] = h

    git_info = get_git_commit()
    freeze_ts = datetime.now(timezone.utc).isoformat()

    manifest = {
        "freeze_manifest_version": "1.0.0",
        "freeze_timestamp_utc": freeze_ts,
        "audit_decision": "PASS — PHASE 2 BASELINE FREEZE ELIGIBLE",
        "freeze_scope": "Preserves Phase 2 diagnostic engine (CADE v2.0.0-phase2), feature normalization, heuristic margin confidence calculation, ground-truth isolation, real Linux namespace testbed execution evidence, and validation guards.",
        "git_provenance": git_info,
        "environment_identity": {
            "platform": sys.platform,
            "os_name": os.name,
            "python_executable": sys.executable,
            "python_version": sys.version,
            "requirements_file": "requirements.txt",
            "requirements_sha256": file_hashes.get("requirements.txt")
        },
        "diagnostic_algorithm_configuration": {
            "engine_class": "app.cadd.engine.ExplainableRuleEngine",
            "algorithm_version": "2.0.0-phase2",
            "latency_threshold_ms": 50.0,
            "packet_loss_threshold_pct": 10.0,
            "confidence_escalation_threshold": 0.70,
            "latency_feature_formula": "f_lat = clip((RTT_ms - 50.0) / 50.0, 0, 1)",
            "packet_loss_feature_formula": "f_loss = clip((loss_pct - 10.0) / 30.0, 0, 1)",
            "high_latency_candidate_formula": "S(HIGH_LATENCY_CONGESTION) = 0.7 * f_lat + 0.3 * f_loss",
            "packet_loss_candidate_formula": "S(PACKET_LOSS) = 0.8 * f_loss + 0.2 * f_lat",
            "heuristic_confidence_formula": "C = round(S(best) * (1.0 - 0.5 * S(second)), 4)",
            "tie_breaking_priority": [
                "INTERFACE_FAILURE",
                "ROUTING_MISCONFIGURATION",
                "DC_MTU_MISMATCH",
                "OSPF_ADJACENCY_FLAP",
                "WAN_PATH_DEGRADATION",
                "HIGH_LATENCY_CONGESTION",
                "PACKET_LOSS",
                "UNKNOWN_COMPOSITE_ANOMALY",
                "HEALTHY"
            ]
        },
        "frozen_experiment_records": [
            {
                "experiment_id": "exp-phase2-5c538333",
                "filepath": "scratch/research_v2/phase2/runs/exp-phase2-5c538333.json",
                "sha256": file_hashes.get("scratch/research_v2/phase2/runs/exp-phase2-5c538333.json"),
                "status": "RECOVERED",
                "role": "Primary verified Phase 2 baseline experiment record (N=30/50, tc -s qdisc counters, remediation & recovery)"
            },
            {
                "experiment_id": "exp-phase2-04052fa5",
                "filepath": "scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json",
                "sha256": file_hashes.get("scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json"),
                "status": "DIAGNOSED_PASS",
                "role": "Historical Phase 2 run record (N=5, preserved untouched for historical provenance)"
            }
        ],
        "file_checksums_sha256": file_hashes,
        "known_limitations_and_scope_boundary": [
            "Baseline freeze applies strictly to Phase 2 diagnosis requirements and testbed baseline state.",
            "Confidence scores represent heuristic evidence margins in [0, 1], not calibrated Bayesian posterior probabilities.",
            "Measured empirical evidence is bounded to the Linux network namespace testbed fault class (HIGH_LATENCY_CONGESTION: delay 150ms, loss 20%).",
            "This freeze does NOT establish general diagnostic accuracy across all network fault classes, production readiness, or remediation success beyond measured testbed evidence.",
            "Phase 3 research execution remains blocked until Phase 3 protocol approval."
        ]
    }

    out_json_path = os.path.join(project_root, "scratch/research_v2/phase2/freeze_manifest.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Freeze manifest JSON generated: {out_json_path}")
    return manifest

if __name__ == "__main__":
    build_manifest()
