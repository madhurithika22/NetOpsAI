from app.msvs.benchmark import benchmark_runner

def test_experiment_3_safety_validation():
    """
    Experiment 3: Test management interface protection, unauthorized commands, unapproved & rejected executions.
    """
    report = benchmark_runner.run_all_experiments(iterations_per_fault=2)

    assert report.exp3_safety_prevention_rate_pct == 100.0
    assert benchmark_runner._test_safety_protected_interface() is True
    assert benchmark_runner._test_safety_unwhitelisted_command() is True
    assert benchmark_runner._test_safety_unapproved_execution_blocked() is True
    assert benchmark_runner._test_safety_rejected_execution_blocked() is True
