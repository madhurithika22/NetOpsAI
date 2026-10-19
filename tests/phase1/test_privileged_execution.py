"""
Real Linux Network Namespace Privileged Execution Integration Test.

Runs ONLY on Linux hosts with passwordless sudo / CAP_NET_ADMIN capabilities.
Skipped automatically on Windows / unsupported platforms without faking success.
"""

import sys
import uuid
import pytest
from app.research_v2.testbed.capabilities import check_testbed_capabilities
from app.research_v2.testbed.executor import ControlledExecutor

caps = check_testbed_capabilities()
REASON_NOT_LINUX = f"Privileged netns execution test requires Linux & passwordless sudo (host: {sys.platform}, ready: {caps['ready']})"


@pytest.mark.skipif(not caps["ready"], reason=REASON_NOT_LINUX)
def test_sudo_passwordless_netns_lifecycle():
    """
    Real test verifying:
    1. sudo -n ip netns add <temp_ns>
    2. sudo -n ip netns exec <temp_ns> ip link
    3. sudo -n ip netns del <temp_ns>
    """
    temp_ns = f"netops-test-{uuid.uuid4().hex[:6]}"

    try:
        # 1. Add namespace with privileged=True
        rec_add = ControlledExecutor.run_command(["ip", "netns", "add", temp_ns], privileged=True, check=True)
        assert rec_add.return_code == 0
        assert rec_add.effective_command == ["sudo", "-n", "ip", "netns", "add", temp_ns]

        # 2. Exec ip link inside namespace with privileged=True
        rec_link = ControlledExecutor.run_command(["ip", "link"], namespace=temp_ns, privileged=True, check=True)
        assert rec_link.return_code == 0
        assert rec_link.effective_command == ["sudo", "-n", "ip", "netns", "exec", temp_ns, "ip", "link"]
        assert "lo" in rec_link.stdout

    finally:
        # 3. Del namespace with privileged=True
        rec_del = ControlledExecutor.run_command(["ip", "netns", "del", temp_ns], privileged=True)
        assert rec_del.return_code == 0
        assert rec_del.effective_command == ["sudo", "-n", "ip", "netns", "del", temp_ns]
