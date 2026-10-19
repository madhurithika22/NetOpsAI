import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_run_benchmark_simulated():
    response = client.post("/api/v1/evaluation/run-benchmark", json={
        "environment": "SIMULATED",
        "scenarios": ["HIGH_LATENCY_CONGESTION", "HEALTHY_BASELINE"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["environment"] == "SIMULATED"
    assert data["total_runs"] >= 2
    assert "accuracy" in data["metrics"]
    assert data["metrics"]["accuracy"]["status"] == "MEASURED"


def test_api_get_experiments_list():
    response = client.get("/api/v1/evaluation/experiments?environment=SIMULATED")
    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)


def test_api_get_metrics_summary():
    response = client.get("/api/v1/evaluation/metrics-summary?environment=SIMULATED")
    assert response.status_code == 200
    summary = response.json()
    assert summary["environment"] == "SIMULATED"


def test_api_get_aiops2020_report():
    response = client.get("/api/v1/evaluation/aiops2020/report")
    assert response.status_code == 200
    report = response.json()
    assert report["total_records"] > 0
    assert "label_mapping_counts" in report


def test_api_export_json_and_csv():
    res_json = client.get("/api/v1/evaluation/export/json")
    assert res_json.status_code == 200
    assert res_json.headers["content-type"].startswith("application/json")

    res_csv = client.get("/api/v1/evaluation/export/csv")
    assert res_csv.status_code == 200
    assert res_csv.headers["content-type"].startswith("text/csv")
