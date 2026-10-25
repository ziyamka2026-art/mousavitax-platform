"""
Legal Analysis Pipeline — TAXLAW-GROK Constitution v2.0
============================================================

Implements the mandatory 6-stage workflow defined in Chapter 3 of the
TAXLAW-GROK Constitution:

  Stage 1 — Intake & PII Sanitization  (Principle 1)
  Stage 2 — Fiqh Rooting                (Principle 3)
  Stage 3 — Knowledge Retrieval        (Multi-tier Memory)
  Stage 4 — Appeal Drafting             (Principle 4)
  Stage 5 — Archival Version            (Principle 2)
  Stage 6 — Human Review Handoff         (Core Oath)

Each stage:
  - Receives a PipelineContext
  - Performs its work
  - Returns a StageResult (passed/failed + enriched context)
  - Writes to audit_log automatically

The pipeline is strictly sequential — no stage is skippable.

@package apps.api.app.orchestrator
@see docs/adr/ADR-009-TAXLAW-GROK-Constitution.md (Chapter 3)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from packages.fiqh_validator.validator import (
    AnalysisContext,
    Citation,
    enforce_fiqh,
    validate_analysis,
    ValidationReport,
)
from packages.oath.runtime_guards import (
    AnalysisResult,
    AnalysisStatus,
    Citation as OathCitation,
    OathViolation,
    PIIRedactor,
    enforce_oath,
)


# ---------------------------------------------------------------------------
# Pipeline data models
# ---------------------------------------------------------------------------

class PipelineStatus(str, Enum):
    INTAKE = "intake"
    FIQH_ROOTING = "fiqh_rooting"
    RETRIEVAL = "retrieval"
    DRAFTING = "drafting"
    ARCHIVAL = "archival"
    HANDOFF = "handoff"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CaseInput:
    """Raw input from intake (web/bot/upload)."""
    case_id: str
    tenant_id: str
    user_id: str
    question: str
    documents: list[dict[str, Any]] = field(default_factory=list)  # raw docs
    metadata: dict[str, Any] = field(default_factory=dict)
    received_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class StageResult:
    stage: str
    passed: bool
    duration_ms: int
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class PipelineContext:
    """Mutable context passed through all stages."""
    input: CaseInput
    sanitized_content: str = ""
    fiqh_report: ValidationReport | None = None
    retrieved_citations: list[Citation] = field(default_factory=list)
    retrieved_evidence: list[dict[str, Any]] = field(default_factory=list)
    draft_content: str = ""
    analysis_result: AnalysisResult | None = None
    archive_id: str | None = None
    handoff_token: str | None = None
    stages_log: list[StageResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_stage(self, result: StageResult) -> None:
        self.stages_log.append(result)


class StageFailedError(Exception):
    """Raised when a pipeline stage cannot complete successfully."""

    def __init__(self, stage: str, reason: str, context: PipelineContext | None = None):
        self.stage = stage
        self.reason = reason
        self.context = context
        super().__init__(f"Stage '{stage}' failed: {reason}")


# ---------------------------------------------------------------------------
# Stage Protocol
# ---------------------------------------------------------------------------

class PipelineStage(Protocol):
    """Interface for all pipeline stages."""
    name: str

    async def execute(self, ctx: PipelineContext) -> StageResult: ...


    def rollback(self, ctx: PipelineContext) -> None: ...


# ---------------------------------------------------------------------------
# Stage 1: Intake & PII Sanitization (Principle 1)
# ---------------------------------------------------------------------------

class IntakeAndSanitizeStage:
    """Filters PII from raw input before any further processing."""
    name = "intake_and_sanitize"

    async def execute(self, ctx: PipelineContext) -> StageResult:
        started = datetime.now(timezone.utc)
        try:
            # Redact PII from the question text
            ctx.sanitized_content = PIIRedactor.redact(ctx.input.question)

            # Redact PII from documents metadata
            for doc in ctx.input.documents:
                if "content" in doc and isinstance(doc["content"], str):
                    doc["content"] = PIIRedactor.redact(doc["content"])
                if "metadata" in doc and isinstance(doc["metadata"], dict):
                    doc["metadata"] = PIIRedactor.redact_dict(doc["metadata"])

            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=True,
                duration_ms=duration,
                output={
                    "sanitized_length": len(ctx.sanitized_content),
                    "documents_redacted": len(ctx.input.documents),
                    "trace_id": ctx.trace_id,
                },
            )
        except Exception as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    def rollback(self, ctx: PipelineContext) -> None:
        ctx.sanitized_content = ""


# ---------------------------------------------------------------------------
# Stage 2: Fiqh Rooting (Principle 3)
# ---------------------------------------------------------------------------

class FiqhRootingStage:
    """Validates the analysis context against 7 fiqh rules."""
    name = "fiqh_rooting"

    def __init__(self, baseline_context: AnalysisContext | None = None):
        """Optional baseline — used to seed defaults for the analysis."""
        self._baseline = baseline_context

    async def execute(self, ctx: PipelineContext) -> StageResult:
        started = datetime.now(timezone.utc)
        try:
            # Build the AnalysisContext from pipeline input
            ac = self._build_analysis_context(ctx)
            report = validate_analysis(ac)
            ctx.fiqh_report = report

            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            failed_rules = [r.rule.value for r in report.failed_rules()]
            return StageResult(
                stage=self.name,
                passed=report.overall_passed,
                duration_ms=duration,
                output={
                    "overall_passed": report.overall_passed,
                    "failed_rules": failed_rules,
                    "summary": report.summary,
                },
                error=None if report.overall_passed else report.summary,
            )
        except Exception as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    def _build_analysis_context(self, ctx: PipelineContext) -> AnalysisContext:
        """Map pipeline input to AnalysisContext for fiqh validation."""
        if self._baseline:
            base = self._baseline
        else:
            base = AnalysisContext(content=ctx.sanitized_content)

        # Override with what we know from pipeline input
        base.content = ctx.sanitized_content or base.content

        # Detect ambiguity markers in the input question
        ambiguity_markers = ["مبهم", "نامشخص", "ابهام", "غیر واضح"]
        base.has_ambiguity = any(m in ctx.sanitized_content for m in ambiguity_markers)

        # Detect burden-of-proof keywords
        if "کتمان" in ctx.sanitized_content or "پنهان‌کاری" in ctx.sanitized_content:
            base.burden_of_proof = "administration"

        # Detect prior-exemption claim
        if "معافیت قبلی" in ctx.sanitized_content or "معاف بودم" in ctx.sanitized_content:
            base.has_prior_exemption = True

        # Detect hardship claim
        if "عسر و حرج" in ctx.sanitized_content or "مالایطاق" in ctx.sanitized_content:
            base.hardship_claim = True

        return base

    def rollback(self, ctx: PipelineContext) -> None:
        ctx.fiqh_report = None


# ---------------------------------------------------------------------------
# Stage 3: Knowledge Retrieval (Multi-tier Memory)
# ---------------------------------------------------------------------------

class KnowledgeRetrievalStage:
    """Fetches relevant knowledge from L1 (cache), L2 (vector), L4 (graph)."""
    name = "knowledge_retrieval"

    def __init__(self, retriever: "KnowledgeRetriever | None" = None):
        self._retriever = retriever

    async def execute(self, ctx: PipelineContext) -> StageResult:
        started = datetime.now(timezone.utc)
        try:
            if self._retriever is None:
                # Use a stub for testing — in production, inject real retriever
                ctx.retrieved_citations = []
                ctx.retrieved_evidence = []
                duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
                return StageResult(
                    stage=self.name,
                    passed=True,
                    duration_ms=duration,
                    output={
                        "citations_count": 0,
                        "evidence_count": 0,
                        "note": "no retriever injected — stub mode",
                    },
                )

            results = await self._retriever.search(ctx.sanitized_content, limit=6)
            ctx.retrieved_citations = [
                Citation(
                    source_type=r.get("source_type", "law"),
                    source_id=r["source_id"],
                    title=r["title"],
                    url=r.get("url"),
                    effective_date=r.get("effective_date"),
                )
                for r in results
            ]
            ctx.retrieved_evidence = results

            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=True,
                duration_ms=duration,
                output={
                    "citations_count": len(ctx.retrieved_citations),
                    "evidence_count": len(ctx.retrieved_evidence),
                },
            )
        except Exception as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    def rollback(self, ctx: PipelineContext) -> None:
        ctx.retrieved_citations = []
        ctx.retrieved_evidence = []


class KnowledgeRetriever(Protocol):
    """Interface for the multi-tier retrieval implementation."""
    async def search(self, query: str, limit: int = 6) -> list[dict[str, Any]]: ...


# ---------------------------------------------------------------------------
# Stage 4: Appeal Drafting (Principle 4 — LAYEHA_APPEAL_WORKFLOW_V)
# ---------------------------------------------------------------------------

class AppealDraftingStage:
    """Generates a draft appeal document matching repository workflow."""
    name = "appeal_drafting"

    def __init__(self, llm_provider: "LLMProvider | None" = None):
        self._llm = llm_provider

    async def execute(self, ctx: PipelineContext) -> StageResult:
        started = datetime.now(timezone.utc)
        try:
            if self._llm is None:
                # Stub: produce a structured draft from retrieved citations
                ctx.draft_content = self._render_stub_draft(ctx)
            else:
                ctx.draft_content = await self._llm_generate(ctx)

            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=True,
                duration_ms=duration,
                output={
                    "draft_length": len(ctx.draft_content),
                    "citations_used": len(ctx.retrieved_citations),
                },
            )
        except Exception as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    def _render_stub_draft(self, ctx: PipelineContext) -> str:
        citations_block = "\n".join(
            f"- [{i+1}] {c.title} ({c.source_type})"
            for i, c in enumerate(ctx.retrieved_citations)
        )
        ambiguity_note = ""
        if ctx.fiqh_report and any(
            not r.passed and "ابهام" in r.reasoning
            for r in ctx.fiqh_report.results
        ):
            ambiguity_note = "\n\n[نکته]: در این پرونده ابهام وجود دارد و تفسیر به نفع مؤدی اعمال شده است."

        return (
            f"پیش‌نویس لایحه (پرونده {ctx.input.case_id})\n"
            f"------------------------------\n"
            f"{ctx.sanitized_content}\n\n"
            f"استنادات:\n{citations_block or '(بدون استناد)'}"
            f"{ambiguity_note}\n\n"
            f"[تذکر]: این پیش‌نویس نیازمند بازبینی توسط مشاور رسمی است."
        )

    async def _llm_generate(self, ctx: PipelineContext) -> str:
        """Use the injected LLM provider to generate the draft."""
        # In production: call self._llm.complete(messages)
        # For now, fallback to stub
        return self._render_stub_draft(ctx)

    def rollback(self, ctx: PipelineContext) -> None:
        ctx.draft_content = ""


class LLMProvider(Protocol):
    """LLM interface — compatible with apps/api/app/llm/factory.py."""
    async def complete(self, messages: list, **kwargs: Any) -> Any: ...


# ---------------------------------------------------------------------------
# Stage 5: Archival Version (Principle 2)
# ---------------------------------------------------------------------------

class ArchiveVersionStage:
    """Persists the analysis to case_analyses (INSERT-only table)."""
    name = "archive_version"

    def __init__(self, archive_sink: "ArchiveSink | None" = None):
        self._sink = archive_sink

    async def execute(self, ctx: PipelineContext) -> StageResult:
        started = datetime.now(timezone.utc)
        try:
            # Build the AnalysisResult — set status PENDING (NOT FINAL)
            oath_citations = [
                OathCitation(
                    source_type=c.source_type,
                    source_id=c.source_id,
                    title=c.title,
                    url=c.url,
                    effective_date=c.effective_date,
                )
                for c in ctx.retrieved_citations
            ]

            # Determine has_ambiguity: was the tafsir_maddiq rule actually
            # triggered (i.e. ambiguity was detected in the input)?
            has_ambiguity = False
            if ctx.fiqh_report is not None:
                from packages.fiqh_validator.validator import FiqhRule
                for r in ctx.fiqh_report.results:
                    # Rule 6 (tafsir_maddiq) is only invoked when ambiguity is present
                    if r.rule == FiqhRule.TAFSIR_MADDIQ:
                        # If the rule mentions "ابهام شناسایی" → ambiguity was detected
                        # If it says "اعمال نمی‌شود" → no ambiguity
                        if "اعمال نمی‌شود" not in r.reasoning:
                            has_ambiguity = True

            ctx.analysis_result = AnalysisResult(
                content=ctx.draft_content,
                citations=oath_citations,
                case_id=ctx.input.case_id,
                status=AnalysisStatus.PENDING_HUMAN_REVIEW,
                reasoning_chain=[
                    {"stage": "fiqh_rooting",
                     "passed": ctx.fiqh_report.overall_passed if ctx.fiqh_report else False},
                    {"stage": "knowledge_retrieval",
                     "citations_count": len(ctx.retrieved_citations)},
                ],
                has_ambiguity=has_ambiguity,
            )

            # Persist via sink (if injected)
            if self._sink is not None:
                ctx.archive_id = await self._sink.archive(ctx.analysis_result)

            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=True,
                duration_ms=duration,
                output={
                    "analysis_id": ctx.archive_id,
                    "version": ctx.analysis_result.version,
                    "status": ctx.analysis_result.status.value,
                },
            )
        except Exception as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    def rollback(self, ctx: PipelineContext) -> None:
        ctx.analysis_result = None
        ctx.archive_id = None


class ArchiveSink(Protocol):
    """Persistence interface — implement with Supabase in production."""
    async def archive(self, result: AnalysisResult) -> str: ...


# ---------------------------------------------------------------------------
# Stage 6: Human Review Handoff (Core Oath)
# ---------------------------------------------------------------------------

class HumanReviewHandoffStage:
    """Final guard — ensures human reviewer is in the loop before delivery."""
    name = "human_review_handoff"

    async def execute(self, ctx: PipelineContext) -> StageResult:
        started = datetime.now(timezone.utc)
        try:
            # Enforce Oath guards — this is the FINAL gate
            if ctx.analysis_result is None:
                raise StageFailedError(
                    self.name,
                    "no analysis result to deliver — previous stage failed",
                    ctx,
                )

            enforce_oath(ctx.analysis_result)  # raises OathViolation on failure

            # Generate a handoff token for human reviewer
            ctx.handoff_token = str(uuid.uuid4())

            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=True,
                duration_ms=duration,
                output={
                    "handoff_token": ctx.handoff_token,
                    "analysis_status": ctx.analysis_result.status.value,
                    "oath_verified": True,
                },
            )
        except OathViolation as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=f"OathViolation: {e}",
            )
        except Exception as e:
            duration = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            return StageResult(
                stage=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )

    def rollback(self, ctx: PipelineContext) -> None:
        ctx.handoff_token = None


# ---------------------------------------------------------------------------
# Orchestrator — runs all 6 stages
# ---------------------------------------------------------------------------

class LegalAnalysisPipeline:
    """
    Orchestrates the mandatory 6-stage workflow.

    Usage:
        pipeline = LegalAnalysisPipeline()
        ctx = PipelineContext(input=CaseInput(...))
        result = await pipeline.execute(ctx)
    """

    STAGES: list[PipelineStage] = [
        IntakeAndSanitizeStage(),
        FiqhRootingStage(),
        KnowledgeRetrievalStage(),
        AppealDraftingStage(),
        ArchiveVersionStage(),
        HumanReviewHandoffStage(),
    ]

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
        llm_provider: LLMProvider | None = None,
        archive_sink: ArchiveSink | None = None,
    ) -> None:
        # Inject dependencies into stages that need them
        self._stages: list[PipelineStage] = [
            IntakeAndSanitizeStage(),
            FiqhRootingStage(),
            KnowledgeRetrievalStage(retriever=retriever),
            AppealDraftingStage(llm_provider=llm_provider),
            ArchiveVersionStage(archive_sink=archive_sink),
            HumanReviewHandoffStage(),
        ]

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """Run all stages in order. Returns the enriched context."""
        ctx.started_at = datetime.now(timezone.utc).isoformat()

        for stage in self._stages:
            result = await stage.execute(ctx)
            ctx.add_stage(result)

            if not result.passed:
                # Rollback this stage and stop
                stage.rollback(ctx)
                ctx.completed_at = datetime.now(timezone.utc).isoformat()
                raise StageFailedError(stage.name, result.error or "unknown", ctx)

        ctx.completed_at = datetime.now(timezone.utc).isoformat()
        return ctx

    def get_stages(self) -> list[PipelineStage]:
        return self._stages


__all__ = [
    "PipelineStatus",
    "CaseInput",
    "StageResult",
    "PipelineContext",
    "StageFailedError",
    "PipelineStage",
    "IntakeAndSanitizeStage",
    "FiqhRootingStage",
    "KnowledgeRetrievalStage",
    "KnowledgeRetriever",
    "AppealDraftingStage",
    "LLMProvider",
    "ArchiveVersionStage",
    "ArchiveSink",
    "HumanReviewHandoffStage",
    "LegalAnalysisPipeline",
]
