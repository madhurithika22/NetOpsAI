from typing import Dict, Any, List
from app.llm.models import LLMPostActionFeedbackRequest

def create_feedback_package(
    action_id: str,
    result: str,
    verification_passed: bool,
    pre_metrics: Dict[str, Any],
    post_metrics: Dict[str, Any],
    affected_services: List[str] = None,
    observed_side_effects: List[str] = None
) -> LLMPostActionFeedbackRequest:
    deltas = {}
    for k in pre_metrics:
        if k in post_metrics and isinstance(pre_metrics[k], (int, float)) and isinstance(post_metrics[k], (int, float)):
            deltas[f"{k}_delta"] = round(post_metrics[k] - pre_metrics[k], 2)

    return LLMPostActionFeedbackRequest(
        action_id=action_id,
        result=result,
        verification_passed=verification_passed,
        pre_action_metrics=pre_metrics,
        post_action_metrics=post_metrics,
        metric_deltas=deltas,
        affected_services=affected_services or [],
        observed_side_effects=observed_side_effects or []
    )
