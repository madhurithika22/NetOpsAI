# Recovered Phase 2 Baseline Engine Archive

## Overview

This directory preserves the historical source code of the original frozen Phase 2 NetOps CADE diagnostic engine (`app.cadd.engine.ExplainableRuleEngine` v2.0.0-phase2).

- **Archived Source File**: [`engine_phase2_frozen_recovered.py`](file:///d:/NetOpsAI/research/archive/phase2_baseline_recovered/engine_phase2_frozen_recovered.py)
- **Role**: Historical research reproducibility artifact (strictly archived; NOT a runtime implementation).

---

## Cryptographic Verification & Hash Audit

| Metric / Parameter | Value |
|---|---|
| **Freeze Manifest Target Path** | `backend/app/cadd/engine.py` |
| **Freeze Manifest Reference** | [`scratch/research_v2/phase2/freeze_manifest.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/freeze_manifest.json) |
| **Freeze Timestamp (UTC)** | `2026-10-09T07:23:57.280899+00:00` |
| **Expected Freeze Manifest SHA-256** | `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326` |
| **Archived Source File SHA-256** | `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326` |
| **Exact Hash Match Status** | **`YES` (Exact 100% Bit-for-Bit Match)** |
| **Exact Source Byte Length** | **`20,498 bytes`** |
| **Source Line Count** | **`433 lines`** (LF line endings, UTF-8 encoding) |

---

## Recovery Provenance & Extraction Methodology

### 1. Recovery Source
The source bytes were recovered from the local IDE interaction transcript log:
- **Location**: `C:/Users/Ln/.gemini/antigravity-ide/brain/c4dbdd2b-06db-4867-9dca-2f0a3c1723a2/.system_generated/logs/transcript_full.jsonl`
- **Step Index**: `step 20`
- **Timestamp (UTC)**: `2026-10-09T05:44:00Z` (`11:14:00+05:30` local)
- **Recorded Operation**: Verbatim `view_file` response on `file:///d:/NetOpsAI/backend/app/cadd/engine.py` recorded immediately prior to execution of `scratch/build_freeze_manifest.py` at `07:23:57Z`.

### 2. Extraction Protocol
- Parsed the 433 lines displayed by the `view_file` tool call.
- Stripped the `<line_number>: ` line prefix while preserving all internal indentation and code formatting.
- Re-joined lines with standard Unix LF (`\n`) newlines. Because line 433 is an empty trailing line (`""`), this preserves the final newline following line 432 (`...return None\n`).
- The reconstructed byte stream was written in binary mode directly to disk and independently re-hashed. No auto-formatting, refactoring, or whitespace normalization was applied.

### 3. Provenance Limitations
- **Incomplete SCM Tracking**: At the time of the Phase 2 freeze, the workspace was not tracked by an active Git repository. The freeze manifest recorded `git_provenance.commit: "unpinned"` (exit status 128).
- **Unverified Commit Hash**: The commit SHA `dfa8241b7e28901a8ef1c0e359a4918ef9b4186c` referenced in narrative markdown (`freeze_manifest.md`) is an unverified reference that cannot be resolved in any Git object database.
- **Transcript Custody**: The source was recovered from an internal IDE agent session transcript rather than a cryptographically signed Git commit, tag, or external release archive.

---

## Operational Constraints & Usage Boundary

> [!CAUTION]
> **DO NOT IMPORT OR EXECUTE AS RUNTIME ENGINE**
>
> 1. This file is preserved strictly for **historical research reproducibility and baseline auditing**.
> 2. It **must not** be imported by the application runtime or substituted for the current operational engine [`backend/app/cadd/engine.py`](file:///d:/NetOpsAI/backend/app/cadd/engine.py).
> 3. Any future transition or substitution of the runtime engine requires a separately documented, reviewed, and approved engineering change proposal.

---

## Relationship to Current Runtime Implementation

- **Current Runtime File**: [`backend/app/cadd/engine.py`](file:///d:/NetOpsAI/backend/app/cadd/engine.py)
- **Current Runtime File SHA-256**: `97227c88ee345b53474d11491912f3c960e2a2414f5059f7bf02d4a4c050bad8` (29,116 bytes, 477 lines)
- **Divergence Summary**:
  The current runtime implementation is a **Modified Phase 2-Derived Engine**:
  1. Contains the operational implementation for **Arm 3** (`diagnose_rule_based()`, 162 lines, `RULE_BASED_VERSION = "1.0.0-arm3-rule-based"`).
  2. Implements route-misconfiguration filtering in `diagnose_state()` exempting connected LAN subnet routes (`r.destination != "10.0.1.0/24"`).
  3. Implements hardcoded interface-failure candidate scoring (`round(1.0 if down_ifaces else 0.0, 4)`).
  4. Keeps the diagnostic evidence chain empty (`pass`) for healthy states.
