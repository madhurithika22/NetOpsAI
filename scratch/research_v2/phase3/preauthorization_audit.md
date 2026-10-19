# NetOps Research V2 — Phase 3 Pre-Authorization Consistency Audit Report

**Audit Date (UTC)**: 2026-10-09  
**Execution Environment**: Linux Ubuntu WSL2 (`/mnt/d/NetOpsAI/.venv-linux/bin/python`)  
**Auditor**: Independent Research Engineer & Reproducibility Auditor  
**Audit Scope**: Phase 2 Baseline Freeze Manifest & Phase 3 Experimental Protocol Preparation  

---

## Executive Summary & Final Decision

### Audit Decision: `BLOCKED`

Phase 3 experimental execution is **BLOCKED** from authorization review until the critical discrepancies, missing implementations, environment dependencies, and experiment matrix errors identified in this audit are resolved in documentation and codebase readiness checks.

### Key Audit Findings Summary

| Audit Domain | Sub-Domain / Component | Status | Primary Finding / Discrepancy |
|---|---|---|---|
| **1. Phase 2 Freeze** | Manifest SHA-256 Checksums | `PASS` / `DISCREPANCY` | Disk files match `freeze_manifest.json` checksums; however `freeze_manifest.md` contains outdated SHA-256 values for several files. |
| **1. Phase 2 Freeze** | Git Provenance & Working Tree | `NOT VERIFIABLE` (WSL) | In WSL environment, `git rev-parse HEAD` returns exit code 128 (WSL `/mnt/d` boundary permissions), recording `commit: "unpinned"` in `.json`, whereas native Git records commit `dfa8241b7e28901a8ef1c0e359a4918ef9b4186c` with uncommitted changes. |
| **1. Phase 2 Freeze** | Engine Version & Escalation Predicate | `PASS` (Code) / `DISCREPANCY` (Doc) | Code in `engine.py:154` implements `confidence < 0.70 OR top_candidate == "UNKNOWN_COMPOSITE_ANOMALY"`. Freeze prose mentioned `top score < 0.60`, which is absent from source code. |
| **1. Phase 2 Freeze** | Experiment Records | `PASS` | `exp-phase2-5c538333.json` and `exp-phase2-04052fa5.json` intact and untouched; internal confidence and escalation fields agree with engine calculation. |
| **1. Phase 2 Freeze** | Pytest Validation Capture | `PASS` | `freeze_validation_test_output.txt` captures 29 passed tests in 1.16s, matching `freeze_manifest.md`. |
| **1. Phase 2 Freeze** | Dependency Identity | `FAIL` | `requirements.txt` is missing on disk; `requirements_sha256` is `null` in `.json` while `.md` claimed hash `785d0d88...`. |
| **2. Phase 3 Protocol** | Experiment Matrix Completeness | `FAIL` | Protocol claims a 420-run design ($7 \times 6 \times 10$), but `experiment_matrix.csv` contains only 17 unexpanded rows (missing 25 arm-scenario pairings, missing per-run seeds, missing unique `run_id`s). |
| **2. Phase 3 Protocol** | Local LLM Dependency | `BLOCKED` | Ollama daemon is NOT running (`Connection refused`) and `ollama` CLI is not installed in WSL. `llama3.2:3b` is unavailable. Arms 6 & 7 must be `BLOCKED`. |
| **2. Phase 3 Protocol** | Comparison Arms Implementation | `BLOCKED` | Arm 1 (Static Detector) and Arm 2 (Rolling Stat Detector) are `NOT IMPLEMENTED` in code. Arm 7 (Closed-Loop NetOps) is `BLOCKED` pending Phase 4 hooks. |
| **2. Phase 3 Protocol** | Dataset Scenario Guardrails | `FAIL` | Matrix sets `Remediation_Supported = True` for dataset-only scenarios SCN-04 and SCN-05, violating the rule against dataset metrics contributing to live remediation success. |
| **2. Phase 3 Protocol** | Per-Run Seed Assignment | `BLOCKED` | Protocol lists global `seed = 42` without pre-registering deterministic per-run seed offsets ($42 + \text{run\_index}$), risking duplicate deterministic runs. |

---

## Section 1: Detailed Audit of the Phase 2 Baseline Freeze

