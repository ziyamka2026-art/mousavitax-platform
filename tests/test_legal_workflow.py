import sys
sys.path.insert(0, "packages/agent-core")
from agent_core.legal_workflow import Gate, LegalAppealWorkflow, WorkflowError, WorkflowStatus


def test_missing_facts_force_clarification_before_research():
    engine = LegalAppealWorkflow()
    wf = engine.start(case_id="case-1", owner_id="supervisor-1", request="تنظیم لایحه مالیاتی")
    wf = engine.record_intake(
        wf.workflow_id,
        actor_id="supervisor-1",
        facts={"year": 1402},
        missing_fields=["مرحله رسیدگی", "برگ تشخیص"],
        scope={"taxpayer_id": "tp-1"},
    )
    assert wf.status == WorkflowStatus.NEEDS_CLARIFICATION
    assert Gate.CLARIFICATION in wf.pending_gates


def test_no_evidence_blocks_release():
    engine = LegalAppealWorkflow()
    wf = engine.start(case_id="case-2", owner_id="supervisor-1", request="اعتراض")
    wf = engine.record_intake(wf.workflow_id, actor_id="supervisor-1", facts={}, missing_fields=[], scope={})
    wf = engine.submit_research(wf.workflow_id, actor_id="supervisor-1", findings={}, citations=[])
    assert wf.status == WorkflowStatus.BLOCKED
    assert Gate.EVIDENCE in wf.pending_gates


def test_only_owner_can_approve_and_delivery_requires_approval():
    engine = LegalAppealWorkflow()
    wf = engine.start(case_id="case-3", owner_id="supervisor-1", request="اعتراض")
    wf = engine.record_intake(wf.workflow_id, actor_id="supervisor-1", facts={}, missing_fields=[], scope={})
    wf = engine.submit_research(
        wf.workflow_id,
        actor_id="supervisor-1",
        findings={"issues": []},
        citations=[{"source_id": "law-237", "title": "ماده ۲۳۷", "source_type": "law"}],
    )
    wf = engine.submit_draft(wf.workflow_id, actor_id="supervisor-1", draft="پیش‌نویس", quality={"blockers": []}, attachment_index=[])
    try:
        engine.approve(wf.workflow_id, supervisor_id="other-user", decision="approve")
        assert False, "approval must be owner-only"
    except WorkflowError:
        pass
    wf = engine.approve(wf.workflow_id, supervisor_id="supervisor-1", decision="approve", note="بازبینی شد")
    assert wf.status == WorkflowStatus.APPROVED
    wf = engine.deliver(wf.workflow_id, actor_id="supervisor-1")
    assert wf.status == WorkflowStatus.DELIVERED
