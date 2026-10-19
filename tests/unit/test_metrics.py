from app.msvs.metrics import EvaluationTracker

def test_metrics_calculation_and_export():
    tracker = EvaluationTracker()

    # 1. Fault injection
    tracker.record_fault_injection("rec-001", "HIGH_LATENCY_CONGESTION", rtt=145.5, loss=15.0)
    tracker.record_detection("rec-001")
    tracker.record_diagnosis("rec-001")
    tracker.record_policy_check("rec-001", is_valid=True)
    tracker.record_approval("rec-001")
    tracker.record_execution("rec-001")
    tracker.record_verification("rec-001", success=True, final_rtt=4.8, final_loss=0.0)

    # 2. Blocked unsafe policy check
    tracker.record_fault_injection("rec-002", "INTERFACE_FAILURE", rtt=999.0, loss=100.0)
    tracker.record_policy_check("rec-002", is_valid=False)

    summary = tracker.compute_summary()
    assert summary.total_incidents == 2
    assert summary.completed_workflows == 1
    assert summary.remediation_success_rate_pct == 100.0
    assert summary.policy_prevention_rate_pct == 50.0

    csv_data = tracker.export_csv()
    assert "Record ID,Fault Profile" in csv_data
    assert "rec-001,HIGH_LATENCY_CONGESTION" in csv_data
