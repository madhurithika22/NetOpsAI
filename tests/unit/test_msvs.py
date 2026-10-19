from app.ceso.service import ceso_service
from app.cadd.service import CADDService
from app.msvs.service import MSVSService
from app.models.cadd_models import ActionPlan, ProposedAction

def test_msvs_policy_validation_pass():
    msvs = MSVSService()
    plan = ActionPlan(
        plan_id="plan-test-01",
        diagnosis_id="diag-test-01",
        proposed_actions=[
            ProposedAction(
                action_id="act-01",
                command_type="REROUTE_TRAFFIC",
                target_device="rtr1",
                parameters={"interface": "rtr1-eth1", "target_destination": "10.0.2.0/24"},
                is_destructive=True
            )
        ],
        estimated_risk_level="MEDIUM",
        requires_approval=True
    )

    val_res = msvs.validate_action_plan(plan, "Test high latency diagnosis")
    assert val_res.is_valid is True
    assert val_res.stage1_policy_passed is True
    assert val_res.stage2_syntax_passed is True
    assert len(val_res.policy_violations) == 0

def test_msvs_policy_validation_fail_protected_interface():
    msvs = MSVSService()
    plan = ActionPlan(
        plan_id="plan-test-02",
        diagnosis_id="diag-test-02",
        proposed_actions=[
            ProposedAction(
                action_id="act-02",
                command_type="SET_INTERFACE_STATE",
                target_device="rtr1",
                parameters={"interface": "eth0", "state": "DOWN"},  # eth0 is protected!
                is_destructive=True
            )
        ],
        estimated_risk_level="HIGH",
        requires_approval=True
    )

    val_res = msvs.validate_action_plan(plan)
    assert val_res.is_valid is False
    assert val_res.stage1_policy_passed is False
    assert any(v.policy_id == "POL_002_PROTECTED_IFACE" for v in val_res.policy_violations)

def test_msvs_approval_and_execution_flow():
    # Reset CESO
    ceso_service.reset_simulation()
    cadd = CADDService()
    msvs = MSVSService()

    # Inject fault and get plan
    state = ceso_service.inject_fault("HIGH_LATENCY_CONGESTION")
    report, plan = cadd.diagnose_network_state(state)

    # Validate
    val_res = msvs.validate_action_plan(plan, report.explanation_summary)
    assert val_res.is_valid is True

    # Pending approval should exist
    pending = msvs.get_pending_approvals()
    assert len(pending) == 1
    approval_req = pending[0]
    assert approval_req.plan_id == plan.plan_id
    assert approval_req.status == "PENDING"

    # Approve
    approved_req = msvs.approve_request(approval_req.approval_id, reviewer_id="OPERATOR_TEST")
    assert approved_req is not None
    assert approved_req.status == "APPROVED"

    # Execute
    log = msvs.execute_action_plan(plan.plan_id, operator_id="OPERATOR_TEST")
    assert log.status == "SUCCESS"
    assert log.post_verification_passed is True

    # Verify CESO state post-execution
    post_state = ceso_service.get_latest_state()
    assert post_state.anomalies_detected is False
