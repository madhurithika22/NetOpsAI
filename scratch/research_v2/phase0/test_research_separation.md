# NetOps Test vs Research Separation Audit

Software regression tests (`tests/unit/`, `tests/integration/`) are cleanly separated from research benchmarks (`scratch/run_phase7a_benchmark.py`). However, mock providers used in unit tests were accidentally allowed to act as fallbacks during benchmark runs when Ollama was offline.
