import pytest
from app.scenarios.registry import scenario_registry

def test_all_four_scenarios_exist():
    scenarios = scenario_registry.list_scenarios()
    sc_ids = [sc.scenario_id for sc in scenarios]
    assert "CASE_01" in sc_ids
    assert "CASE_02" in sc_ids
    assert "CASE_03" in sc_ids
    assert "CASE_04" in sc_ids

def test_scenario_topology_node_link_counts():
    c1 = scenario_registry.get_scenario("CASE_01")
    c2 = scenario_registry.get_scenario("CASE_02")
    c3 = scenario_registry.get_scenario("CASE_03")
    c4 = scenario_registry.get_scenario("CASE_04")

    assert c1.target_node_count >= 18 and c1.target_node_count <= 22
    assert c2.target_node_count >= 25 and c2.target_node_count <= 30
    assert c3.target_node_count >= 30 and c3.target_node_count <= 40
    assert c4.target_node_count >= 40 and c4.target_node_count <= 50

def test_unique_node_and_link_ids():
    for sc in scenario_registry.list_scenarios():
        node_ids = [n.id for n in sc.nodes]
        link_ids = [l.id for l in sc.links]
        assert len(node_ids) == len(set(node_ids)), f"Duplicate node IDs in {sc.scenario_id}"
        assert len(link_ids) == len(set(link_ids)), f"Duplicate link IDs in {sc.scenario_id}"

def test_fault_injection_and_reset():
    c1 = scenario_registry.load_scenario("CASE_01")
    assert c1.scenario_id == "CASE_01"

    # Baseline healthy
    baseline_telemetry = scenario_registry.generate_telemetry("CASE_01", "NONE")
    assert not baseline_telemetry.anomalies_detected

    # Inject fault
    active_fault = scenario_registry.inject_fault("CASE_01")
    fault_telemetry = scenario_registry.generate_telemetry("CASE_01", active_fault)
    assert fault_telemetry.anomalies_detected

    # Reset
    scenario_registry.reset_scenario("CASE_01")
    reset_telemetry = scenario_registry.generate_telemetry("CASE_01", "NONE")
    assert not reset_telemetry.anomalies_detected
