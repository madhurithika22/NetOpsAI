"""
Controlled Shell & Namespace Executor for NetOps Research V2.

Executes commands in target network namespaces safely using argument lists.
Supports explicit controlled privilege escalation via 'sudo -n'.
Strictly prohibits shell=True, string interpolation, and fallback to simulation.
"""

import time
import subprocess
from datetime import datetime, timezone
from typing import List, Optional
from app.research_v2.testbed.models import CommandExecutionRecord
from app.research_v2.testbed.exceptions import ResearchTestbedError


class ControlledExecutor:
    """
    Controlled subprocess executor for Linux network namespace commands.
    """

    @staticmethod
    def construct_effective_command(
        cmd: List[str],
        namespace: Optional[str] = None,
        privileged: bool = False
    ) -> List[str]:
        """
        Constructs safe argv list for subprocess execution.
        """
        orig = list(cmd)
        if privileged:
            if namespace:
                return ["sudo", "-n", "ip", "netns", "exec", namespace] + orig
            else:
                return ["sudo", "-n"] + orig
        else:
            if namespace:
                return ["ip", "netns", "exec", namespace] + orig
            else:
                return orig

    @classmethod
    def run_command(
        cls,
        cmd: List[str],
        namespace: Optional[str] = None,
        privileged: bool = False,
        timeout_seconds: float = 15.0,
        check: bool = False
    ) -> CommandExecutionRecord:
        """
        Executes a command list using safe argument vectors.
        """
        original_command = list(cmd)
        effective_command = cls.construct_effective_command(cmd, namespace, privileged)

        started_at = datetime.now(timezone.utc)
        start_t = time.perf_counter()

        try:
            # NO shell=True
            res = subprocess.run(
                effective_command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=False
            )
            end_t = time.perf_counter()
            finished_at = datetime.now(timezone.utc)
            duration_ms = round((end_t - start_t) * 1000.0, 2)

            # Check if sudo failed due to password prompt
            is_sudo_password_error = (
                privileged and (
                    "a password is required" in res.stderr.lower() or
                    "password" in res.stderr.lower() or
                    "sudo: a password is required" in res.stderr.lower()
                )
            )

            record = CommandExecutionRecord(
                original_command=original_command,
                effective_command=effective_command,
                privileged=privileged,
                namespace=namespace,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                return_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr
            )

            if is_sudo_password_error:
                err_msg = f"Privileged execution failed: 'sudo -n' requires password ({res.stderr.strip()})"
                if check:
                    raise ResearchTestbedError(err_msg)

            if check and res.returncode != 0:
                err_msg = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
                raise ResearchTestbedError(
                    f"Command execution failed ('{' '.join(effective_command)}'): {err_msg}"
                )

            return record

        except subprocess.TimeoutExpired as te:
            end_t = time.perf_counter()
            finished_at = datetime.now(timezone.utc)
            duration_ms = round((end_t - start_t) * 1000.0, 2)
            record = CommandExecutionRecord(
                original_command=original_command,
                effective_command=effective_command,
                privileged=privileged,
                namespace=namespace,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                return_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout_seconds}s"
            )
            if check:
                raise ResearchTestbedError(
                    f"Command execution timed out ('{' '.join(effective_command)}')"
                ) from te
            return record
