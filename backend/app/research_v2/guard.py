"""
Research Execution Guard Module for NetOps Research V2.

Protects research execution pipelines from accidental contamination by mock providers,
synthetic state generators, reset_simulation() calls, or hardcoded evaluation overrides.
"""

from typing import Optional

class ResearchGuardViolationError(RuntimeError):
    """Raised when a simulation path or mock provider is invoked during research execution."""
    pass


class ResearchExecutionContext:
    """
    Context manager to enforce strict research-real mode.
    """
    _current_mode: str = "production"

    def __init__(self, mode: str = "research_real"):
        self.mode = mode
        self._previous_mode = None

    def __enter__(self):
        self._previous_mode = ResearchExecutionContext._current_mode
        ResearchExecutionContext._current_mode = self.mode
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ResearchExecutionContext._current_mode = self._previous_mode

    @classmethod
    def get_mode(cls) -> str:
        return cls._current_mode

    @classmethod
    def is_research_mode(cls) -> bool:
        return cls._current_mode == "research_real"

    @classmethod
    def assert_real_execution(cls, caller_symbol: str):
        """
        Asserts that the current context allows execution.
        If in 'research_real' mode and caller is a mock/simulation provider, raises exception.
        """
        if cls.is_research_mode():
            forbidden_keywords = [
                "simulated", "mock", "reset_simulation", "synthetic",
                "hardcoded", "fixture", "fallback"
            ]
            lower_caller = caller_symbol.lower()
            if any(k in lower_caller for k in forbidden_keywords):
                raise ResearchGuardViolationError(
                    f"CRITICAL RESEARCH INTEGRITY VIOLATION: '{caller_symbol}' is a simulated/mock path "
                    f"and cannot be executed during 'research_real' mode."
                )


class Phase2ResearchViolationError(ResearchGuardViolationError):
    """Raised when a Phase 2 research record violates research integrity rules."""
    pass


class Phase2ResearchValidator:
    """
    Phase 2 Research Result Validator.
    Rejects any research record that fails ground-truth isolation,
    runs on non-Linux platforms, uses mock/fixture data, lacks computed evidence traces,
    or contains hardcoded confidence values.
    """

    @classmethod
    def validate_record(cls, record_dict: dict) -> bool:
        # 1. Environment check: MUST be linux
        sys_info = record_dict.get("system_info", {})
        platform_str = sys_info.get("platform", "").lower()
        if platform_str != "linux":
            raise Phase2ResearchViolationError(
                f"PHASE 2 VALIDATION FAILED: Execution platform '{platform_str}' is not Linux."
            )

        # 2. Rejects records originating from unit tests or fixtures
        exp_id = str(record_dict.get("experiment_id", "")).lower()
        run_id = str(record_dict.get("run_id", "")).lower()
        if any(k in exp_id or k in run_id for k in ["test", "fixture", "mock", "pytest", "unit"]):
            raise Phase2ResearchViolationError(
                f"PHASE 2 VALIDATION FAILED: Experiment record '{exp_id}' originates from a test/fixture."
            )

        # 3. Operational inputs check: no ground-truth fields in operational diagnosis input
        top_def = record_dict.get("topology_definition", {})
        top_id = str(top_def.get("topology_id", "")).upper()
        if top_id in ["CASE_01", "CASE_02", "CASE_03", "CASE_04"]:
            raise Phase2ResearchViolationError(
                f"PHASE 2 VALIDATION FAILED: Operational input contains answer-leaking topology ID '{top_id}'."
            )

        # 4. Computed score/confidence & algorithm version check
        diag_rec = record_dict.get("diagnosis_record", {}) or record_dict.get("cadd_diagnosis", {})
        alg_version = diag_rec.get("algorithm_version")
        alg_config = diag_rec.get("algorithm_config")
        candidate_scores = diag_rec.get("candidate_scores")
        conf_score = diag_rec.get("confidence_score")

        if not alg_version or not alg_config:
            raise Phase2ResearchViolationError(
                "PHASE 2 VALIDATION FAILED: Diagnosis record missing algorithm_version or algorithm_config."
            )

        if not candidate_scores or not isinstance(candidate_scores, dict) or len(candidate_scores) == 0:
            raise Phase2ResearchViolationError(
                "PHASE 2 VALIDATION FAILED: Candidate scores map is missing or uncomputed."
            )

        if conf_score is None:
            raise Phase2ResearchViolationError(
                "PHASE 2 VALIDATION FAILED: Confidence score is missing."
            )

        # Check for legacy hardcoded low confidence cheat
        if conf_score == 0.47 and "UNKNOWN_COMPOSITE_ANOMALY" not in candidate_scores:
            raise Phase2ResearchViolationError(
                "PHASE 2 VALIDATION FAILED: Hardcoded 0.47 confidence detected without candidate scoring."
            )

        # 5. Raw evidence check: must contain raw execution history
        raw_cmd_hist = record_dict.get("raw_command_history", [])
        if not raw_cmd_hist or len(raw_cmd_hist) == 0:
            raise Phase2ResearchViolationError(
                "PHASE 2 VALIDATION FAILED: Raw execution command evidence history is missing."
            )

        return True

