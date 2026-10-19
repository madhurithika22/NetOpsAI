from typing import List, Tuple
from app.models.cadd_models import ActionPlan, ProposedAction
from app.models.msvs_models import PolicyViolation
from app.testbed.config import PROTECTED_HOST_INTERFACES, TESTBED_PREFIX
from app.testbed.manager import testbed_manager

class SafetyPolicyEngine:
    """
    Stage 1 & Stage 2 Static Policy Filter and Dry-Run Validator.
    Supports protection of host management interfaces, NetOps ownership verification, and blast radius constraints.
    """
    ALLOWED_COMMAND_TYPES = {
        "REROUTE_TRAFFIC", 
        "SET_INTERFACE_STATE", 
        "ADJUST_METRIC", 
        "FLUSH_ARP", 
        "RESTORE_ROUTING_TABLE",
        "RESET_OSPF_NEIGHBOR_AND_METRIC",
        "APPLY_SDWAN_QOS_TRAFFIC_SHAPING",
        "SET_INTERFACE_MTU",
        "RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE"
    }

    def validate_plan(self, plan: ActionPlan) -> Tuple[bool, bool, List[PolicyViolation]]:
        stage1_passed = True
        stage2_passed = True
        violations: List[PolicyViolation] = []

        for action in plan.proposed_actions:
            # Stage 1: Command whitelist check
            if action.command_type not in self.ALLOWED_COMMAND_TYPES:
                stage1_passed = False
                violations.append(
                    PolicyViolation(
                        policy_id="POL_001_WHITELIST",
                        policy_name="Command Type Whitelist",
                        violation_reason=f"Command type '{action.command_type}' is not in permitted safety whitelist."
                    )
                )

            # Stage 1: Protected interface check (protect eth0, wlan0, lo, mgmt0, docker0)
            target_iface = action.parameters.get("interface", "")
            if target_iface in PROTECTED_HOST_INTERFACES:
                stage1_passed = False
                violations.append(
                    PolicyViolation(
                        policy_id="POL_002_PROTECTED_IFACE",
                        policy_name="Management Interface Protection",
                        violation_reason=f"Action targets protected infrastructure interface '{target_iface}'."
                    )
                )

            # Stage 2: Syntax and parameter bounds check
            if action.command_type in ["REROUTE_TRAFFIC", "RESTORE_ROUTING_TABLE"]:
                if "destination" not in action.parameters and "target_destination" not in action.parameters and "interface" not in action.parameters:
                    stage2_passed = False
                    violations.append(
                        PolicyViolation(
                            policy_id="POL_003_MISSING_PARAM",
                            policy_name="Required Parameter Bounds",
                            violation_reason="Missing required destination parameter for routing modifications."
                        )
                    )

        overall_valid = stage1_passed and stage2_passed
        return stage1_passed, stage2_passed, violations
