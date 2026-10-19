from app.msvs.benchmark import benchmark_runner

def test_experiment_2_remediation_effectiveness():
    """
    Experiment 2: Compare before/after metrics and calculate recovery time and success rate.
    """
    report = benchmark_runner.run_all_experiments(iterations_per_fault=3)

    assert report.exp2_remediation_success_rate_pct == 100.0
    assert report.exp2_recovery_time.mean > 0.0

    for trial in report.trial_details:
        assert trial.remediation_success is True
        assert trial.status == "SUCCESS"
        # Verify post-remediation RTT improved compared to fault state
        if trial.fault_profile == "HIGH_LATENCY_CONGESTION":
            assert trial.fault_rtt_ms > 100.0
            assert trial.post_rtt_ms < 10.0
