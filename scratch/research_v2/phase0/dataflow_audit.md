# NetOps Dataflow Audit

| Stage | Implementation | Input | Output | Real/Simulated | Evidence |
|---|---|---|---|---|---|
| Telemetry | `LinuxTestbedTelemetryProvider` / `SimulatedTelemetryProvider` | Ping/link shell output or dict generator | `NetworkState` | MIXED | `provider.py:188` (ping measured, throughput assigned) |
| CESO | `CESOService` | `NetworkState` | `CESOSummary` | REAL | `service.py:17` |
| CADD | `ExplainableRuleEngine` | `NetworkState` | `DiagnosticReport` + `ActionPlan` | REAL | `engine.py:18` (matches rules on topology_id) |
| Confidence | `ExplainableRuleEngine` | Matched Rule | `float` (0.47, 0.95, etc.) | SIMULATED | `engine.py:144, 204` (hardcoded constants) |
| Escalation | `ExplainableRuleEngine` | confidence_score < 0.70 | `bool` | REAL | `engine.py:207` |
| LLM | `LLMGateway` / `OllamaProvider` | Prompt context package | JSON text / `LLMResponse` | REAL (Ollama) / MOCK | `gateway.py:102`, `ollama.py:25` |
| MSVS | `SafetyPolicyEngine` | `ActionPlan` | `ValidationResult` | REAL | `policies.py:15` |
| Execution | `MSVSService.execute_action_plan` | `plan_id` | `ExecutionLog` | SIMULATED | `service.py:94` (calls `reset_simulation()`) |
| Verification | `MSVSService.execute_action_plan` | `post_state` | `bool` | SIMULATED | `service.py:97` (verifies reset simulation state) |
| Metrics | `EvaluationMetricsEngine` | `List[ExperimentRecord]` | Metric dictionary | REAL / MIXED | `metrics.py:45` (VSR=66.7% hardcoded) |
