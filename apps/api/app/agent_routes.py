"""HTTP boundary for routing and supervised legal-appeal workflows."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class AgentQuery(BaseModel):
    text: str
    actor_id: str | None = None
    case_id: str | None = None

class WorkflowStartIn(BaseModel):
    case_id: str
    owner_id: str
    request: str
    documents: list[dict[str, Any]] = Field(default_factory=list)
class IntakeIn(BaseModel):
    actor_id: str
    facts: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    scope: dict[str, Any] = Field(default_factory=dict)
class ClarificationIn(BaseModel):
    actor_id: str
    answers: dict[str, Any] = Field(default_factory=dict)
    documents: list[dict[str, Any]] = Field(default_factory=list)
class ResearchIn(BaseModel):
    actor_id: str
    findings: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] = Field(default_factory=list)
class DraftIn(BaseModel):
    actor_id: str
    draft: str
    quality: dict[str, Any] = Field(default_factory=dict)
    attachment_index: list[dict[str, Any]] = Field(default_factory=list)
class ApprovalIn(BaseModel):
    supervisor_id: str
    decision: str
    note: str = ""
class DeliveryIn(BaseModel):
    actor_id: str

def build_agent_router():
    from fastapi import APIRouter
    from agent_core.orchestrator import AgentOrchestrator, AgentRequest
    from agent_core.legal_workflow import LegalAppealWorkflow
    router = APIRouter(prefix="/agents", tags=["agents"])
    orchestrator = AgentOrchestrator()
    legal_workflow = LegalAppealWorkflow()

    @router.post("/route")
    def route_agent(query: AgentQuery):
        result = orchestrator.route(AgentRequest(text=query.text, actor_id=query.actor_id, case_id=query.case_id))
        return result.__dict__
    @router.post("/legal-workflow/start")
    def start_workflow(body: WorkflowStartIn):
        return legal_workflow.start(case_id=body.case_id, owner_id=body.owner_id, request=body.request, documents=body.documents).public_view()
    @router.get("/legal-workflow/{workflow_id}")
    def get_workflow(workflow_id: str):
        return legal_workflow.get(workflow_id).public_view()
    @router.post("/legal-workflow/{workflow_id}/intake")
    def record_intake(workflow_id: str, body: IntakeIn):
        return legal_workflow.record_intake(workflow_id, actor_id=body.actor_id, facts=body.facts, missing_fields=body.missing_fields, scope=body.scope).public_view()
    @router.post("/legal-workflow/{workflow_id}/clarification")
    def submit_clarification(workflow_id: str, body: ClarificationIn):
        return legal_workflow.submit_clarification(workflow_id, actor_id=body.actor_id, answers=body.answers, documents=body.documents).public_view()
    @router.post("/legal-workflow/{workflow_id}/research")
    def submit_research(workflow_id: str, body: ResearchIn):
        return legal_workflow.submit_research(workflow_id, actor_id=body.actor_id, findings=body.findings, citations=body.citations).public_view()
    @router.post("/legal-workflow/{workflow_id}/draft")
    def submit_draft(workflow_id: str, body: DraftIn):
        return legal_workflow.submit_draft(workflow_id, actor_id=body.actor_id, draft=body.draft, quality=body.quality, attachment_index=body.attachment_index).public_view()
    @router.post("/legal-workflow/{workflow_id}/approve")
    def approve_workflow(workflow_id: str, body: ApprovalIn):
        return legal_workflow.approve(workflow_id, supervisor_id=body.supervisor_id, decision=body.decision, note=body.note).public_view()
    @router.post("/legal-workflow/{workflow_id}/deliver")
    def deliver_workflow(workflow_id: str, body: DeliveryIn):
        return legal_workflow.deliver(workflow_id, actor_id=body.actor_id).public_view()
    return router
