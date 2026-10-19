"""
Exceptions for Real Linux Network Namespace Research Testbed.
"""

class ResearchTestbedError(Exception):
    """Base exception for all research testbed errors."""
    pass

class TestbedCapabilityError(ResearchTestbedError):
    """Raised when host environment lacks required Linux network namespace capabilities."""
    pass

class TopologyCreationError(ResearchTestbedError):
    """Raised when network namespace topology creation fails."""
    pass

class BaselineMeasurementError(ResearchTestbedError):
    """Raised when network baseline measurement fails or is unhealthy."""
    pass

class FaultInjectionError(ResearchTestbedError):
    """Raised when fault injection command fails."""
    pass

class FaultActivationError(ResearchTestbedError):
    """Raised when fault is injected but telemetry does not observe expected degradation."""
    pass

class RemediationExecutionError(ResearchTestbedError):
    """Raised when remediation command execution fails."""
    pass

class VerificationError(ResearchTestbedError):
    """Raised when independent post-remediation verification fails."""
    pass

class CleanupError(ResearchTestbedError):
    """Raised when testbed namespace cleanup fails."""
    pass
