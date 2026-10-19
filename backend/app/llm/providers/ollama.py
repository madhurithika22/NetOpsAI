import time
import requests
from typing import Tuple
from app.llm.providers.base import BaseLLMProvider
from app.llm.models import LLMHealthStatus, LLMStatus, TokenMetrics, TokenMeasurementMethod
from app.llm.token_metrics import estimate_tokens

class OllamaProvider(BaseLLMProvider):
    def health_check(self) -> LLMHealthStatus:
        if not self.config.enabled:
            return LLMHealthStatus(
                enabled=False,
                provider="ollama",
                model=self.config.model,
                status=LLMStatus.LLM_DISABLED,
                reachable=False,
                error="LLM disabled via configuration"
            )

        t0 = time.perf_counter()
        try:
            url = f"{self.config.base_url.rstrip('/')}/api/tags"
            resp = requests.get(url, timeout=1.5)
            latency = (time.perf_counter() - t0) * 1000.0

            if resp.status_code == 200:
                models_data = resp.json().get("models", [])
                return LLMHealthStatus(
                    enabled=True,
                    provider="ollama",
                    model=self.config.model,
                    status=LLMStatus.LLM_AVAILABLE,
                    reachable=True,
                    latency_ms=round(latency, 2)
                )
            else:
                return LLMHealthStatus(
                    enabled=True,
                    provider="ollama",
                    model=self.config.model,
                    status=LLMStatus.LLM_UNAVAILABLE,
                    reachable=False,
                    latency_ms=round(latency, 2),
                    error=f"Ollama server returned HTTP {resp.status_code}"
                )
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            return LLMHealthStatus(
                enabled=True,
                provider="ollama",
                model=self.config.model,
                status=LLMStatus.LLM_UNAVAILABLE,
                reachable=False,
                latency_ms=round(latency, 2),
                error=f"Ollama endpoint unreachable at {self.config.base_url}: {str(e)}"
            )

    def generate(self, system_prompt: str, user_prompt: str) -> Tuple[str, TokenMetrics]:
        url = f"{self.config.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": 256
            }
        }

        t0 = time.perf_counter()
        resp = requests.post(url, json=payload, timeout=max(self.config.timeout_seconds, 180))
        latency = (time.perf_counter() - t0) * 1000.0

        if resp.status_code != 200:
            raise RuntimeError(f"Ollama API request failed with status {resp.status_code}: {resp.text}")

        data = resp.json()
        response_text = data.get("response", "")

        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")

        if prompt_tokens is not None and completion_tokens is not None:
            metrics = TokenMetrics(
                input_tokens=int(prompt_tokens),
                output_tokens=int(completion_tokens),
                total_tokens=int(prompt_tokens + completion_tokens),
                latency_ms=round(latency, 2),
                measurement_method=TokenMeasurementMethod.PROVIDER_REPORTED
            )
        else:
            in_t = estimate_tokens(system_prompt + "\n\n" + user_prompt)
            out_t = estimate_tokens(response_text)
            metrics = TokenMetrics(
                input_tokens=in_t,
                output_tokens=out_t,
                total_tokens=in_t + out_t,
                latency_ms=round(latency, 2),
                measurement_method=TokenMeasurementMethod.ESTIMATED
            )

        return response_text, metrics
