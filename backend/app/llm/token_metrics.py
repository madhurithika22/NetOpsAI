import math
from typing import Tuple
from app.llm.models import TokenMetrics, TokenMeasurementMethod

def estimate_tokens(text: str) -> int:
    """
    Estimates token count using a standard LLM character/word ratio.
    ~4 characters per token or ~0.75 words per token.
    """
    if not text:
        return 0
    words = text.split()
    chars = len(text)
    # Average of character heuristic and word heuristic for high accuracy
    token_est = int(math.ceil((chars / 3.8 + len(words) / 0.75) / 2.0))
    return max(1, token_est)

def calculate_token_reduction(direct_metrics: TokenMetrics, pipeline_metrics: TokenMetrics) -> Tuple[float, float]:
    """
    Calculates input token reduction percentage and total token reduction percentage.
    Formula:
    input_reduction_pct = (direct_input_tokens - pipeline_input_tokens) / direct_input_tokens * 100
    total_reduction_pct = (direct_total_tokens - pipeline_total_tokens) / direct_total_tokens * 100
    """
    if direct_metrics.input_tokens == 0:
        input_reduction = 0.0
    else:
        input_reduction = ((direct_metrics.input_tokens - pipeline_metrics.input_tokens) / float(direct_metrics.input_tokens)) * 100.0

    if direct_metrics.total_tokens == 0:
        total_reduction = 0.0
    else:
        total_reduction = ((direct_metrics.total_tokens - pipeline_metrics.total_tokens) / float(direct_metrics.total_tokens)) * 100.0

    return max(0.0, round(input_reduction, 2)), max(0.0, round(total_reduction, 2))
