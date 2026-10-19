import os
import sys
import pytest
from app.testbed.manager import testbed_manager
from app.testbed.config import get_default_testbed_config

def is_root_linux_netns_active() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        return False
    return True

def test_testbed_ownership_validation():
    # Valid NetOps owned resources
    assert testbed_manager.is_owned_resource("netops-hosta") is True
    assert testbed_manager.is_owned_resource("netops-rtr1") is True
    assert testbed_manager.is_owned_resource("veth-r1-r2") is True

    # Protected host resources MUST be rejected
    assert testbed_manager.is_owned_resource("eth0") is False
    assert testbed_manager.is_owned_resource("wlan0") is False
    assert testbed_manager.is_owned_resource("lo") is False
    assert testbed_manager.is_owned_resource("mgmt0") is False
    assert testbed_manager.is_owned_resource("docker0") is False

def test_testbed_default_topology_config():
    config = get_default_testbed_config()
    assert len(config.namespaces) == 4
    assert len(config.veth_pairs) == 3
    assert "netops-hosta" in config.namespaces
    assert "netops-rtr1" in config.namespaces
    assert config.namespaces["netops-rtr1"].is_router is True

def test_testbed_status_query():
    status = testbed_manager.get_status()
    assert hasattr(status, "is_platform_supported")
    assert hasattr(status, "is_created")
    assert hasattr(status, "is_connected")
    assert isinstance(status.message, str)

@pytest.mark.skipif(not is_root_linux_netns_active(), reason="Real Linux namespace creation requires root/sudo privileges (geteuid == 0)")
def test_real_linux_testbed_creation_and_teardown():
    """Integration test: Creates full 4-node Linux netns topology, tests ping connectivity, and tears down safely."""
    try:
        status = testbed_manager.create_testbed()
        assert status.is_created is True
        assert status.is_connected is True
        assert len(status.active_namespaces) == 4
    finally:
        teardown_status = testbed_manager.teardown_testbed()
        assert teardown_status.is_created is False
