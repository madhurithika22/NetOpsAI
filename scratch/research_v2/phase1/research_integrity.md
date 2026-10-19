# Research Integrity Rules for Phase 1

1. ZERO SIMULATION FALLBACKS: If host OS lacks Linux network namespace support, capability check fails explicitly.
2. NO FABRICATED MEASUREMENTS: Telemetry snapshot fields are parsed directly from shell command output.
3. CAUSAL REMEDIATION: Remediation requires running real corrective commands (`tc qdisc del`).
4. IMMUTABLE RAW EVIDENCE: All raw command stdout, stderr, and exit codes are recorded in experiment JSON logs.
