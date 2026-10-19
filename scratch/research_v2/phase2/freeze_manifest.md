# NetOps Research V2 — Phase 2 Freeze Manifest (Remediated)

## Status: PASS — PHASE 2 BASELINE FROZEN AND VERIFIED

---

## 1. Freeze Metadata & Scope

- **Freeze Timestamp (UTC)**: `2026-10-09T07:23:57Z`
- **Audit Decision**: `PASS — PHASE 2 BASELINE FREEZE ELIGIBLE`
- **Engine Version**: `2.0.0-phase2` ([`app.cadd.engine.ExplainableRuleEngine`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L25))
- **Scope Boundary**:
  > This freeze preserves the Phase 2 diagnostic baseline (`ExplainableRuleEngine` v2.0.0-phase2), evidence extraction rules, candidate scoring equations, heuristic margin confidence calculation, ground-truth isolation, real Linux namespace testbed execution evidence, and validation guards.
  >
  > **This freeze does NOT establish general diagnostic accuracy across all network fault classes, production readiness, calibrated probabilities, or remediation success beyond the measured testbed evidence.**

---

## 2. Provenance & Environment Identity

### Git Repository Revision & Provenance Note
- **Native Git Commit**: `dfa8241b7e28901a8ef1c0e359a4918ef9b4186c`
- **Working Tree Status**: `Uncommitted working tree changes present` (working tree has uncommitted Phase 2 audit reports and test scripts; exact source files are individually pinned by SHA-256 hashes below).
- **WSL Git Boundary Limitation**: When `scratch/build_freeze_manifest.py` executed under Ubuntu WSL2, `git rev-parse HEAD` returned exit code 128 due to `/mnt/d` filesystem boundary ownership restrictions. Consequently, `freeze_manifest.json` accurately recorded `git_provenance.commit: "unpinned"`, `is_dirty: true`, and the corresponding error message. Native Windows Git resolves the commit hash `dfa8241b7e28901a8ef1c0e359a4918ef9b4186c`.

### Execution Environment
- **Platform**: `linux` (Ubuntu WSL2)
- **Python Executable**: `/mnt/d/NetOpsAI/.venv-linux/bin/python`
- **Python Version**: `3.12.15 (main, Oct  1 2026, 20:59:04) [Clang 22.1.3 ]`
- **Dependency Lock Identity**: `requirements.txt` is **omitted on disk** at root level; `requirements_sha256` is recorded as `null` in `freeze_manifest.json` (reflecting actual file system state).

---

## 3. Diagnostic Algorithm Configuration & Verified Formulas

| Parameter / Metric | Frozen Value / Specification | Implementation Location |
|---|---|---|
| Engine Class | `app.cadd.engine.ExplainableRuleEngine` | [`backend/app/cadd/engine.py:25`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L25) |
| Algorithm Version | `2.0.0-phase2` | [`backend/app/cadd/engine.py:32`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L32) |
| Latency Threshold ($\Theta_{\text{lat}}$) | `50.0 ms` | [`backend/app/cadd/engine.py:33`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L33) |
| Loss Threshold ($\Theta_{\text{loss}}$) | `10.0 %` | [`backend/app/cadd/engine.py:34`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L34) |
| Escalation Threshold ($\Theta_{\text{esc}}$) | `0.70` | [`backend/app/cadd/engine.py:35`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L35) |
| Latency Feature Formula | $f_{\text{lat}} = \text{clip}\left(\frac{\text{RTT\_ms} - 50.0}{50.0}, 0, 1\right)$ | [`backend/app/cadd/engine.py:78`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L78) |
| Packet Loss Feature Formula | $f_{\text{loss}} = \text{clip}\left(\frac{\text{loss\_pct} - 10.0}{30.0}, 0, 1\right)$ | [`backend/app/cadd/engine.py:81`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L81) |
| High Latency Candidate Formula | $S(\text{HIGH\_LATENCY\_CONGESTION}) = 0.7 \cdot f_{\text{lat}} + 0.3 \cdot f_{\text{loss}}$ | [`backend/app/cadd/engine.py:111-113`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L111-L113) |
| Packet Loss Candidate Formula | $S(\text{PACKET\_LOSS}) = 0.8 \cdot f_{\text{loss}} + 0.2 \cdot f_{\text{lat}}$ | [`backend/app/cadd/engine.py:115-117`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L115-L117) |
| Heuristic Confidence Formula | $C = \text{round}\left(S(c^*) \cdot (1.0 - 0.5 \cdot S(c^{(2)})), 4\right)$ | [`backend/app/cadd/engine.py:151`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L151) |
| Escalation Predicate | $\text{escalation\_required} = (C < 0.70) \lor (c^* = \text{UNKNOWN\_COMPOSITE\_ANOMALY})$ | [`backend/app/cadd/engine.py:154`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L154) |
| Tie-Breaking Precedence Order | `INTERFACE_FAILURE` > `ROUTING_MISCONFIGURATION` > `DC_MTU_MISMATCH` > `OSPF_ADJACENCY_FLAP` > `WAN_PATH_DEGRADATION` > `HIGH_LATENCY_CONGESTION` > `PACKET_LOSS` > `UNKNOWN_COMPOSITE_ANOMALY` > `HEALTHY` | [`backend/app/cadd/engine.py:38-48`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L38-L48) |

