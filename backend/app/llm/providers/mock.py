import json
import time
from typing import Tuple
from app.llm.providers.base import BaseLLMProvider
from app.llm.models import LLMHealthStatus, LLMStatus, TokenMetrics, TokenMeasurementMethod
from app.llm.token_metrics import estimate_tokens

class MockLLMProvider(BaseLLMProvider):
    def health_check(self) -> LLMHealthStatus:
        if not self.config.enabled:
            return LLMHealthStatus(
                enabled=False,
                provider="mock",
                model=self.config.model,
                status=LLMStatus.LLM_DISABLED,
                reachable=False,
                error="LLM disabled"
            )
        return LLMHealthStatus(
            enabled=True,
            provider="mock",
            model=self.config.model,
            status=LLMStatus.LLM_AVAILABLE,
            reachable=True,
            latency_ms=1.5
        )

    def generate(self, system_prompt: str, user_prompt: str) -> Tuple[str, TokenMetrics]:
        t0 = time.perf_counter()
        
        if "CASE_04" in user_prompt or "NOVEL_COMPOSITE_ANOMALY" in user_prompt or "edge-gw-01" in user_prompt:
            res_dict = {
                "diagnosis": "NOVEL_COMPOSITE_ANOMALY",
                "reasoning_summary": "Multidimensional analysis indicates DNS resolver cache lock contention on edge-gw-01 combined with BGP local-preference route shift towards secondary WAN.",
                "evidence": [
                    "edge-gw-01 CPU utilization at 58% due to resolver lock",
                    "BGP route metric shift to 150 on wan0",
                    "Packet loss at 7.5% on edge-to-wan path"
                ],
                "confidence": 0.88,
                "recommended_action": {
                    "action_id": "act-case04-remed",
                    "command_type": "RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE",
                    "target_device": "edge-gw-01",
                    "parameters": {
                        "service": "dns-resolver",
                        "target_gateway": "edge-gw-01",
                        "action": "FLUSH_DNS_CACHE_AND_RESTORE_BGP_LOCAL_PREF",
                        "bgp_neighbor": "cloud-gw-01",
                        "local_pref": 200
                    }
                },
                "alternatives": ["RESTART_EDGE_GATEWAY_SERVICE"],
                "uncertainty": "Requires post-action monitoring of cloud sync latency"
            }
        else:
            res_dict = {
                "diagnosis": "NETWORK_INCIDENT_DIAGNOSED",
                "reasoning_summary": "LLM evaluated context package and confirmed target node degradation.",
                "evidence": ["High latency observed on core link"],
                "confidence": 0.85,
                "recommended_action": {
                    "action_id": "act-mock-remed",
                    "command_type": "REROUTE_TRAFFIC",
                    "target_device": "core-rtr01",
                    "parameters": {"interface": "eth2", "new_metric": 100}
                },
                "alternatives": [],
                "uncertainty": "None"
            }

        response_text = json.dumps(res_dict, indent=2)
        latency = (time.perf_counter() - t0) * 1000.0

        in_tokens = estimate_tokens(system_prompt + "\n\n" + user_prompt)
        out_tokens = estimate_tokens(response_text)

        metrics = TokenMetrics(
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=in_tokens + out_tokens,
            latency_ms=round(latency, 2),
            measurement_method=TokenMeasurementMethod.ESTIMATED
        )

        return response_text, metrics
