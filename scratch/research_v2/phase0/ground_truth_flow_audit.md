# NetOps Ground Truth Flow Audit

**Ground Truth Leakage Path Identified**:
In `ExplainableRuleEngine` (`backend/app/cadd/engine.py`), diagnostic rules check `state.topology_id` (e.g. `topology_id == 'CASE_01'`). Because `topology_id` directly identifies the scenario name, the diagnostic engine bypasses general telemetry reasoning and executes scenario-specific canned logic. Ground truth leaks into rule selection.
