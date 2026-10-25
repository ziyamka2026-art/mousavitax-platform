"""
Unit tests for the LegalAnalysisPipeline (6-stage workflow).

These tests use stubs for retriever/llm/archive to verify orchestration
logic without external services.
"""

import asyncio
import pytest

from apps.api.app.orchestrator.pipeline import (
    AppealDraftingStage,
    ArchiveVersionStage,
    CaseInput,
    FiqhRootingStage,
    HumanReviewHandoffStage,
    IntakeAndSanitizeStage,
    KnowledgeRetrievalStage,
    LegalAnalysisPipeline,
    PipelineContext,
    PipelineStatus,
    StageFailedError,
)


def _input(**overrides) -> CaseInput:
    defaults = {
        "case_id": "CASE-001",
        "tenant_id": "TENANT-A",
        "user_id": "USER-1",
        "question": "مؤدی به کتمان درآمد متهم شده.",
        "documents": [],
        "metadata": {},
    }
    defaults.update(overrides)
    return CaseInput(**defaults)


def _ctx(**overrides) -> PipelineContext:
    return PipelineContext(input=_input(**overrides))


# ---------------------------------------------------------------------------
# Stage 1: Intake & PII Sanitization
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_1_redacts_national_id():
    ctx = _ctx(question="کد ملی من 1234567890 است.")
    stage = IntakeAndSanitizeStage()
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert "1234567890" not in ctx.sanitized_content
    assert "[NATIONAL_ID]" in ctx.sanitized_content


@pytest.mark.unit
def test_stage_1_redacts_phone_in_documents():
    ctx = _ctx(
        question="سؤال",
        documents=[{"content": "تماس: 09123456789"}],
    )
    stage = IntakeAndSanitizeStage()
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert "09123456789" not in ctx.input.documents[0]["content"]


@pytest.mark.unit
def test_stage_1_handles_empty_question():
    ctx = _ctx(question="")
    stage = IntakeAndSanitizeStage()
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert ctx.sanitized_content == ""


# ---------------------------------------------------------------------------
# Stage 2: Fiqh Rooting
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_2_passes_on_clean_input():
    ctx = _ctx(question="تحلیل حقوقی درباره ارزش افزوده.")
    # Pre-populate sanitized content (since stage 1 isn't run)
    ctx.sanitized_content = ctx.input.question
    stage = FiqhRootingStage()
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert ctx.fiqh_report is not None
    assert ctx.fiqh_report.overall_passed


@pytest.mark.unit
def test_stage_2_detects_ambiguity_and_validates():
    ctx = _ctx(question="قانون در این مورد مبهم است.")
    ctx.sanitized_content = ctx.input.question
    stage = FiqhRootingStage()
    result = asyncio.run(stage.execute(ctx))
    # Ambiguity without pro-taxpayer mention → should fail
    assert not result.passed
    assert "تفسیر مضیق" in (result.error or "")


@pytest.mark.unit
def test_stage_2_detects_concealment_claim():
    ctx = _ctx(question="مؤدی به کتمان درآمد متهم شده.")
    ctx.sanitized_content = ctx.input.question
    stage = FiqhRootingStage()
    result = asyncio.run(stage.execute(ctx))
    # The burden_of_proof should be auto-set to 'administration'
    # → this rule should pass
    assert result.passed


# ---------------------------------------------------------------------------
# Stage 3: Knowledge Retrieval (stub mode)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_3_stub_returns_empty():
    ctx = _ctx()
    ctx.sanitized_content = "سؤال"
    stage = KnowledgeRetrievalStage(retriever=None)
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert ctx.retrieved_citations == []


@pytest.mark.unit
def test_stage_3_with_injected_retriever():
    class MockRetriever:
        async def search(self, query, limit=6):
            return [
                {"source_type": "law", "source_id": "qmm-251-m",
                 "title": "ماده ۲۵۱ مکرر ق.م.م",
                 "effective_date": "2008-01-01",
                 "url": "https://example.com/qmm-251-m"},
            ]
    ctx = _ctx()
    ctx.sanitized_content = "سؤال درباره اعتراض."
    stage = KnowledgeRetrievalStage(retriever=MockRetriever())
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert len(ctx.retrieved_citations) == 1
    assert ctx.retrieved_citations[0].title == "ماده ۲۵۱ مکرر ق.م.م"


