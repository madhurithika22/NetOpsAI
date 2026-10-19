from app.msvs.benchmark import benchmark_runner

def test_experiment_4_robustness():
    """
    Experiment 4: Test incomplete telemetry, rapid fault injection cycles, and failed workflow metric isolation.
    """
    report = benchmark_runner.run_all_experiments(iterations_per_fault=2)

    assert report.exp4_robustness_pass_rate_pct == 100.0
    assert benchmark_runner._test_robustness_incomplete_telemetry() is True
    assert benchmark_runner._test_robustness_rapid_fault_cycles() is True
    assert benchmark_runner._test_robustness_failed_workflow_metric_isolation() is True
