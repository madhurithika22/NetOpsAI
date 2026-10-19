"""
Data Models for Real Linux Network Namespace Research Testbed.
Defines immutable records, command evidence, telemetry snapshots, and experiment results.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CommandExecutionRecord(BaseModel):
    """Raw shell command execution record for auditability."""
    original_command: List[str] = Field(default_factory=list)
    effective_command: List[str] = Field(default_factory=list)
    privileged: bool = False
    namespace: Optional[str] = None
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    return_code: int
    stdout: str
    stderr: str


class InterfaceStateRecord(BaseModel):
    """Measured state of a single network interface."""
    name: str
    is_up: bool
    mac_address: Optional[str] = None
    ip_addresses: List[str] = Field(default_factory=list)
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_errors: int = 0
    tx_errors: int = 0
    rx_drops: int = 0
    tx_drops: int = 0
    mtu: int = 1500


class LinkLatencyRecord(BaseModel):
    """Measured link latency & packet loss from ping ICMP probe."""
    source_node: str
    target_node: str
    target_ip: str
    packets_tx: int
    packets_rx: int
    packet_loss_pct: float
    rtt_min_ms: float
    rtt_avg_ms: float
    rtt_max_ms: float
    rtt_mdev_ms: float = 0.0


class RouteRecord(BaseModel):
    """Measured IP routing table entry."""
    destination: str
    gateway: Optional[str] = None
    interface: Optional[str] = None
    metric: Optional[int] = None
    raw_route: str = ""


class QdiscRecord(BaseModel):
    """Measured Linux traffic control (tc) qdisc state."""
    namespace: str
    interface: str
    qdisc_type: str
    handle: Optional[str] = None
    parent: Optional[str] = None
    options_raw: str = ""


class TelemetrySnapshot(BaseModel):
    """Immutable real telemetry snapshot taken directly from Linux namespaces."""
    snapshot_id: str
    experiment_id: str
    timestamp: datetime
    source_namespace: str
    destination_ip: str
    link_latency: Optional[LinkLatencyRecord] = None
    interface_states: Dict[str, InterfaceStateRecord] = Field(default_factory=dict)
    routes: List[RouteRecord] = Field(default_factory=list)
    qdiscs: List[QdiscRecord] = Field(default_factory=list)
    raw_commands: List[CommandExecutionRecord] = Field(default_factory=list)
    is_healthy: bool = True
    summary: str = ""


class FaultDefinition(BaseModel):
    """Specification of a real fault to inject into Linux namespace."""
    fault_id: str
    fault_type: str
    target_namespace: str
    target_interface: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    injection_command: List[str] = Field(default_factory=list)
    reset_command: List[str] = Field(default_factory=list)


class FaultInjectionRecord(BaseModel):
    """Execution log of fault injection and post-injection observation."""
    fault_id: str
    fault_type: str
    target_namespace: str
    target_interface: str
    parameters: Dict[str, Any]
    injection_command_record: CommandExecutionRecord
    injection_timestamp: datetime
    status: str  # ACTIVE, FAULT_ACTIVATION_FAILED, INJECTION_FAILED
    pre_fault_snapshot: TelemetrySnapshot
    post_fault_snapshot: TelemetrySnapshot
    activation_verified: bool
    observed_rtt_ms: float
    observed_loss_pct: float


class RemediationPlan(BaseModel):
    """Specification of real corrective command to execute."""
    plan_id: str
    fault_id: str
    remediation_type: str
    target_namespace: str
    target_interface: str
    remediation_command: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)


class RemediationExecutionRecord(BaseModel):
    """Log of real remediation command execution."""
    execution_id: str
    plan_id: str
    executed_at: datetime
    command_record: CommandExecutionRecord
    status: str  # EXECUTED, FAILED
    pre_remediation_snapshot: TelemetrySnapshot


class IndependentVerificationRecord(BaseModel):
    """Log of independent post-remediation recovery verification."""
    verification_id: str
    plan_id: str
    timestamp: datetime
    verification_snapshot: TelemetrySnapshot
    reachability_healthy: bool
    loss_healthy: bool
    rtt_healthy: bool
    qdisc_absent: bool
    overall_passed: bool
    criteria_details: Dict[str, Any]


class ExperimentRecord(BaseModel):
    """Complete, immutable causal research record of a single testbed run."""
    experiment_id: str
    run_id: str
    timestamp: datetime
    testbed_version: str = "2.0.0-phase1"
    system_info: Dict[str, Any] = Field(default_factory=dict)
    topology_definition: Dict[str, Any] = Field(default_factory=dict)
    baseline_snapshot: Optional[TelemetrySnapshot] = None
    fault_definition: Optional[FaultDefinition] = None
    fault_injection_record: Optional[FaultInjectionRecord] = None
    remediation_plan: Optional[RemediationPlan] = None
    remediation_execution_record: Optional[RemediationExecutionRecord] = None
    independent_verification_record: Optional[IndependentVerificationRecord] = None
    final_status: str  # BASELINE_FAILED, FAULT_INJECTION_FAILED, FAULT_ACTIVE, EXECUTION_FAILED, VERIFICATION_FAILED, RECOVERED, CLEANUP_FAILED
    raw_command_history: List[CommandExecutionRecord] = Field(default_factory=list)