# ---------------------------------------------------------------------------
# Stage 4: Appeal Drafting
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_4_stub_generates_draft():
    ctx = _ctx()
    ctx.sanitized_content = "سؤال درباره ارزش افزوده."
    stage = AppealDraftingStage(llm_provider=None)
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert "پیش‌نویس لایحه" in ctx.draft_content
    assert "CASE-001" in ctx.draft_content


# ---------------------------------------------------------------------------
# Stage 5: Archival Version
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_5_creates_pending_human_review_result():
    ctx = _ctx()
    ctx.sanitized_content = "سؤال."
    ctx.draft_content = "پیش‌نویس متن تحلیل."
    stage = ArchiveVersionStage(archive_sink=None)
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert ctx.analysis_result is not None
    # CRITICAL: AI must NOT set FINAL — only PENDING_HUMAN_REVIEW
    assert ctx.analysis_result.status.value == "pending_human_review"
    assert ctx.analysis_result.case_id == "CASE-001"


@pytest.mark.unit
def test_stage_5_with_injected_sink():
    class MockSink:
        async def archive(self, result):
            return "archive-001"
    ctx = _ctx()
    ctx.sanitized_content = "سؤال."
    ctx.draft_content = "پیش‌نویس."
    stage = ArchiveVersionStage(archive_sink=MockSink())
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert ctx.archive_id == "archive-001"


# ---------------------------------------------------------------------------
# Stage 6: Human Review Handoff — the Oath Guard gate
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_6_blocks_when_no_analysis():
    ctx = _ctx()
    # Skip stages 1-5 — analysis_result is None
    stage = HumanReviewHandoffStage()
    result = asyncio.run(stage.execute(ctx))
    assert not result.passed
    assert "no analysis" in (result.error or "")


@pytest.mark.unit
def test_stage_6_blocks_when_oath_violation_no_citations():
    """Oath Clause 2: بدون مستند سخن نگویم."""
    from packages.oath.runtime_guards import AnalysisResult, AnalysisStatus
    ctx = _ctx()
    ctx.analysis_result = AnalysisResult(
        content="تحلیل بدون citation.",
        citations=[],
        case_id="CASE-001",
        status=AnalysisStatus.PENDING_HUMAN_REVIEW,
    )
    stage = HumanReviewHandoffStage()
    result = asyncio.run(stage.execute(ctx))
    assert not result.passed
    assert "OathViolation" in (result.error or "")


@pytest.mark.unit
def test_stage_6_blocks_when_ai_set_final():
    """Oath Clause 6: تصمیم نهایی به انسان واگذار شود."""
    from packages.oath.runtime_guards import AnalysisResult, AnalysisStatus, Citation
    ctx = _ctx()
    ctx.analysis_result = AnalysisResult(
        content="تحلیل.",
        citations=[Citation(source_type="law", source_id="x", title="x")],
        case_id="CASE-001",
        status=AnalysisStatus.FINAL,  # ILLEGAL — AI cannot set FINAL
    )
    stage = HumanReviewHandoffStage()
    result = asyncio.run(stage.execute(ctx))
    assert not result.passed
    assert "require_human_review" in (result.error or "")


@pytest.mark.unit
def test_stage_6_passes_with_valid_pending_result():
    from packages.oath.runtime_guards import AnalysisResult, AnalysisStatus, Citation
    ctx = _ctx()
    ctx.analysis_result = AnalysisResult(
        content="تحلیل.",
        citations=[Citation(source_type="law", source_id="x", title="x")],
        case_id="CASE-001",
        status=AnalysisStatus.PENDING_HUMAN_REVIEW,
    )
    stage = HumanReviewHandoffStage()
    result = asyncio.run(stage.execute(ctx))
    assert result.passed
    assert ctx.handoff_token is not None
    assert len(ctx.handoff_token) > 0


