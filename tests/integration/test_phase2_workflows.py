from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_all_fault_profiles_e2e():
    fault_profiles = [
        "HIGH_LATENCY_CONGESTION",
        "PACKET_LOSS",
        "INTERFACE_FAILURE",
        "ROUTING_MISCONFIGURATION"
    ]

    for fault in fault_profiles:
        # Reset baseline
        res = client.post("/api/v1/simulation/reset")
        assert res.status_code == 200

        # Inject fault
        res = client.post("/api/v1/simulation/inject-fault", json={"fault_type": fault})
        assert res.status_code == 200
        state = res.json()
        assert state["anomalies_detected"] is True

        # Run diagnosis
        res = client.post("/api/v1/cadd/diagnose")
        assert res.status_code == 200
        diag = res.json()
        report = diag["diagnostic_report"]
        plan = diag["action_plan"]

        assert report["fault_type"] == fault
        assert len(report["evidence_chain"]) >= 1

        # Validate action plan
        res = client.post("/api/v1/msvs/validate", json={"action_plan": plan, "diagnosis_summary": report["explanation_summary"]})
        assert res.status_code == 200
        val_res = res.json()
        assert val_res["is_valid"] is True

        # Approve pending request
        res = client.get("/api/v1/msvs/approvals")
        assert res.status_code == 200
        approvals = res.json()
        assert len(approvals) >= 1
        appr_id = approvals[-1]["approval_id"]

        res = client.post(f"/api/v1/msvs/approvals/{appr_id}/approve")
        assert res.status_code == 200

        # Execute
        res = client.post(f"/api/v1/msvs/execute/{plan['plan_id']}")
        assert res.status_code == 200
        exec_log = res.json()
        assert exec_log["status"] == "SUCCESS"

def test_metrics_api_and_csv_export():
    res = client.get("/api/v1/msvs/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert "total_incidents" in metrics
    assert "remediation_success_rate_pct" in metrics

    res = client.get("/api/v1/msvs/metrics/export-csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Record ID,Fault Profile" in res.text
