"""
Unit tests for Research Execution Guard.
"""

import pytest
from app.research_v2.guard import (
    ResearchExecutionContext,
    ResearchGuardViolationError
)


def test_research_guard_allows_real():
    with ResearchExecutionContext(mode="research_real"):
        assert ResearchExecutionContext.is_research_mode() is True
        # Asserting a real component symbol passes
        ResearchExecutionContext.assert_real_execution("RealTelemetryCollector")


def test_research_guard_blocks_simulated():
    with ResearchExecutionContext(mode="research_real"):
        with pytest.raises(ResearchGuardViolationError) as exc_info:
            ResearchExecutionContext.assert_real_execution("SimulatedTelemetryProvider")
        assert "is a simulated/mock path" in str(exc_info.value)

        with pytest.raises(ResearchGuardViolationError):
            ResearchExecutionContext.assert_real_execution("reset_simulation")

        with pytest.raises(ResearchGuardViolationError):
            ResearchExecutionContext.assert_real_execution("MockLLMProvider")
