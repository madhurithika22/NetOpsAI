"""
Experiment Recorder for NetOps Research V2.

Assembles and persists immutable, fully auditable JSON experiment records.
"""

import os
import sys
import json
import platform
from datetime import datetime, timezone
from typing import Optional
from app.research_v2.testbed.models import (
    ExperimentRecord,
    TelemetrySnapshot,
    FaultDefinition,
    FaultInjectionRecord,
    RemediationPlan,
    RemediationExecutionRecord,
    IndependentVerificationRecord
)


class ExperimentRecorder:
    """
    Persists complete research experiment records to disk.
    """

    def __init__(self, output_dir: str = "scratch/research_v2/phase1/runs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def create_record(
        self,
        experiment_id: str,
        run_id: str,
        final_status: str,
        topology_def: dict,
        baseline_snapshot: Optional[TelemetrySnapshot] = None,
        fault_def: Optional[FaultDefinition] = None,
        fault_inj_record: Optional[FaultInjectionRecord] = None,
        remediation_plan: Optional[RemediationPlan] = None,
        remediation_exec_record: Optional[RemediationExecutionRecord] = None,
        verification_record: Optional[IndependentVerificationRecord] = None,
    ) -> ExperimentRecord:
        """
        Assembles immutable ExperimentRecord object.
        """
        system_info = {
            "platform": sys.platform,
            "os_name": os.name,
            "python_version": sys.version,
            "system_release": platform.release(),
            "machine": platform.machine()
        }

        # Gather raw command history from snapshots and execution records
        raw_history = []
        if baseline_snapshot:
            raw_history.extend(baseline_snapshot.raw_commands)
        if fault_inj_record:
            raw_history.append(fault_inj_record.injection_command_record)
            raw_history.extend(fault_inj_record.post_fault_snapshot.raw_commands)
        if remediation_exec_record:
            raw_history.append(remediation_exec_record.command_record)
        if verification_record:
            raw_history.extend(verification_record.verification_snapshot.raw_commands)

        record = ExperimentRecord(
            experiment_id=experiment_id,
            run_id=run_id,
            timestamp=datetime.now(timezone.utc),
            testbed_version="2.0.0-phase1",
            system_info=system_info,
            topology_definition=topology_def,
            baseline_snapshot=baseline_snapshot,
            fault_definition=fault_def,
            fault_injection_record=fault_inj_record,
            remediation_plan=remediation_plan,
            remediation_execution_record=remediation_exec_record,
            independent_verification_record=verification_record,
            final_status=final_status,
            raw_command_history=raw_history
        )

        return record

    def save_record(self, record: ExperimentRecord) -> str:
        """
        Saves ExperimentRecord as formatted JSON file.
        Returns target filepath.
        """
        filename = f"{record.experiment_id}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))

        return filepath
