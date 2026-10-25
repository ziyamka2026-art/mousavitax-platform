"""Supervised Iranian tax-appeal workflow.

The module is intentionally provider-agnostic: model calls, Drive retrieval and
OCR are adapters. The state machine itself is deterministic and blocks final
issuance until evidence, clarification and human-review gates pass.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class WorkflowStatus(str, Enum):
    INTAKE = "INTAKE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    RESEARCH = "RESEARCH"
    ANALYSIS = "ANALYSIS"
    DRAFTING = "DRAFTING"
    QUALITY_REVIEW = "QUALITY_REVIEW"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    APPROVED = "APPROVED"
    DELIVERED = "DELIVERED"
    BLOCKED = "BLOCKED"


class Gate(str, Enum):
    CLARIFICATION = "CLARIFICATION"
    EVIDENCE = "EVIDENCE"
    CITATION = "CITATION"
    CONTRADICTION = "CONTRADICTION"
    FINAL_HUMAN_REVIEW = "FINAL_HUMAN_REVIEW"


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    title: str
    mission: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    tools: tuple[str, ...]
    autonomy: str = "suggest"


AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition("case-intake", "پذیرش و تفکیک پرونده", "ساخت شناسنامه پرونده و جداسازی مؤدی، اشخاص، املاک و معاملات", ("user_request", "case_documents"), ("case_identity", "missing_fields", "case_scope"), ("case.read", "document.list")),
    AgentDefinition("document-forensics", "کارشناس اسناد و OCR", "خواندن اصل سند، استخراج ارقام و ثبت شماره، تاریخ و صادرکننده", ("case_documents",), ("document_facts", "document_index", "ocr_warnings"), ("document.read", "ocr.run", "checksum.verify")),
    AgentDefinition("drive-research", "پژوهشگر مخزن قوانین", "جست‌وجوی اولویت‌دار در Google Drive و ثبت منابع قابل استناد", ("case_scope", "legal_questions"), ("retrieved_sources", "source_conflicts"), ("drive.search", "drive.open", "citation.capture")),
    AgentDefinition("timeline-agent", "تحلیل‌گر زمانی", "تعیین سال عملکرد، تاریخ رویداد و قانون لازم‌الاجرا و منع عطف‌به‌ماسبق", ("document_facts",), ("timeline", "temporal_risks"), ("date.normalize", "law.effective_date")),
    AgentDefinition("legal-issues", "تحلیل‌گر مسائل حقوقی", "تفکیک ایرادات شکلی و ماهوی و نگاشت هر ادعا به قانون و دلیل", ("document_facts", "retrieved_sources", "timeline"), ("issue_matrix", "claims_evidence_map"), ("law.map", "precedent.search")),
    AgentDefinition("accounting-check", "بازبین حسابداری و محاسبات", "بازمحاسبه ارقام و تطبیق اظهارنامه، تشخیص، گزارش رسیدگی و پرداخت‌ها", ("document_facts",), ("calculation_table", "accounting_findings"), ("calculator.run", "accounting.standard.search")),
    AgentDefinition("penalty-procedure", "تحلیل‌گر جرائم و تشریفات", "بررسی مبنای جریمه، ابلاغ، مهلت، صلاحیت، حق دفاع و بخشودگی", ("issue_matrix", "timeline", "retrieved_sources"), ("penalty_matrix", "procedure_findings"), ("deadline.check", "procedure.map")),
    AgentDefinition("defense-strategy", "طراح دفاع چندلایه", "اولویت‌بندی دفاع اصلی، تکمیلی، علی‌البدل و درخواست احتیاطی", ("issue_matrix", "claims_evidence_map", "accounting_findings", "procedure_findings"), ("defense_plan", "risk_register"), ("strategy.rank",)),
    AgentDefinition("drafting-agent", "تنظیم‌کننده لایحه", "تدوین پیش‌نویس رسمی فقط بر اساس واقعیت‌های اثبات‌شده و منابع ثبت‌شده", ("defense_plan", "claims_evidence_map", "retrieved_sources"), ("draft", "attachment_index"), ("draft.compose",)),
    AgentDefinition("citation-verifier", "بازرس استنادات", "کنترل شماره ماده، تاریخ، صادرکننده، URL و ارتباط واقعی استناد با ادعا", ("draft", "retrieved_sources"), ("citation_report",), ("citation.verify",), "read_only"),
    AgentDefinition("contradiction-reviewer", "بازبین تناقض و محرمانگی", "کشف تناقض، تعمیم ناروا میان مؤدیان و افشای اطلاعات پرونده", ("draft", "document_facts", "case_scope"), ("contradiction_report", "privacy_report"), ("consistency.check", "privacy.scan"), "read_only"),
    AgentDefinition("quality-gate", "دروازه کیفیت نهایی", "بررسی کامل بودن واقعیت، قانون، زمان، محاسبات، جرائم، خواسته و پیوست‌ها", ("draft", "citation_report", "contradiction_report", "calculation_table"), ("quality_report", "release_blockers"), ("quality.check",), "read_only"),
)


@dataclass
class WorkflowEvent:
    event: str
    actor_id: str | None
    agent_id: str
    details: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CaseWorkflow:
    workflow_id: str
    case_id: str
    owner_id: str
    status: WorkflowStatus = WorkflowStatus.INTAKE
    current_stage: str = "case-intake"
    data: dict[str, Any] = field(default_factory=dict)
    pending_gates: list[Gate] = field(default_factory=list)
    events: list[WorkflowEvent] = field(default_factory=list)
    version: int = 1

    def public_view(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "case_id": self.case_id,
            "owner_id": self.owner_id,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "pending_gates": [g.value for g in self.pending_gates],
            "data": self.data,
            "events": [asdict(e) for e in self.events],
            "version": self.version,
        }


class WorkflowError(ValueError):
    pass


class LegalAppealWorkflow:
    """Deterministic supervisor for the legal-research and pleading loop."""

    def __init__(self) -> None:
        self._workflows: dict[str, CaseWorkflow] = {}

    def start(self, *, case_id: str, owner_id: str, request: str, documents: list[dict[str, Any]] | None = None) -> CaseWorkflow:
        if not case_id or not owner_id or not request.strip():
            raise WorkflowError("case_id، owner_id و شرح درخواست الزامی است")
        workflow = CaseWorkflow(
            workflow_id=str(uuid4()),
            case_id=case_id,
            owner_id=owner_id,
            data={"request": request, "documents": documents or [], "facts": {"certain": [], "probable": [], "unknown": []}},
        )
        workflow.events.append(WorkflowEvent("workflow.started", owner_id, "case-intake", {"case_id": case_id}))
        self._workflows[workflow.workflow_id] = workflow
        return workflow

    def get(self, workflow_id: str) -> CaseWorkflow:
        try:
            return self._workflows[workflow_id]
        except KeyError as exc:
            raise WorkflowError("workflow یافت نشد") from exc

    def record_intake(self, workflow_id: str, *, actor_id: str, facts: dict[str, Any], missing_fields: list[str], scope: dict[str, Any]) -> CaseWorkflow:
        wf = self.get(workflow_id)
        self._assert_owner(wf, actor_id)
        wf.data.update({"facts": facts, "case_scope": scope, "missing_fields": missing_fields})
        wf.events.append(WorkflowEvent("intake.completed", actor_id, "case-intake", {"missing_fields": missing_fields}))
        if missing_fields:
            wf.status = WorkflowStatus.NEEDS_CLARIFICATION
            wf.current_stage = "case-intake"
            self._add_gate(wf, Gate.CLARIFICATION)
        else:
            wf.status = WorkflowStatus.RESEARCH
            wf.current_stage = "document-forensics"
        wf.version += 1
        return wf

    def submit_clarification(self, workflow_id: str, *, actor_id: str, answers: dict[str, Any], documents: list[dict[str, Any]] | None = None) -> CaseWorkflow:
        wf = self.get(workflow_id)
        self._assert_owner(wf, actor_id)
        if Gate.CLARIFICATION not in wf.pending_gates:
            raise WorkflowError("دروازه رفع ابهام فعال نیست")
        wf.data.setdefault("clarifications", {}).update(answers)
        if documents:
            wf.data.setdefault("documents", []).extend(documents)
        wf.pending_gates.remove(Gate.CLARIFICATION)
        wf.status = WorkflowStatus.RESEARCH
        wf.current_stage = "document-forensics"
        wf.events.append(WorkflowEvent("clarification.submitted", actor_id, "human-supervisor", {"answer_count": len(answers)}))
        wf.version += 1
        return wf

    def submit_research(self, workflow_id: str, *, actor_id: str, findings: dict[str, Any], citations: list[dict[str, Any]]) -> CaseWorkflow:
        wf = self.get(workflow_id)
        self._assert_owner(wf, actor_id)
        if wf.status not in (WorkflowStatus.RESEARCH, WorkflowStatus.ANALYSIS):
            raise WorkflowError("پرونده در مرحله تحقیق یا تحلیل نیست")
        wf.data.update({"findings": findings, "citations": citations})
        wf.events.append(WorkflowEvent("research.completed", actor_id, "multi-agent-research", {"citation_count": len(citations)}))
        if not citations:
            wf.status = WorkflowStatus.BLOCKED
            wf.data.setdefault("release_blockers", []).append("هیچ منبع قابل استنادی ثبت نشده است")
            self._add_gate(wf, Gate.EVIDENCE)
        else:
            wf.status = WorkflowStatus.ANALYSIS
            wf.current_stage = "legal-issues"
        wf.version += 1
        return wf

    def submit_draft(self, workflow_id: str, *, actor_id: str, draft: str, quality: dict[str, Any], attachment_index: list[dict[str, Any]]) -> CaseWorkflow:
        wf = self.get(workflow_id)
        self._assert_owner(wf, actor_id)
        if wf.status not in (WorkflowStatus.ANALYSIS, WorkflowStatus.DRAFTING):
            raise WorkflowError("پرونده هنوز آماده تدوین نیست")
        wf.data.update({"draft": draft, "quality_report": quality, "attachment_index": attachment_index})
        blockers = list(quality.get("blockers", []))
        if blockers:
            wf.status = WorkflowStatus.BLOCKED
            wf.data["release_blockers"] = blockers
        else:
            wf.status = WorkflowStatus.HUMAN_REVIEW
            wf.current_stage = "human-supervisor"
            self._add_gate(wf, Gate.FINAL_HUMAN_REVIEW)
        wf.events.append(WorkflowEvent("draft.ready", actor_id, "quality-gate", {"blocker_count": len(blockers)}))
        wf.version += 1
        return wf

    def approve(self, workflow_id: str, *, supervisor_id: str, decision: str, note: str = "") -> CaseWorkflow:
        wf = self.get(workflow_id)
        self._assert_owner(wf, supervisor_id)
        if Gate.FINAL_HUMAN_REVIEW not in wf.pending_gates:
            raise WorkflowError("تأیید نهایی انسانی در انتظار نیست")
        if decision not in {"approve", "reject", "request_changes"}:
            raise WorkflowError("decision باید approve، reject یا request_changes باشد")
        wf.events.append(WorkflowEvent(f"human_review.{decision}", supervisor_id, "human-supervisor", {"note": note}))
        wf.pending_gates.remove(Gate.FINAL_HUMAN_REVIEW)
        if decision == "approve":
            wf.status = WorkflowStatus.APPROVED
            wf.current_stage = "delivery"
        else:
            wf.status = WorkflowStatus.BLOCKED
            wf.current_stage = "quality-gate"
            wf.data.setdefault("release_blockers", []).append(note or "نیازمند اصلاح توسط تیم ایجنت‌ها")
        wf.version += 1
        return wf

    def deliver(self, workflow_id: str, *, actor_id: str) -> CaseWorkflow:
        wf = self.get(workflow_id)
        self._assert_owner(wf, actor_id)
        if wf.status != WorkflowStatus.APPROVED:
            raise WorkflowError("تحویل فقط پس از تأیید ناظر مجاز است")
        wf.status = WorkflowStatus.DELIVERED
        wf.events.append(WorkflowEvent("pleading.delivered", actor_id, "human-supervisor", {"case_id": wf.case_id}))
        wf.version += 1
        return wf

    @staticmethod
    def _add_gate(wf: CaseWorkflow, gate: Gate) -> None:
        if gate not in wf.pending_gates:
            wf.pending_gates.append(gate)

    @staticmethod
    def _assert_owner(wf: CaseWorkflow, actor_id: str) -> None:
        if actor_id != wf.owner_id:
            raise WorkflowError("فقط ناظر مالک پرونده می‌تواند این مرحله را ثبت یا تأیید کند")


def workflow_blueprint() -> dict[str, Any]:
    return {
        "name": "iran-tax-appeal-supervised-loop",
        "version": "1.0.0",
        "principles": ["case_isolation", "evidence_first", "official_sources_first", "human_in_the_loop", "no_final_without_clarification"],
        "parallel_tracks": ["timeline-agent", "legal-issues", "accounting-check", "penalty-procedure"],
        "gates": [g.value for g in Gate],
        "agents": [asdict(agent) for agent in AGENTS],
        "stages": [
            "intake", "document_forensics", "clarification_gate", "drive_research", "parallel_analysis",
            "defense_strategy", "draft", "citation_review", "contradiction_privacy_review", "quality_gate",
            "human_supervisor_approval", "delivery_and_archive",
        ],
    }
