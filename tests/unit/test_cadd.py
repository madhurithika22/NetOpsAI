from app.ceso.service import CESOService
from app.cadd.service import CADDService

def test_cadd_healthy_state_diagnosis():
    ceso = CESOService()
    cadd = CADDService()

    state = ceso.collect_and_normalize()
    report, plan = cadd.diagnose_network_state(state)

    assert report.fault_type == "HEALTHY"
    assert report.confidence_score == 1.0
    assert len(report.evidence_chain) == 0
    assert len(plan.proposed_actions) == 0
    assert plan.requires_approval is False

def test_cadd_high_latency_diagnosis():
    ceso = CESOService()
    cadd = CADDService()

    state = ceso.inject_fault("HIGH_LATENCY_CONGESTION")
    report, plan = cadd.diagnose_network_state(state)

    assert report.fault_type == "HIGH_LATENCY_CONGESTION"
    assert report.severity == "HIGH"
    assert "rtr1<->rtr2" in report.impacted_elements
    assert len(report.evidence_chain) >= 1
    assert report.evidence_chain[0].rule_id == "RULE_HIGH_LATENCY_CONGESTION"

def test_cadd_packet_loss_diagnosis():
    ceso = CESOService()
    cadd = CADDService()

    state = ceso.inject_fault("PACKET_LOSS")
    report, plan = cadd.diagnose_network_state(state)

    assert report.fault_type == "PACKET_LOSS"
    assert report.severity == "HIGH"
    assert report.evidence_chain[0].rule_id == "RULE_PACKET_LOSS"

def test_cadd_interface_failure_diagnosis():
    ceso = CESOService()
    cadd = CADDService()

    state = ceso.inject_fault("INTERFACE_FAILURE")
    report, plan = cadd.diagnose_network_state(state)

    assert report.fault_type == "INTERFACE_FAILURE"
    assert report.severity == "CRITICAL"
    assert report.evidence_chain[0].rule_id == "RULE_INTERFACE_DOWN"
    assert plan.proposed_actions[0].command_type == "SET_INTERFACE_STATE"

def test_cadd_routing_misconfiguration_diagnosis():
    ceso = CESOService()
    cadd = CADDService()

    state = ceso.inject_fault("ROUTING_MISCONFIGURATION")
    report, plan = cadd.diagnose_network_state(state)

    assert report.fault_type == "ROUTING_MISCONFIGURATION"
    assert report.evidence_chain[0].rule_id == "RULE_ROUTING_BLACKHOLE"
    assert plan.proposed_actions[0].command_type == "RESTORE_ROUTING_TABLE"
