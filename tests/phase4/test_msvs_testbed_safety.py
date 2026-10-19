import pytest
from app.msvs.service import MSVSService
from app.models.cadd_models import ActionPlan, ProposedAction

def test_msvs_safety_policy_rejects_host_interface():
    msvs = MSVSService()
    plan = ActionPlan(
        plan_id="plan-testbed-unsafe",
        diagnosis_id="diag-testbed-unsafe",
        proposed_actions=[
            ProposedAction(
                action_id="act-unsafe-wlan0",
                command_type="SET_INTERFACE_STATE",
                target_device="rtr1",
                parameters={"interface": "wlan0", "target_state": "DOWN"},
                is_destructive=True
            )
        ],
        estimated_risk_level="HIGH",
        requires_approval=True
    )

    res = msvs.validate_action_plan(plan)
    assert res.is_valid is False
    assert res.stage1_policy_passed is False
    assert any(v.policy_id == "POL_002_PROTECTED_IFACE" for v in res.policy_violations)
