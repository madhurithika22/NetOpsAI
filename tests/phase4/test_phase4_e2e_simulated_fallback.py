from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_environment_api_and_mode_switching():
    # 1. Query environment info
    res = client.get("/api/v1/simulation/environment")
    assert res.status_code == 200
    env_info = res.json()
    assert "mode" in env_info
    assert "platform" in env_info

    # 2. Switch to LINUX_TESTBED mode
    res = client.post("/api/v1/simulation/environment/switch", json={"mode": "LINUX_TESTBED"})
    assert res.status_code == 200
    assert res.json()["active_mode"] == "LINUX_TESTBED"

    # 3. Query state under LINUX_TESTBED mode
    res = client.get("/api/v1/ceso/state")
    assert res.status_code == 200
    state = res.json()
    assert state["topology_id"] == "netops-linux-testbed"

    # 4. Run Phase 4 benchmark under LINUX_TESTBED mode
    res = client.post("/api/v1/simulation/benchmark/run", json={"iterations_per_fault": 2, "environment_mode": "LINUX_TESTBED"})
    assert res.status_code == 200
    report = res.json()
    assert report["environment_mode"] == "LINUX_TESTBED"
    assert report["total_trials"] == 8

    # 5. Switch back to SIMULATED mode
    res = client.post("/api/v1/simulation/environment/switch", json={"mode": "SIMULATED"})
    assert res.status_code == 200
    assert res.json()["active_mode"] == "SIMULATED"
