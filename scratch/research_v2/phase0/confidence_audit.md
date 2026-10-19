# NetOps Confidence & Escalation Audit

- **Escalation Threshold**: Defined in `ExplainableRuleEngine.CONFIDENCE_ESCALATION_THRESHOLD = 0.70` (`backend/app/cadd/engine.py:14`).
- **Escalation Logic**: If `confidence_score < 0.70`, `escalation_required` is set to `True`, triggering secondary LLM reasoning.
- **Reproducibility**: The score `0.47` for Case 4 is NOT reproducible from telemetry metrics; it is a hardcoded literal assigned to force the system to cross the escalation threshold.
- **Cross-Fault Comparability**: Because scores are static literals rather than normalized probabilities, confidence values cannot be compared across different fault classes scientifically.
