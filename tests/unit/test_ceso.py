from app.ceso.service import CESOService

def test_ceso_baseline_state():
    service = CESOService()
    state = service.collect_and_normalize()

    assert state.snapshot_id.startswith("snap-")
    assert state.anomalies_detected is False
    assert len(state.links) == 3
    assert len(state.nodes) == 4
    # Check node metrics
    assert "rtr1" in state.nodes
    assert state.nodes["rtr1"].cpu_utilization_pct < 50.0

def test_ceso_all_fault_profiles():
    service = CESOService()

    # Profile 1: HIGH_LATENCY_CONGESTION
    s1 = service.inject_fault("HIGH_LATENCY_CONGESTION")
    assert s1.anomalies_detected is True
    assert s1.nodes["rtr1"].cpu_utilization_pct > 80.0

    # Profile 2: PACKET_LOSS
    s2 = service.inject_fault("PACKET_LOSS")
    assert s2.anomalies_detected is True
    degraded_link = next(l for l in s2.links if l.source_node == "rtr1" and l.target_node == "rtr2")
    assert degraded_link.packet_loss_pct == 25.0

    # Profile 3: INTERFACE_FAILURE
    s3 = service.inject_fault("INTERFACE_FAILURE")
    assert s3.anomalies_detected is True
    assert s3.interfaces["rtr1-eth1"].is_up is False

    # Profile 4: ROUTING_MISCONFIGURATION
    s4 = service.inject_fault("ROUTING_MISCONFIGURATION")
    assert s4.anomalies_detected is True
    bad_route = next(r for r in s4.routes if r.destination == "10.0.2.0/24")
    assert bad_route.interface == "rtr1-eth0" or bad_route.metric == 999

def test_ceso_reset_simulation():
    service = CESOService()
    service.inject_fault("INTERFACE_FAILURE")
    state = service.reset_simulation()

    assert state.anomalies_detected is False
    assert state.interfaces["rtr1-eth1"].is_up is True
