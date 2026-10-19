from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_incident_workflow():
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # 2. Reset simulation to baseline healthy state
    res = client.post("/api/v1/simulation/reset")
    assert res.status_code == 200

    # 3. CESO: Get baseline state
    res = client.get("/api/v1/ceso/state")
    assert res.status_code == 200
    state = res.json()
    assert state["anomalies_detected"] is False

    # 4. CADD: Run diagnosis on baseline -> HEALTHY
    res = client.post("/api/v1/cadd/diagnose")
    assert res.status_code == 200
    diag_data = res.json()
    assert diag_data["diagnostic_report"]["fault_type"] == "HEALTHY"

    # 5. Simulation: Inject HIGH_LATENCY_CONGESTION fault
    res = client.post("/api/v1/simulation/inject-fault", json={"fault_type": "HIGH_LATENCY_CONGESTION"})
    assert res.status_code == 200
    fault_state = res.json()
    assert fault_state["anomalies_detected"] is True

    # 6. CADD: Run diagnosis -> HIGH_LATENCY_CONGESTION detected with ActionPlan
    res = client.post("/api/v1/cadd/diagnose")
    assert res.status_code == 200
    fault_diag = res.json()
    report = fault_diag["diagnostic_report"]
    plan = fault_diag["action_plan"]

    assert report["fault_type"] == "HIGH_LATENCY_CONGESTION"
    assert len(report["evidence_chain"]) >= 1
    assert plan["requires_approval"] is True

    # 7. MSVS: Validate action plan
    res = client.post("/api/v1/msvs/validate", json={"action_plan": plan, "diagnosis_summary": report["explanation_summary"]})
    assert res.status_code == 200
    val_res = res.json()
    assert val_res["is_valid"] is True

    # 8. MSVS: Fetch pending approvals
    res = client.get("/api/v1/msvs/approvals")
    assert res.status_code == 200
    approvals = res.json()
    assert len(approvals) >= 1
    matching_appr = next(a for a in approvals if a["plan_id"] == plan["plan_id"])
    appr_id = matching_appr["approval_id"]

    # 9. MSVS: Approve request
    res = client.post(f"/api/v1/msvs/approvals/{appr_id}/approve")
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 10. MSVS: Execute plan
    plan_id = plan["plan_id"]
    res = client.post(f"/api/v1/msvs/execute/{plan_id}")
    assert res.status_code == 200
    exec_log = res.json()
    assert exec_log["status"] == "SUCCESS"
    assert exec_log["post_verification_passed"] is True

    # 11. CESO: Verify state post-remediation
    res = client.get("/api/v1/ceso/state")
    assert res.status_code == 200
    post_state = res.json()
    assert post_state["anomalies_detected"] is False

    # 12. MSVS: Verify audit log
    res = client.get("/api/v1/msvs/audit-logs")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1
