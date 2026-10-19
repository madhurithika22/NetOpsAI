# NetOps Research V2 — Phase 3 Pre-Authorization Audit Summary

## Executive Summary

- **Audit Decision**: **`BLOCKED`**
- **Date**: 2026-10-09 (UTC)
- **Execution Environment**: Linux Ubuntu WSL2 (`/mnt/d/NetOpsAI/.venv-linux/bin/python`)
- **Primary Report Path**: [`scratch/research_v2/phase3/preauthorization_audit.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/preauthorization_audit.md)
- **Summary Report Path**: [`scratch/research_v2/phase3/preauthorization_audit_summary.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/preauthorization_audit_summary.md)

---

## Key Findings by Category

### Category 1: Phase 2 Baseline Freeze Audit

1. **SHA-256 Checksums (`PASS` for JSON / `DISCREPANCY` for MD)**:
   - All actual files on disk match the SHA-256 hashes recorded in [`scratch/research_v2/phase2/freeze_manifest.json`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase2/freeze_manifest.json).
   - Markdown summary table in [`freeze_manifest.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase2/freeze_manifest.md) contains outdated SHA-256 hashes for 18 files.
   - `requirements.txt` does not exist on disk; recorded as `null` in `.json`.

2. **Git Provenance (`NOT VERIFIABLE` in WSL)**:
   - Native Git records commit `dfa8241b7e28901a8ef1c0e359a4918ef9b4186c` with uncommitted changes.
   - WSL Git fails with exit code 128 due to `/mnt/d` filesystem mount permissions, recording `commit: "unpinned"` in `.json`.

3. **Engine Version & Escalation Predicate (`PASS` for Code / `DISCREPANCY` for Doc)**:
   - Code in `backend/app/cadd/engine.py:154` implements `(confidence < 0.70) OR (top_candidate == "UNKNOWN_COMPOSITE_ANOMALY")`.
   - Phrase `top score < 0.60` in audit text is a documentation summary artifact and does not exist in source code.

4. **Experiment Records & Pytest Output (`PASS`)**:
   - Historical experiment records `exp-phase2-5c538333.json` and `exp-phase2-04052fa5.json` remain untouched and intact.
   - Pytest output in `freeze_validation_test_output.txt` accurately records 29 passed unit tests in 1.16s.

---

### Category 2: Phase 3 Protocol Preparation Audit

1. **Experiment Matrix Structure (`FAIL`)**:
   - `experiment_matrix.csv` contains only 17 unexpanded rows instead of the pre-registered 420-run design ($7 \times 6 \times 10$).
   - 25 scenario-arm pairings, per-run seeds, and explicit `Run_ID`s are missing.
   - Dataset-only scenarios SCN-04 and SCN-05 incorrectly set `Remediation_Supported = True` for Arm 7.

2. **Local LLM Availability (`BLOCKED`)**:
   - Ollama daemon is NOT running (`Connection refused`) and `ollama` CLI is missing in WSL. Model `llama3.2:3b` is unavailable.
   - Arm 6 and Arm 7 are marked `BLOCKED`.

3. **Comparison Arms Implementation (`BLOCKED`)**:
   - Arm 1 (Static Detector) and Arm 2 (Rolling Stat Detector) are `NOT IMPLEMENTED` in code.
   - Arm 7 (Closed-Loop NetOps) is `BLOCKED` pending Phase 4 remediation hooks.
   - Arms 3, 4, and 5 are `READY`.

4. **Seed & Repetition Control (`BLOCKED`)**:
   - Protocol specifies global `seed = 42` without a per-run seed expansion equation, risking non-independent repeated runs.

5. **Metrics & Statistical Validity (`PASS`)**:
   - Formulas for F1, Latency, Safety Violations (`SEV-1`..`SEV-4`), missing data policy (`NOT_MEASURED`), and non-calibrated confidence semantics are verified.

---

## Audit Decision & Next Steps

### Decision: `BLOCKED`

Phase 3 research runs remain **strictly unauthorized**. Authorization review requires resolving the prioritized fixes documented in [`scratch/research_v2/phase3/preauthorization_audit.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/preauthorization_audit.md).
