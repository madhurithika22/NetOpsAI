from app.msvs.benchmark import benchmark_runner

def test_experiment_5_results_export():
    """
    Experiment 5: Store individual experiment records and export results to CSV & JSON format.
    """
    report = benchmark_runner.run_all_experiments(iterations_per_fault=2)
    assert report.total_trials == 8

    # Verify JSON serialization
    json_data = report.model_dump_json()
    assert "exp1_detection_latency" in json_data
    assert "trial_details" in json_data

    # Verify CSV export
    csv_data = benchmark_runner.export_benchmark_csv(report)
    assert "Trial ID,Environment Mode,Fault Profile,Iteration" in csv_data
    assert "HIGH_LATENCY_CONGESTION" in csv_data
