"""
Unit tests for ControlledExecutor and privileged execution mechanics.
"""

import sys
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import CommandExecutionRecord


def test_unprivileged_command_construction():
    cmd = ["ip", "netns", "list"]
    eff = ControlledExecutor.construct_effective_command(cmd, namespace=None, privileged=False)
    assert eff == ["ip", "netns", "list"]


def test_privileged_command_construction():
    cmd = ["ip", "netns", "add", "test-ns"]
    eff = ControlledExecutor.construct_effective_command(cmd, namespace=None, privileged=True)
    assert eff == ["sudo", "-n", "ip", "netns", "add", "test-ns"]


def test_namespace_and_privileged_command_construction():
    cmd = ["tc", "qdisc", "add", "dev", "veth-r1-r2", "root", "netem", "delay", "150ms"]
    eff = ControlledExecutor.construct_effective_command(cmd, namespace="rns-router-1", privileged=True)
    assert eff == ["sudo", "-n", "ip", "netns", "exec", "rns-router-1", "tc", "qdisc", "add", "dev", "veth-r1-r2", "root", "netem", "delay", "150ms"]


def test_evidence_record_fields_canonical_schema():
    py_cmd = [sys.executable, "-c", "print('hello')"]
    rec = ControlledExecutor.run_command(py_cmd, privileged=False)
    assert rec.original_command == py_cmd
    assert rec.effective_command == py_cmd
    assert rec.privileged is False
    assert rec.return_code == 0
    assert hasattr(rec, "return_code")
    assert "hello" in rec.stdout
    assert rec.duration_ms >= 0.0


def test_privileged_evidence_record_fields():
    orig = ["ip", "link", "set", "dev", "veth1", "up"]
    eff = ControlledExecutor.construct_effective_command(orig, namespace="ns1", privileged=True)
    assert orig == ["ip", "link", "set", "dev", "veth1", "up"]
    assert eff == ["sudo", "-n", "ip", "netns", "exec", "ns1", "ip", "link", "set", "dev", "veth1", "up"]


def test_no_shell_true_flag():
    py_cmd = [sys.executable, "-c", "import sys; print(sys.executable)"]
    rec = ControlledExecutor.run_command(py_cmd, privileged=False)
    assert rec.return_code == 0
    assert rec.effective_command[0] == sys.executable
