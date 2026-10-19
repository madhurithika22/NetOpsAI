import os
import sys
import pytest
from app.testbed.faults import testbed_fault_injector
from app.testbed.manager import testbed_manager

def is_root_linux_netns_active() -> bool:
    """Helper to detect if pytest is running on Linux with root/sudo privileges and active netns capabilities."""
    if not sys.platform.startswith("linux"):
        return False
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        return False
    return True

def test_testbed_fault_injection_validated_scenario():
    """Unit test: Validates fault injector parameter safety and logging without requiring active Linux root namespaces."""
    log = testbed_fault_injector.inject_testbed_fault("HIGH_LATENCY_CONGESTION")
    assert log.fault_type == "HIGH_LATENCY_CONGESTION"
    assert log.status == "SUCCESS"
    testbed_fault_injector.reset_testbed_faults()

def test_testbed_fault_safety_rejection_protected_host_interface():
    """Safety test: Attempting to target protected host interface eth0 MUST raise PermissionError on all platforms."""
    with pytest.raises(PermissionError) as exc_info:
        testbed_fault_injector.inject_testbed_fault(
            fault_type="INTERFACE_FAILURE",
            target_ns="netops-rtr1",
            target_iface="eth0"  # Protected host interface!
        )
    assert "CRITICAL SAFETY VIOLATION" in str(exc_info.value)

def test_testbed_fault_safety_rejection_unowned_namespace():
    """Safety test: Attempting to target unowned namespace 'root' MUST raise PermissionError on all platforms."""
    with pytest.raises(PermissionError) as exc_info:
        testbed_fault_injector.inject_testbed_fault(
            fault_type="HIGH_LATENCY_CONGESTION",
            target_ns="root",  # Unowned namespace!
            target_iface="veth-r1-r2"
        )
    assert "CRITICAL SAFETY VIOLATION" in str(exc_info.value)

@pytest.mark.skipif(not is_root_linux_netns_active(), reason="Real Linux namespace execution requires root/sudo privileges (geteuid == 0)")
def test_real_linux_testbed_fault_injection_lifecycle():
    """Integration test: Exercises actual Linux netns tc qdisc fault injection on a live created Linux testbed."""
    # 1. Initialize real Linux testbed
    status = testbed_manager.create_testbed()
    assert status.is_created is True

    try:
        # 2. Inject real tc qdisc fault on live netops-rtr1 namespace
        log = testbed_fault_injector.inject_testbed_fault("HIGH_LATENCY_CONGESTION")
        assert log.status == "SUCCESS"
        assert "tc qdisc add dev veth-r1-r2" in log.command_executed

        # 3. Reset fault
        testbed_fault_injector.reset_testbed_faults()
    finally:
        # 4. Clean teardown
        testbed_manager.teardown_testbed()
