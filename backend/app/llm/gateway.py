import os
import json
import uuid
from typing import Dict, Any, Optional
from app.llm.models import (
    LLMConfig, LLMHealthStatus, LLMStatus, LLMContextPackage,
    LLMDiagnosisResponse, LLMPostActionFeedbackRequest, LLMPostActionAssessment,
    DirectVsNetOpsExperimentResult, TokenMetrics, TokenMeasurementMethod
)
from app.llm.providers import get_llm_provider
from app.llm.prompts import SYSTEM_PROMPT, build_direct_prompt, build_netops_prompt, build_feedback_prompt
from app.llm.token_metrics import calculate_token_reduction

class LLMGateway:
    def __init__(self):
        self.config = self._load_config_from_env()
        self.provider = get_llm_provider(self.config)

    def _load_config_from_env(self) -> LLMConfig:
        enabled_str = os.getenv("LLM_ENABLED", "true").lower()
        enabled = enabled_str in ["true", "1", "yes"]
        provider = os.getenv("LLM_PROVIDER", "ollama")
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
        model = os.getenv("LLM_MODEL", "llama3")
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

        return LLMConfig(
            enabled=enabled,
            provider=provider,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout,
            temperature=temperature
        )

    def set_config(self, config: LLMConfig):
        self.config = config
        self.provider = get_llm_provider(config)

    def get_health(self) -> LLMHealthStatus:
        # If env has overridden provider, update unless custom provider set
        env_provider = os.getenv("LLM_PROVIDER")
        if env_provider and env_provider != self.config.provider:
            self.config = self._load_config_from_env()
            self.provider = get_llm_provider(self.config)
        return self.provider.health_check()

    def analyze_direct_raw_logs(
        self, scenario_id: str, raw_telemetry: Dict[str, Any], raw_logs: list = None, topology_events: list = None
    ) -> LLMDiagnosisResponse:
        health = self.get_health()
        if not health.reachable:
            return LLMDiagnosisResponse(
                diagnosis="LLM_UNAVAILABLE",
                reasoning_summary=f"LLM provider '{self.config.provider}' is unavailable: {health.error}",
                confidence=0.0,
                llm_status=health.status,
                raw_response=health.error or "Provider unreachable"
            )

        user_prompt = build_direct_prompt(raw_telemetry, raw_logs or [], topology_events or [])
        
        try:
            raw_response, token_metrics = self.provider.generate(SYSTEM_PROMPT, user_prompt)
            parsed = self._parse_json_response(raw_response)
            return LLMDiagnosisResponse(
                diagnosis=parsed.get("diagnosis", "DIRECT_ANALYSIS_COMPLETED"),
                reasoning_summary=parsed.get("reasoning_summary", raw_response),
                evidence=parsed.get("evidence", []),
                confidence=float(parsed.get("confidence", 0.75)),
                recommended_action=parsed.get("recommended_action"),
                alternatives=parsed.get("alternatives", []),
                uncertainty=parsed.get("uncertainty", ""),
                raw_response=raw_response,
                token_metrics=token_metrics,
                llm_status=LLMStatus.LLM_AVAILABLE
            )
        except Exception as e:
            return LLMDiagnosisResponse(
                diagnosis="LLM_ERROR",
                reasoning_summary=f"LLM direct inference error: {str(e)}",
                confidence=0.0,
                llm_status=LLMStatus.LLM_ERROR,
                raw_response=str(e)
            )

    def analyze_netops_context(self, context_package: LLMContextPackage) -> LLMDiagnosisResponse:
        health = self.get_health()
        if not health.reachable:
            return LLMDiagnosisResponse(
                diagnosis="LLM_UNAVAILABLE",
                reasoning_summary=f"LLM provider '{self.config.provider}' is unavailable: {health.error}",
                confidence=0.0,
                llm_status=health.status,
                raw_response=health.error or "Provider unreachable"
            )

        user_prompt = build_netops_prompt(context_package)

        try:
            raw_response, token_metrics = self.provider.generate(SYSTEM_PROMPT, user_prompt)
            parsed = self._parse_json_response(raw_response)
            return LLMDiagnosisResponse(
                diagnosis=parsed.get("diagnosis", "NETOPS_PIPELINE_ANALYSIS_COMPLETED"),
                reasoning_summary=parsed.get("reasoning_summary", raw_response),
                evidence=parsed.get("evidence", []),
                confidence=float(parsed.get("confidence", 0.85)),
                recommended_action=parsed.get("recommended_action"),
                alternatives=parsed.get("alternatives", []),
                uncertainty=parsed.get("uncertainty", ""),
                raw_response=raw_response,
                token_metrics=token_metrics,
                llm_status=LLMStatus.LLM_AVAILABLE
            )
        except Exception as e:
            return LLMDiagnosisResponse(
                diagnosis="LLM_ERROR",
                reasoning_summary=f"LLM pipeline inference error: {str(e)}",
                confidence=0.0,
                llm_status=LLMStatus.LLM_ERROR,
                raw_response=str(e)
            )

    def run_controlled_token_experiment(
        self,
        scenario_id: str,
        raw_telemetry: Dict[str, Any],
        raw_logs: list,
        topology_events: list,
        context_package: LLMContextPackage
    ) -> DirectVsNetOpsExperimentResult:
        direct_res = self.analyze_direct_raw_logs(scenario_id, raw_telemetry, raw_logs, topology_events)
        netops_res = self.analyze_netops_context(context_package)

        in_red, tot_red = calculate_token_reduction(direct_res.token_metrics, netops_res.token_metrics)
        measurement_method = direct_res.token_metrics.measurement_method

        return DirectVsNetOpsExperimentResult(
            scenario_id=scenario_id,
            model=self.config.model,
            provider=self.config.provider,
            direct=direct_res.token_metrics,
            netops_pipeline=netops_res.token_metrics,
            input_token_reduction_pct=in_red,
            total_token_reduction_pct=tot_red,
            direct_response_summary=direct_res.reasoning_summary[:200],
            netops_response_summary=netops_res.reasoning_summary[:200],
            token_measurement_method=measurement_method
        )

    def assess_post_remediation(self, feedback_req: LLMPostActionFeedbackRequest) -> LLMPostActionAssessment:
        health = self.get_health()
        if not health.reachable:
            return LLMPostActionAssessment(
                diagnosis_supported=feedback_req.verification_passed,
                remediation_effective=feedback_req.verification_passed,
                additional_action_required=not feedback_req.verification_passed,
                observation_recommended=True,
                assessment_summary="LLM unavailable for post-action assessment; relying on MSVS verification status."
            )

        prompt = build_feedback_prompt(
            action_id=feedback_req.action_id,
            result=feedback_req.result,
            verification_passed=feedback_req.verification_passed,
            pre_metrics=feedback_req.pre_action_metrics,
            post_metrics=feedback_req.post_action_metrics,
            deltas=feedback_req.metric_deltas,
            services=feedback_req.affected_services,
            side_effects=feedback_req.observed_side_effects
        )

        try:
            raw_resp, token_metrics = self.provider.generate(SYSTEM_PROMPT, prompt)
            parsed = self._parse_json_response(raw_resp)
            return LLMPostActionAssessment(
                diagnosis_supported=bool(parsed.get("diagnosis_supported", True)),
                remediation_effective=bool(parsed.get("remediation_effective", feedback_req.verification_passed)),
                additional_action_required=bool(parsed.get("additional_action_required", False)),
                observation_recommended=bool(parsed.get("observation_recommended", True)),
                assessment_summary=parsed.get("assessment_summary", raw_resp),
                raw_response=raw_resp,
                token_metrics=token_metrics
            )
        except Exception as e:
            return LLMPostActionAssessment(
                diagnosis_supported=feedback_req.verification_passed,
                remediation_effective=feedback_req.verification_passed,
                additional_action_required=not feedback_req.verification_passed,
                observation_recommended=True,
                assessment_summary=f"LLM post-action assessment error: {str(e)}"
            )

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except Exception:
                    pass
            return {"reasoning_summary": text}

llm_gateway = LLMGateway()