> **Audit Note on Escalation Predicate**:
> In early draft prose, an escalation condition involving `top score < 0.60` was referenced. Source code inspection of [`backend/app/cadd/engine.py:154`](file:///d:/NetOpsAI/backend/app/cadd/engine.py#L154) confirms that the actual frozen implementation evaluates `(confidence < 0.70) or (top_candidate == "UNKNOWN_COMPOSITE_ANOMALY")`. The obsolete `top score < 0.60` text has been removed and superseded by the verified source logic.

---

## 4. Frozen Experiment Records

1. **`exp-phase2-5c538333`** (Primary Verified Baseline Record):
   - Path: [`scratch/research_v2/phase2/runs/exp-phase2-5c538333.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/runs/exp-phase2-5c538333.json)
   - SHA-256: `4ae90e2c8d63c81dc6482901b3861500a7d39a6e6c5b879233b90b9c8e1b0cfc`
   - Status: `RECOVERED`
   - Role: Verified real Linux namespace testbed experiment record ($N=30/50$, detailed `tc -s qdisc` counters, real netem reset remediation & independent verification).
2. **`exp-phase2-04052fa5`** (Historical Comparison Record):
   - Path: [`scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json`](file:///d:/NetOpsAI/scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json)
   - SHA-256: `0ec73222fb18b16f08507705909544ebb746dc1487016b69b6bade9bd68832d9`
   - Status: `DIAGNOSED_PASS`
   - Role: Preserved untouched as historical evidence ($N=5$).

---

## 5. Frozen Source Files & Artifact Cryptographic Checksums (SHA-256)

The checksum values below represent the actual cryptographic SHA-256 digests computed directly from the current disk files and aligned with `freeze_manifest.json`:

| File Relpath | Category | SHA-256 Checksum |
|---|---|---|
| `backend/app/cadd/engine.py` | Core Engine | `ea483491d34cec03aa6a6a7c28e069fb5c1f80341ef742232ba5284837137326` |
| `backend/app/cadd/service.py` | Engine Service | `001eb662130faf773a328b5bf88811613bddbe85cb1dfeee21f22fe9e124c085` |
| `backend/app/models/cadd_models.py` | Data Models | `eee49fa8dec7297d02c944b96c4015418f3f6ad18a674be17b35842085c60bd6` |
| `backend/app/models/ceso_models.py` | Data Models | `0c4a68880c81a937fd806f22d6e75e476d455d10aad96041ce2a9d5d3d1bba20` |
| `backend/app/research_v2/guard.py` | Research Guard | `1a550fa4b75a2f0c28f5223be23fd3fec6e215078535f5343a658e7f90340335` |
| `backend/app/research_v2/testbed/telemetry.py` | Testbed Telemetry | `cd2988faa699fee2debf9688b6570a9e02114f5871a5f5f502ae4686f2604046` |
| `backend/app/research_v2/testbed/faults.py` | Testbed Faults | `f768cf2af86891ba354eb2be1e7d171ea80542f60da21ec5f8ce289fe2f0ad98` |
| `backend/app/research_v2/testbed/remediation.py` | Testbed Remediation | `39558fc99a40c0d153de8ecce602410666f032807c3ff9c4cd35fbc930baa204` |
| `backend/app/research_v2/testbed/verification.py` | Testbed Verification | `9b8f19ab331f66dcf763cd3f0691068a2796179757444562ba81cf3e46a2035d` |
| `backend/app/research_v2/testbed/topology.py` | Testbed Topology | `47b7c9c98d92d60ad01d135cedc4784d88b780209192b736447ecb4b68f70927` |
| `backend/app/research_v2/testbed/models.py` | Testbed Models | `18ea7b0ad667b4c6306a0551543c94848566ff78a26447ee3c5299733ffc0aff` |
| `backend/app/research_v2/testbed/executor.py` | Testbed Executor | `a54c862c1d01ea4453b27ff61025b4fe59665bb04c7fa0e9765f2bf8df2a941a` |
| `backend/app/research_v2/testbed/recorder.py` | Testbed Recorder | `75113d8762a5a1a6f0853bb1996928b40d945d6ccefdbabf7cdb6ec58d16952e` |
| `scratch/run_phase2_experiment.py` | Experiment Runner | `591ab2e40484719ed0eb800204cac4cbb5b89db27a68a64e64929952934f331a` |
| `tests/unit/test_phase2_formula_and_isolation.py` | Unit Tests | `892ecd563a887e5a102b431c3ea7ca74b495d297ab4f3e848946ebcbfbe342f7` |
| `tests/unit/test_phase2_guard.py` | Guard Tests | `c3b13de4713feda4fc352d4cae3e72c7e6892fe363bf385f29bff1f8b0e77e0e` |
| `scratch/research_v2/phase2/independent_record_verification.md` | Audit Report | `005cd7c8591c3e279c25d3c489dd2f42124cc41e5f733338298673db5a132e55` |
| `scratch/research_v2/phase2/final_evidence_check.md` | Audit Report | `7d907ddbe6e2d12f36ac5bea202a70b6406c41343804ece27b47c9e2afa05a40` |
| `scratch/research_v2/phase2/correction_report.md` | Correction Report | `67e3969088652d41a801d1f2bd236844d4218db6306771a267b7fbdcbb9ceed4` |
| `scratch/research_v2/phase2/runs/exp-phase2-5c538333.json` | Baseline Record | `4ae90e2c8d63c81dc6482901b3861500a7d39a6e6c5b879233b90b9c8e1b0cfc` |
| `scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json` | Historical Record | `0ec73222fb18b16f08507705909544ebb746dc1487016b69b6bade9bd68832d9` |
| `requirements.txt` | Dependency Identity | `null` *(File omitted on disk; recorded as null in JSON manifest)* |

---

## 6. Freeze Validation Test Execution Artifact

The test validation output was executed in Ubuntu WSL2 and captured in [`scratch/research_v2/phase2/freeze_validation_test_output.txt`](file:///d:/NetOpsAI/scratch/research_v2/phase2/freeze_validation_test_output.txt):
```text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.1.1, pluggy-1.6.0 -- /mnt/d/NetOpsAI/.venv-linux/bin/python
cachedir: .pytest_cache
rootdir: /mnt/d/NetOpsAI
configfile: pytest.ini
plugins: anyio-4.15.1
collecting ... collected 29 items

tests/unit/test_phase2_formula_and_isolation.py::test_01_hand_calculable_exact_scores PASSED [  3%]
tests/unit/test_phase2_formula_and_isolation.py::test_02_normalization_and_weight_handling PASSED [  6%]
...
tests/phase1/test_privileged_execution.py::test_sudo_passwordless_netns_lifecycle PASSED [100%]

============================== 29 passed in 1.16s ==============================
```

---

## 7. Scope Boundaries & Audit Constraints

1. **Testbed Scope Limit**: Empirical evidence is bounded to the 4-node Linux network namespace testbed under `HIGH_LATENCY_CONGESTION` fault injection (150ms delay, 20% loss).
2. **Heuristic Confidence**: Confidence values represent non-calibrated evidence intensity margins in $[0, 1]$, not empirical posterior probabilities.
3. **Phase 3 Non-Authorization**: Phase 3 research experiments, baselines, and ablations remain un-executed until Phase 3 protocol authorization.
