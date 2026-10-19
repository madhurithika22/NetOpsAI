from typing import Optional, Dict
from app.models.ceso_models import NetworkState
from app.ceso.provider import TelemetryProvider, SimulatedTelemetryProvider, LinuxTestbedTelemetryProvider
from app.scenarios.registry import scenario_registry
from app.msvs.metrics import evaluation_tracker

class CESOService:
    """
    Context Extraction and State Observation Service.
    Supports dynamic provider switching (Simulated vs Linux Testbed) and active scenario integration.
    """
    def __init__(self):
        self.providers: Dict[str, TelemetryProvider] = {
            "SIMULATED": SimulatedTelemetryProvider(),
            "LINUX_TESTBED": LinuxTestbedTelemetryProvider()
        }
        self.active_mode: str = "SIMULATED"
        self.latest_state: Optional[NetworkState] = None
        self.active_record_id: Optional[str] = None
        self.active_scenario_id: Optional[str] = None

    @property
    def current_provider(self) -> TelemetryProvider:
        return self.providers[self.active_mode]

    def set_provider_mode(self, mode: str) -> str:
        mode_upper = mode.upper()
        if mode_upper not in self.providers:
            raise ValueError(f"Unknown provider mode: '{mode}'. Allowed: {list(self.providers.keys())}")
        self.active_mode = mode_upper
        self.collect_and_normalize()
        return self.active_mode

    def get_provider_mode(self) -> str:
        return self.active_mode

    def load_scenario(self, scenario_id: str, fault_type: Optional[str] = None) -> NetworkState:
        scenario_registry.load_scenario(scenario_id)
        self.active_scenario_id = scenario_id
        if fault_type:
            scenario_registry.inject_fault(scenario_id, fault_type)
        return self.collect_and_normalize()

    def collect_state(self) -> NetworkState:
        return self.collect_and_normalize()

    def collect_and_normalize(self) -> NetworkState:
        if self.active_scenario_id:
            snapshot = scenario_registry.generate_telemetry(self.active_scenario_id)
        else:
            snapshot = self.current_provider.collect_telemetry()

        self.latest_state = snapshot
        if snapshot.anomalies_detected and self.active_record_id:
            evaluation_tracker.record_detection(self.active_record_id)
        return snapshot

    def get_latest_state(self) -> NetworkState:
        if not self.latest_state:
            return self.collect_and_normalize()
        return self.latest_state

    def inject_fault(self, fault_type: str = "HIGH_LATENCY_CONGESTION") -> NetworkState:
        if self.active_scenario_id:
            scenario_registry.inject_fault(self.active_scenario_id, fault_type)
            state = self.collect_and_normalize()
        else:
            state = self.current_provider.inject_fault(fault_type)
            self.latest_state = state

        rtt = state.links[1].rtt_ms if len(state.links) > 1 else 0.0
        loss = state.links[1].packet_loss_pct if len(state.links) > 1 else 0.0

        rec_id = f"rec-{snapshot_id_clean(state.snapshot_id)}"
        self.active_record_id = rec_id
        evaluation_tracker.record_fault_injection(rec_id, fault_type, rtt, loss)
        evaluation_tracker.record_detection(rec_id)
        return state

    def reset_simulation(self) -> NetworkState:
        self.active_scenario_id = None
        scenario_registry.reset_scenario()
        state = self.current_provider.reset()
        self.latest_state = state
        self.active_record_id = None
        return state

def snapshot_id_clean(snap_id: str) -> str:
    return snap_id.replace("snap-", "")

# Singleton service instance
ceso_service = CESOService()
