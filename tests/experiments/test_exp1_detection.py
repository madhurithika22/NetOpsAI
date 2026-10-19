from app.msvs.benchmark import benchmark_runner

def test_experiment_1_fault_detection_performance():
    """
    Experiment 1: Measure detection latency & diagnostic execution time across all 4 fault profiles.
    """
    report = benchmark_runner.run_all_experiments(iterations_per_fault=3)

    assert report.total_trials == 12  # 4 profiles * 3 iterations
    assert report.exp1_detection_latency.mean >= 0.0
    assert report.exp1_diagnostic_execution_time.mean >= 0.0
    assert report.exp1_diagnostic_execution_time.mean < 100.0  # Must be fast (<100ms)

    # Verify each trial records valid latency
    for trial in report.trial_details:
        assert trial.detection_latency_ms >= 0.0
        assert trial.diagnostic_execution_time_ms >= 0.0
