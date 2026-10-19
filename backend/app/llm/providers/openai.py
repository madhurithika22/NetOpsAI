import time
import requests
from typing import Tuple
from app.llm.providers.base import BaseLLMProvider
from app.llm.models import LLMHealthStatus, LLMStatus, TokenMetrics, TokenMeasurementMethod
from app.llm.token_metrics import estimate_tokens

class OpenAICompatibleProvider(BaseLLMProvider):
    def health_check(self) -> LLMHealthStatus:
        if not self.config.enabled:
            return LLMHealthStatus(
                enabled=False,
                provider="openai",
                model=self.config.model,
                status=LLMStatus.LLM_DISABLED,
                reachable=False,
                error="LLM disabled via configuration"
            )

        t0 = time.perf_counter()
        try:
            url = f"{self.config.base_url.rstrip('/')}/v1/models"
            resp = requests.get(url, timeout=min(5, self.config.timeout_seconds))
            latency = (time.perf_counter() - t0) * 1000.0

            if resp.status_code == 200:
                return LLMHealthStatus(
                    enabled=True,
                    provider="openai",
                    model=self.config.model,
                    status=LLMStatus.LLM_AVAILABLE,
                    reachable=True,
                    latency_ms=round(latency, 2)
                )
            else:
                return LLMHealthStatus(
                    enabled=True,
                    provider="openai",
                    model=self.config.model,
                    status=LLMStatus.LLM_UNAVAILABLE,
                    reachable=False,
                    latency_ms=round(latency, 2),
                    error=f"Server returned HTTP {resp.status_code}"
                )
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            return LLMHealthStatus(
                enabled=True,
                provider="openai",
                model=self.config.model,
                status=LLMStatus.LLM_UNAVAILABLE,
                reachable=False,
                latency_ms=round(latency, 2),
                error=f"Endpoint unreachable at {self.config.base_url}: {str(e)}"
            )

    def generate(self, system_prompt: str, user_prompt: str) -> Tuple[str, TokenMetrics]:
        url = f"{self.config.base_url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.config.temperature
        }

        t0 = time.perf_counter()
        resp = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
        latency = (time.perf_counter() - t0) * 1000.0

        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI API request failed with status {resp.status_code}: {resp.text}")

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        p_tokens = usage.get("prompt_tokens")
        c_tokens = usage.get("completion_tokens")

        if p_tokens is not None and c_tokens is not None:
            metrics = TokenMetrics(
                input_tokens=int(p_tokens),
                output_tokens=int(c_tokens),
                total_tokens=int(p_tokens + c_tokens),
                latency_ms=round(latency, 2),
                measurement_method=TokenMeasurementMethod.PROVIDER_REPORTED
            )
        else:
            in_t = estimate_tokens(system_prompt + "\n\n" + user_prompt)
            out_t = estimate_tokens(content)
            metrics = TokenMetrics(
                input_tokens=in_t,
                output_tokens=out_t,
                total_tokens=in_t + out_t,
                latency_ms=round(latency, 2),
                measurement_method=TokenMeasurementMethod.ESTIMATED
            )

        return content, metrics
