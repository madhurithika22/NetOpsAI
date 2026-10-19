# NetOps CADD Algorithm Audit

## Confidence Score Origin Trace
Every confidence score in `ExplainableRuleEngine` is a static hardcoded float constant assigned inside specific `if topology_id == ...` rule branches:
- Case 1: `0.95`
- Case 2: `0.94`
- Case 3: `0.96`
- Case 4: `0.47` (Static low confidence value forced to trigger LLM escalation)
- Interface Failure: `0.99`
- Routing Misconfig: `0.98`
- High Latency: `0.95`
- Packet Loss: `0.92`

None of these confidence scores are calculated from mathematical evidence weights or probabilities.
