"""
Capability Detector for Linux Network Namespace Research Testbed.

Verifies host OS, iproute2, tc netem, ping, network namespace support,
and controlled privileged execution via 'sudo -n'.
If required capabilities are missing, research execution fails explicitly.
"""

import sys
import shutil
import subprocess
from typing import Dict, Any


def check_testbed_capabilities() -> Dict[str, Any]:
    """
    Checks if host environment supports Linux network namespace research testbed.
    Returns structured capability breakdown.
    """
    is_linux = sys.platform.startswith("linux")
    ip_cmd = shutil.which("ip") is not None
    tc_cmd = shutil.which("tc") is not None
    ping_cmd = shutil.which("ping") is not None
    sudo_cmd = shutil.which("sudo") is not None

    netns_available = False
    net_admin_available = False
    privileged_executor_available = False
    netns_error = ""

    if is_linux and ip_cmd:
        # Check unprivileged netns list
        try:
            res = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                netns_available = True
            else:
                netns_error = res.stderr.strip() or f"exit code {res.returncode}"
        except Exception as e:
            netns_error = str(e)

        # Check if Python process itself possesses effective CAP_NET_ADMIN (unprivileged process = False)
        try:
            res = subprocess.run(["ip", "netns", "add", "netops_proc_cap_test"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                net_admin_available = True
                subprocess.run(["ip", "netns", "del", "netops_proc_cap_test"], capture_output=True, text=True, timeout=5)
            else:
                net_admin_available = False
        except Exception:
            net_admin_available = False

        # Check controlled privileged executor (sudo -n)
        if sudo_cmd:
            try:
                res_true = subprocess.run(["sudo", "-n", "true"], capture_output=True, text=True, timeout=5)
                if res_true.returncode == 0:
                    # Verify sudo -n netns creation
                    res_ns = subprocess.run(["sudo", "-n", "ip", "netns", "add", "netops_sudo_cap_test"], capture_output=True, text=True, timeout=5)
                    if res_ns.returncode == 0:
                        privileged_executor_available = True
                        subprocess.run(["sudo", "-n", "ip", "netns", "del", "netops_sudo_cap_test"], capture_output=True, text=True, timeout=5)
                    else:
                        netns_error = f"sudo -n ip netns add failed: {res_ns.stderr.strip()}"
                else:
                    netns_error = f"sudo -n true failed: {res_true.stderr.strip() or 'sudo requires password'}"
            except Exception as e:
                netns_error = str(e)

    ready = is_linux and ip_cmd and tc_cmd and ping_cmd and netns_available and (net_admin_available or privileged_executor_available)

    return {
        "linux": is_linux,
        "platform": sys.platform,
        "ip_available": ip_cmd,
        "tc_available": tc_cmd,
        "ping_available": ping_cmd,
        "sudo_available": sudo_cmd,
        "netns_available": netns_available,
        "net_admin_available": net_admin_available,
        "privileged_executor_available": privileged_executor_available,
        "netns_error": netns_error if not ready else None,
        "ready": ready
    }