# ---------------------------------------------------------------------------
# Full Pipeline — End-to-End Integration
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_full_pipeline_runs_all_six_stages_in_order():
    # Inject a mock retriever so stage 3 returns citations (needed for oath guard)
    class MockRetriever:
        async def search(self, query, limit=6):
            return [
                {"source_type": "law", "source_id": "qmm-1",
                 "title": "ماده ۱ ق.م.م", "effective_date": "2008-01-01"},
            ]
    class MockSink:
        async def archive(self, result):
            return "ARCH-001"
    ctx = _ctx(question="تحلیل حقوقی درباره ارزش افزوده انجام شود.")
    pipeline = LegalAnalysisPipeline(
        retriever=MockRetriever(),
        archive_sink=MockSink(),
    )
    result_ctx = asyncio.run(pipeline.execute(ctx))

    assert len(result_ctx.stages_log) == 6
    stage_names = [r.stage for r in result_ctx.stages_log]
    assert stage_names == [
        "intake_and_sanitize",
        "fiqh_rooting",
        "knowledge_retrieval",
        "appeal_drafting",
        "archive_version",
        "human_review_handoff",
    ]
    assert all(r.passed for r in result_ctx.stages_log)
    assert result_ctx.handoff_token is not None


@pytest.mark.unit
def test_full_pipeline_fails_fast_when_fiqh_violation():
    # Ambiguity without pro-taxpayer mention → fiqh fails at stage 2
    ctx = _ctx(question="قانون در این مورد مبهم است و نیاز به تحلیل دارد.")
    pipeline = LegalAnalysisPipeline()
    with pytest.raises(StageFailedError) as exc_info:
        asyncio.run(pipeline.execute(ctx))
    assert "fiqh_rooting" in str(exc_info.value)
    # Stages 1 (intake) and 2 (fiqh) should be logged; stages 3-6 should NOT run
    assert len(ctx.stages_log) == 2
    assert ctx.stages_log[0].stage == "intake_and_sanitize"
    assert ctx.stages_log[0].passed
    assert ctx.stages_log[1].stage == "fiqh_rooting"
    assert not ctx.stages_log[1].passed


@pytest.mark.unit
def test_full_pipeline_injects_dependencies():
    """Verify DI works — retriever and sink are used in their stages."""
    class MockRetriever:
        async def search(self, query, limit=6):
            return [
                {"source_type": "law", "source_id": "x",
                 "title": "ماده قانونی", "effective_date": "2008-01-01"},
            ]

    class MockSink:
        async def archive(self, result):
            return "ARCHIVE-ID-123"

    ctx = _ctx(question="تحلیل حقوقی درباره اظهارنامه.")
    pipeline = LegalAnalysisPipeline(
        retriever=MockRetriever(),
        archive_sink=MockSink(),
    )
    result_ctx = asyncio.run(pipeline.execute(ctx))
    assert all(r.passed for r in result_ctx.stages_log)
    assert len(result_ctx.retrieved_citations) == 1
    assert result_ctx.archive_id == "ARCHIVE-ID-123"


# ---------------------------------------------------------------------------
# Pipeline Status Enum
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_pipeline_status_enum_has_seven_states():
    states = {s.value for s in PipelineStatus}
    assert states == {
        "intake", "fiqh_rooting", "retrieval",
        "drafting", "archival", "handoff",
        "completed", "failed",
    }


# ---------------------------------------------------------------------------
# Rollback safety
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_stage_1_rollback_clears_sanitized_content():
    ctx = _ctx(question="test")
    ctx.sanitized_content = "stale data"
    stage = IntakeAndSanitizeStage()
    stage.rollback(ctx)
    assert ctx.sanitized_content == ""


@pytest.mark.unit
def test_stage_5_rollback_clears_analysis_result():
    from packages.oath.runtime_guards import AnalysisResult
    ctx = _ctx()
    ctx.analysis_result = AnalysisResult(content="x")
    stage = ArchiveVersionStage()
    stage.rollback(ctx)
    assert ctx.analysis_result is None
    assert ctx.archive_id is None
