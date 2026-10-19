"""
Real Remediation Executor for NetOps Research V2.

Executes corrective network commands against target Linux network namespaces.
Strictly prohibits simulation resets, mock execution, or Python state overrides.
"""

import uuid
from datetime import datetime, timezone
from app.research_v2.guard import ResearchExecutionContext
from app.research_v2.testbed.executor import ControlledExecutor
from app.research_v2.testbed.models import (
    RemediationPlan,
    RemediationExecutionRecord
)
from app.research_v2.testbed.telemetry import RealTelemetryCollector
from app.research_v2.testbed.exceptions import RemediationExecutionError


class RealRemediationExecutor:
    """
    Executes real remediation actions in Linux network namespaces.
    """

    @classmethod
    def execute_remediation(
        cls,
        plan: RemediationPlan,
        experiment_id: str = "exp-default"
    ) -> RemediationExecutionRecord:
        """
        Executes real Linux command in target namespace with privileged=True.
        """
        ResearchExecutionContext.assert_real_execution("RealRemediationExecutor")

        # 1. Take pre-remediation snapshot
        pre_snapshot = RealTelemetryCollector.collect_telemetry(experiment_id)

        executed_at = datetime.now(timezone.utc)

        # 2. Execute real remediation command (e.g. tc qdisc del dev veth-r1-r2 root) with privileged=True
        cmd_rec = ControlledExecutor.run_command(
            plan.remediation_command,
            namespace=plan.target_namespace,
            privileged=True
        )

        if cmd_rec.return_code != 0:
            raise RemediationExecutionError(
                f"Remediation command failed on {plan.target_namespace}:{plan.target_interface}: {cmd_rec.stderr}"
            )

        execution_id = f"exec-{uuid.uuid4().hex[:8]}"

        return RemediationExecutionRecord(
            execution_id=execution_id,
            plan_id=plan.plan_id,
            executed_at=executed_at,
            command_record=cmd_rec,
            status="EXECUTED",
            pre_remediation_snapshot=pre_snapshot
        )