### 1.1 Cryptographic SHA-256 Checksums
- **JSON Manifest** ([`scratch/research_v2/phase2/freeze_manifest.json`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase2/freeze_manifest.json)): Evaluated 100% match against actual files on disk right now.
  - `backend/app/cadd/engine.py`: `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326`
  - `exp-phase2-5c538333.json`: `4ae90e2c8d63c81dc6482901b3861500a7d39a6e6c5b879233b90b9c8e1b0cfc`
  - `exp-phase2-04052fa5.json`: `0ec73222fb18b16f08507705909544ebb746dc1487016b69b6bade9bd68832d9`
- **Markdown Documentation** ([`scratch/research_v2/phase2/freeze_manifest.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase2/freeze_manifest.md)): **Discrepancy Detected**. Table in Section 5 of `.md` lists outdated SHA-256 hashes for 18 files (e.g. listed `83516641...` for `engine.py`).
- **Dependency Identity**: `requirements.txt` does NOT exist at project root. In `freeze_manifest.json`, `"requirements_sha256": null`, whereas `freeze_manifest.md` claimed hash `785d0d88efbd7e1d5462cfb37ae1c3a647e30d4a9ec04f86be2e8f15d9186638`.

### 1.2 Git Commit & Working Tree Provenance
- **Native Git**: Commit `dfa8241b7e28901a8ef1c0e359a4918ef9b4186c`. Working tree dirty with uncommitted audit/manifest artifacts.
- **WSL Environment**: Subprocess call `git rev-parse HEAD` returned status code `128` because `/mnt/d/NetOpsAI` crosses filesystem mount boundary. `freeze_manifest.json` accurately recorded `commit: "unpinned"`, `is_dirty: true`, and error message.
- **Finding**: `PASS` for JSON manifest reporting WSL execution reality; `NOT VERIFIABLE` inside WSL without configuring `git config --global --add safe.directory /mnt/d/NetOpsAI`.

### 1.3 Engine Version & Escalation Predicate Investigation
- **Engine Class & Version**: `app.cadd.engine.ExplainableRuleEngine`, `VERSION = "2.0.0-phase2"` ([`backend/app/cadd/engine.py:32`](file:///mnt/d/NetOpsAI/backend/app/cadd/engine.py#L32)).
- **Escalation Implementation**: Line 154 of `backend/app/cadd/engine.py`:
  ```python
  escalation_required = (confidence < self.CONFIDENCE_ESCALATION_THRESHOLD) or (top_candidate == "UNKNOWN_COMPOSITE_ANOMALY")
  ```
  where `CONFIDENCE_ESCALATION_THRESHOLD = 0.70`.
- **Discrepancy Investigation**:
  - Audit text mentioned an escalation condition `confidence < 0.70 OR top score < 0.60`.
  - Code inspection of `engine.py` proves `top score < 0.60` does NOT exist in code logic.
  - The actual predicate is `(confidence < 0.70) OR (top_candidate == "UNKNOWN_COMPOSITE_ANOMALY")`.
  - Historical provenance: Phase 0/1 used static `confidence < 0.70` or hardcoded `0.47` literal for Case 4. Phase 2 updated this to check both low confidence ($< 0.70$) AND `UNKNOWN_COMPOSITE_ANOMALY` candidate selection.
- **Finding**: Source code logic is deterministic and verified; freeze summary text contained a minor phrasing discrepancy (`top score < 0.60` vs `top candidate UNKNOWN_COMPOSITE_ANOMALY`).

### 1.4 Frozen Experiment Records Verification
- **Record 1**: `exp-phase2-5c538333.json`
  - Candidate scores: `HIGH_LATENCY_CONGESTION: 0.7000`, `PACKET_LOSS: 0.3000`, `HEALTHY: 0.0000`.
  - Top candidate: `HIGH_LATENCY_CONGESTION` ($S = 0.7000$), second: `PACKET_LOSS` ($S = 0.3000$).
  - Confidence recomputation: $0.7000 \times (1.0 - 0.5 \times 0.3000) = 0.7000 \times 0.8500 = 0.5950$. Stored in JSON: `0.5950`. Match.
  - Escalation: `confidence < 0.70` ($0.5950 < 0.70$) $\implies$ `escalation_required = True`. Stored in JSON: `True`. Match.
- **Record 2**: `exp-phase2-04052fa5.json`
  - Preserved untouched as historical evidence ($N=5$).
- **Finding**: `PASS`.

### 1.5 Pytest Execution Validation Capture
- `scratch/research_v2/phase2/freeze_validation_test_output.txt` contains 39 lines.
- Execution header: `platform linux -- Python 3.12.15, pytest-9.1.1`.
- Summary: `29 passed in 1.16s`.
- Command run: `pytest tests/unit/test_phase2_*.py tests/unit/test_cadd_*.py tests/unit/test_engine.py`.
- Matching in `freeze_manifest.md`: Section 6 quotes exact text.
- **Finding**: `PASS`.

---

## Section 2: Detailed Audit of the Phase 3 Experimental Protocol

### 2.1 Experiment Matrix Analysis (`experiment_matrix.csv`)
- **Protocol Claim**: 420-run experimental matrix ($7\text{ arms} \times 6\text{ scenarios} \times 10\text{ repetitions}$).
- **Actual File Inspection**: [`scratch/research_v2/phase3/experiment_matrix.csv`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/experiment_matrix.csv) contains only **17 rows**.
- **Defects Identified**:
  1. **Incomplete Cross Product**: Only 17 scenario-arm pairs are listed instead of the full $7 \times 6 = 42$ combinations. Scenarios SCN-02, SCN-03, SCN-04, SCN-05, and SCN-06 omit arms ARM_1, ARM_2, ARM_3, and ARM_5.
  2. **Unexpanded Repetitions**: Repetitions are represented by a single integer column `Repeat_Count = 10` rather than 10 explicit individual run rows.
  3. **Missing Run IDs**: CSV header lacks a `Run_ID` column for pre-registered immutable run identification.
  4. **Dataset Guardrail Violation**: Rows 14 and 16 list `Remediation_Supported = True` for dataset/synthetic scenarios SCN-04 (MTU) and SCN-05 (Composite). Protocol rules mandate that dataset-only scenarios MUST NOT contribute to live remediation metrics (`Remediation_Supported` must be `False`).
  5. **Missing Status Attribute**: CSV lacks execution status fields (`BLOCKED`, `PLANNED`, `READY`) for arms that cannot currently execute.
- **Finding**: `FAIL`.

### 2.2 Seed Assignment & Statistical Control
- **Current State**: `experimental_protocol.md` specifies `random_seed: 42`.
- **Defect**: The protocol does not explicitly declare a per-run seed expansion equation (e.g. $\text{seed}_{i, j, k} = \text{base\_seed} + 1000 \cdot i + 100 \cdot j + k$). Reusing a fixed seed `42` across 10 repetitions of deterministic simulation runs causes identical repeated measurements, destroying statistical independence assumptions.
- **Repetition Rationale**: Repetition count $N=10$ is stated without a formal statistical power calculation or variance expectation bound.
- **Finding**: `BLOCKED`.

### 2.3 Local LLM Dependency Audit
- **WSL Environment Inspection**:
  - `http://localhost:11434/api/tags`: `<urlopen error [Errno 111] Connection refused>`.
  - `ollama list`: `No such file or directory: 'ollama'`.
- **Determination**: Ollama daemon is NOT running and the `ollama` executable is not installed on PATH inside Ubuntu WSL2 environment. Model `llama3.2:3b` is UNAVAILABLE.
- **Enforcement**: Per pre-authorization constraints, no model may be pulled or installed during audit. Arms requiring LLM (ARM_6 and ARM_7) MUST be marked `BLOCKED`.
- **Finding**: `BLOCKED`.

### 2.4 Comparison Arms & Ablation Implementation Status

| Arm ID | Arm Name | Code Implementation Status | Interface Inputs / Outputs | GT Isolated? | Ready Status |
|---|---|---|---|---|---|
| **ARM_1** | Static-Threshold Detector | `NOT IMPLEMENTED` (No static single-metric threshold script exists in repo) | `NetworkState` $\to$ `DiagnosticReport` | Yes | `BLOCKED` |
| **ARM_2** | Rolling-Statistical Detector | `NOT IMPLEMENTED` (No z-score / rolling window detector script exists in repo) | `NetworkState` $\to$ `DiagnosticReport` | Yes | `BLOCKED` |
| **ARM_3** | Rule-Based Diagnosis | `PARTIALLY IMPLEMENTED` (Rule logic exists within `engine.py`) | `NetworkState` $\to$ `DiagnosticReport` | Yes | `READY` |
| **ARM_4** | Frozen Phase 2 Baseline | `IMPLEMENTED` (`ExplainableRuleEngine` v2.0.0-phase2 in `backend/app/cadd/engine.py`) | `NetworkState` $\to$ `DiagnosticReport` | Yes | `READY` |
| **ARM_5** | CESO + CADE (No LLM) | `IMPLEMENTED` (CESO state extraction + CADE engine diagnosis without LLM fallback) | `NetworkState` $\to$ `DiagnosticReport` | Yes | `READY` |
| **ARM_6** | CESO + CADE (With LLM) | `BLOCKED` (Ollama daemon / `llama3.2:3b` unavailable in WSL) | `NetworkState` $\to$ `DiagnosticReport` + LLM prompt/response | Yes | `BLOCKED` |
| **ARM_7** | Full Closed-Loop NetOps | `BLOCKED` (Requires live Mininet testbed, automated remediation hooks, and post-verification cycles) | `NetworkState` $\to$ ActionPlan $\to$ Execution $\to$ Verification | Yes | `BLOCKED` |

- **Finding**: `BLOCKED`.

### 2.5 Metrics & Statistical Validity Audit
- **Metric Specification Document**: [`scratch/research_v2/phase3/metric_specification.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/metric_specification.md) correctly defines formulas for Precision, Recall, Macro-F1, Latency, and Safety Violations (`SEV-1` to `SEV-4`).
- **Missing Data Policy**: Explicitly uses `NOT_MEASURED` for unsupported scenario-metric pairs (e.g. remediation metrics on offline dataset scenarios). Non-silent zero policy is respected.
- **Detection Latency**: Starts at recorded fault injection timestamp $t_{\text{fault\_start}}$.
- **Confidence Calibration Statement**: Protocol explicitly notes that confidence values $C \in [0, 1]$ represent evidence margins, not calibrated Bayesian probabilities.
- **Finding**: `PASS`.

---

## Section 3: Prioritized Action Plan & Required Fixes

To achieve `READY FOR AUTHORIZATION REVIEW` in a future audit, the following documentation and protocol corrections must be applied:

1. **Fix Experiment Matrix CSV (`experiment_matrix.csv`)**:
   - Expand matrix to include all 420 explicit run rows ($7\text{ arms} \times 6\text{ scenarios} \times 10\text{ repetitions}$).
   - Add explicit columns: `Run_ID`, `Base_Seed`, `Effective_Seed`, `Execution_Status`.
   - Set `Remediation_Supported = False` for SCN-04 and SCN-05 across all arms.
   - Mark `Execution_Status = BLOCKED` for ARM_1, ARM_2, ARM_6, and ARM_7.

2. **Pre-Register Per-Run Seed Assignment Formula**:
   - Add deterministic seed formula $\text{seed}(a, s, r) = 42 + 1000 \cdot a + 100 \cdot s + r$ in `experimental_protocol.md`.

3. **Reconcile Phase 2 Freeze Manifest Files**:
   - Update `scratch/research_v2/phase2/freeze_manifest.md` Section 5 table so SHA-256 hashes match the actual disk file hashes recorded in `freeze_manifest.json`.
   - Add explicit footnote explaining that `requirements.txt` is omitted from the repository root (recording `null` in manifest).
   - Document WSL Git safe directory requirement (`git config --global --add safe.directory /mnt/d/NetOpsAI`).

4. **Clarify Escalation Predicate in Freeze Documentation**:
   - Align freeze documentation prose with `backend/app/cadd/engine.py:154` logic: `(confidence < 0.70) OR (top_candidate == "UNKNOWN_COMPOSITE_ANOMALY")`.

---

## Section 4: Final Conclusion & Execution Constraint

- **Final Audit Decision**: **`BLOCKED`**
- **Phase 3 Research Execution Status**: **STRICTLY PROHIBITED / UN-AUTHORIZED**.
- **Report Artifact Paths**:
  - Full Audit Report: [`scratch/research_v2/phase3/preauthorization_audit.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/preauthorization_audit.md)
  - Executive Summary: [`scratch/research_v2/phase3/preauthorization_audit_summary.md`](file:///mnt/d/NetOpsAI/scratch/research_v2/phase3/preauthorization_audit_summary.md)
