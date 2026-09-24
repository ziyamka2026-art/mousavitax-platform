"""Audit procedure API routes – ماده ۲۱۹ / ۲۰۰/۹۹/۵۲۲."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/tax/audit-procedure", tags=["audit-procedure"])

ROOT = Path(__file__).resolve().parents[3]

try:
    from taxlaw_engine import (
        AuditProcedureInput,
        calculate_audit_procedure,
        audit_procedure_meta,
        run_audit_procedure_smoke,
    )
except ImportError:
    calculate_audit_procedure = None  # type: ignore
    audit_procedure_meta = None  # type: ignore
    run_audit_procedure_smoke = None  # type: ignore


class AuditProcedureRequest(BaseModel):
    taxpayer_kind: str = "legal"
    year: int = 1402
    invitation_received: bool = True
    attended_on_time: bool = True
    current_audit_type: str = "administrative"
    books_status: str = "full"
    docs_status: str = "full"
    revenue_docs: str = "full"
    cost_docs: str = "full"
    legal_books_provided: bool = True
    paper_company_tx: bool = False
    related_party_below_fair: bool = False
    related_party_above_fair: bool = False
    concealment_activity: bool = False
    concealment_revenue: bool = False
    opex_accepted_on_concealment: str = "na"
    facts_summary: str = ""
    taxpayer_name: Optional[str] = None


@router.get("/meta")
async def meta():
    if audit_procedure_meta is None:
        raise HTTPException(status_code=503, detail="audit-procedure engine not installed")
    return audit_procedure_meta()


@router.post("/calculate")
async def calculate(body: AuditProcedureRequest):
    if calculate_audit_procedure is None:
        raise HTTPException(status_code=503, detail="audit-procedure engine not installed")
    inp = AuditProcedureInput(
        taxpayer_kind="sole" if body.taxpayer_kind == "sole" else "legal",
        year=body.year,
        invitation_received=body.invitation_received,
        attended_on_time=body.attended_on_time,
        current_audit_type=body.current_audit_type
        if body.current_audit_type in ("administrative", "field", "unknown")
        else "administrative",  # type: ignore
        books_status=body.books_status if body.books_status in ("full", "partial", "none") else "full",  # type: ignore
        docs_status=body.docs_status if body.docs_status in ("full", "partial", "none") else "full",  # type: ignore
        revenue_docs=body.revenue_docs if body.revenue_docs in ("full", "partial", "none") else "full",  # type: ignore
        cost_docs=body.cost_docs
        if body.cost_docs in ("full", "partial_cogs", "partial_opex", "none")
        else "full",  # type: ignore
        legal_books_provided=body.legal_books_provided,
        paper_company_tx=body.paper_company_tx,
        related_party_below_fair=body.related_party_below_fair,
        related_party_above_fair=body.related_party_above_fair,
        concealment_activity=body.concealment_activity,
        concealment_revenue=body.concealment_revenue,
        opex_accepted_on_concealment=body.opex_accepted_on_concealment
        if body.opex_accepted_on_concealment in ("yes", "no", "na")
        else "na",  # type: ignore
        facts_summary=body.facts_summary or "",
    )
    result = calculate_audit_procedure(inp)
    out = result.to_dict()
    out["taxpayer_name"] = body.taxpayer_name
    out["human_review_required"] = True

    log_path = ROOT / "data" / "audit_procedure_logs.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_id = f"aud-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "id": log_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "inputs": body.model_dump(),
                    "outputs": {k: out[k] for k in out if k not in ("disclaimer", "sources")},
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    out["log_id"] = log_id
    return out


@router.get("/smoke")
async def smoke():
    if run_audit_procedure_smoke is None:
        raise HTTPException(status_code=503, detail="audit-procedure engine not installed")
    return {"tests": run_audit_procedure_smoke()}
