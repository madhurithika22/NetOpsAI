"""
Unit tests for Research V2 capability detector.
"""

from app.research_v2.testbed.capabilities import check_testbed_capabilities


def test_capability_check_format():
    caps = check_testbed_capabilities()
    assert "linux" in caps
    assert "ip_available" in caps
    assert "tc_available" in caps
    assert "ping_available" in caps
    assert "netns_available" in caps
    assert "net_admin_available" in caps
    assert "ready" in caps
    assert isinstance(caps["ready"], bool)
