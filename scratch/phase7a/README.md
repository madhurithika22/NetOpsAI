# NetOps Phase 7A — Reproducible Benchmark Artifacts

This directory contains the primary research benchmark artifacts generated during **NetOps Phase 7A**.

## Files Included
- `benchmark_manifest.json`: Index of all benchmark files and summary metrics.
- `benchmark_results.json`: Full detailed records for all 40 primary benchmark runs.
- `benchmark_results.csv`: CSV export of all 40 primary benchmark runs.
- `case01_results.json` ... `case04_results.json`: Per-scenario run records.
- `token_comparison.json`: 5 paired Case 4 token efficiency runs comparing Direct vs Pipeline representation against Ollama `qwen3:4b`.
- `safety_results.json`: MSVS 4-scenario safety regression suite results.
- `ground_truth_audit.json`: Ground-truth isolation audit verification for all runs.
- `environment.json`: Execution environment configuration and Ollama health metadata.

## Summary Metrics
- **Primary Benchmark Runs**: 40 runs (4 scenarios x 10 runs)
- **Diagnosis Accuracy / F1**: 100.00%
- **Verification Success Rate**: 100.00%
- **NESS Composite Score**: 0.75
- **Token Input Reduction (Case 4 vs Direct)**: 43.86%
- **Ground-Truth Isolation Audit**: Passed (40 runs verified)
- **MSVS Safety Suite**: Passed (100% unsafe actions blocked)
