import pytest
from datetime import datetime, timezone
from app.adapters.aiops2020_adapter import AIOps2020Adapter
from app.evaluation.models import EvaluationEnvironment


def test_excel_time_to_datetime_conversion():
    excel_val = 43973.0
    dt = AIOps2020Adapter.excel_time_to_datetime(excel_val)
    assert dt.year == 2020
    assert dt.month == 5
    assert dt.day == 23


def test_label_mapping_defensibility():
    adapter = AIOps2020Adapter()
    
    norm, mapped, supported, reason = adapter.normalize_label_and_domain("DCOS容器", "网络延迟")
    assert supported is True
    assert mapped == "HIGH_LATENCY_CONGESTION"

    norm, mapped, supported, reason = adapter.normalize_label_and_domain("数据库oracle", "数据库关监听")
    assert supported is False
    assert mapped == "UNSUPPORTED_DB_FAULT"
    assert "Database listener failure" in reason

    norm, mapped, supported, reason = adapter.normalize_label_and_domain("数据库oracle", "表空间满")
    assert supported is False
    assert mapped == "UNSUPPORTED_DB_FAULT"
    assert "Storage space capacity" in reason


def test_generate_experiment_runs_stream():
    adapter = AIOps2020Adapter()
    runs = list(adapter.generate_experiment_runs())
    assert len(runs) > 0
    first_run = runs[0]
    assert first_run.environment == EvaluationEnvironment.AIOPS_2020
    assert first_run.run_id.startswith("run-aiops2020-")


def test_quality_report_generation():
    adapter = AIOps2020Adapter()
    report = adapter.generate_quality_report()
    assert report.total_records > 0
    assert report.usable_records + report.excluded_records == report.total_records
    assert report.adapter_version == "1.0.0"
