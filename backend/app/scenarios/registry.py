from typing import Dict, List, Optional
from app.scenarios.base import ScenarioDefinition
from app.scenarios.case01_enterprise import get_case01_enterprise_scenario, generate_case01_telemetry
from app.scenarios.case02_wan import get_case02_wan_scenario, generate_case02_telemetry
from app.scenarios.case03_datacenter import get_case03_datacenter_scenario, generate_case03_telemetry
from app.scenarios.case04_hybrid import get_case04_hybrid_scenario, generate_case04_telemetry
from app.ceso.simulator import NetworkStateSimulator
from app.models.ceso_models import NetworkState

class ScenarioRegistry:
    def __init__(self):
        self._scenarios: Dict[str, ScenarioDefinition] = {}
        self._telemetry_generators = {}
        self.active_scenario_id: Optional[str] = None
        self.active_fault: str = "NONE"
        self.legacy_simulator = NetworkStateSimulator()
        self._register_defaults()

    def _register_defaults(self):
        # Primary research scenarios
        c1 = get_case01_enterprise_scenario()
        c2 = get_case02_wan_scenario()
        c3 = get_case03_datacenter_scenario()
        c4 = get_case04_hybrid_scenario()

        self._scenarios[c1.scenario_id] = c1
        self._scenarios[c2.scenario_id] = c2
        self._scenarios[c3.scenario_id] = c3
        self._scenarios[c4.scenario_id] = c4

        self._telemetry_generators[c1.scenario_id] = generate_case01_telemetry
        self._telemetry_generators[c2.scenario_id] = generate_case02_telemetry
        self._telemetry_generators[c3.scenario_id] = generate_case03_telemetry
        self._telemetry_generators[c4.scenario_id] = generate_case04_telemetry

    def list_scenarios(self) -> List[ScenarioDefinition]:
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDefinition]:
        return self._scenarios.get(scenario_id)

    def load_scenario(self, scenario_id: str) -> ScenarioDefinition:
        if scenario_id not in self._scenarios:
            raise ValueError(f"Scenario '{scenario_id}' not found in registry. Available: {list(self._scenarios.keys())}")
        self.active_scenario_id = scenario_id
        self.active_fault = "NONE"
        return self._scenarios[scenario_id]

    def inject_fault(self, scenario_id: Optional[str] = None, fault_type: Optional[str] = None) -> str:
        target_scenario = scenario_id or self.active_scenario_id
        scenario = self.get_scenario(target_scenario)
        if not scenario:
            raise ValueError(f"Scenario '{target_scenario}' not found.")
        
        selected_fault = fault_type or scenario.fault_definition.fault_type
        self.active_scenario_id = target_scenario
        self.active_fault = selected_fault
        return selected_fault

    def reset_scenario(self, scenario_id: Optional[str] = None):
        if scenario_id:
            self.active_scenario_id = scenario_id
        else:
            self.active_scenario_id = None
        self.active_fault = "NONE"
        self.legacy_simulator.reset()

    def generate_telemetry(self, scenario_id: Optional[str] = None, fault_type: Optional[str] = None) -> NetworkState:
        sc_id = scenario_id or self.active_scenario_id
        f_type = fault_type if fault_type is not None else self.active_fault

        if sc_id in self._telemetry_generators:
            telemetry_fn = self._telemetry_generators[sc_id]
            active_f = f_type if f_type != "NONE" else "NONE"
            sc_def = self.get_scenario(sc_id)
            if active_f != "NONE" and active_f not in [sc_def.fault_definition.fault_type]:
                active_f = sc_def.fault_definition.fault_type

            return telemetry_fn(active_f)
        else:
            if f_type != "NONE":
                self.legacy_simulator.inject_fault(f_type)
            else:
                self.legacy_simulator.reset()
            return self.legacy_simulator.generate_snapshot()

scenario_registry = ScenarioRegistry()
