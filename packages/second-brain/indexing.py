from __future__ import annotations
import re
from typing import Any,Iterable
from .model import MemoryObject
from .service import SecondBrainService,content_hash
def _first(patterns,text):
    for pattern in patterns:
        m=re.search(pattern,text or "",flags=re.MULTILINE|re.IGNORECASE)
        if m:return m.group(1).strip()
    return None
def extract_metadata(text):
    return {"document_number":_first([r"(?:شماره|شماره بخشنامه|شماره دستورالعمل)\s*[:：]?\s*([\d۰-۹٠-٩\-/]+)"],text),
            "document_date":_first([r"(?:تاریخ|مورخ)\s*[:：]?\s*([\d۰-۹٠-٩\-/]+)"],text),
            "issuing_authority":_first([r"(?:مرجع صادرکننده|صادرکننده|مرجع)\s*[:：]?\s*(.+)"],text)}
def index_drive_records(service,records):
    count=0
    for rec in records:
        text=rec.get("text") or ""; meta=extract_metadata(text); file_id=rec.get("drive_file_id")
        memory_id=f"drive-{file_id}" if file_id else f"doc-{content_hash(text)[:16]}"
        memory=MemoryObject(memory_id=memory_id,memory_type="document",title=rec.get("title") or "Drive document",
            topic=rec.get("topic"),document_type=rec.get("document_type"),document_number=rec.get("document_number") or meta.get("document_number"),
            document_date=rec.get("document_date") or meta.get("document_date"),issuing_authority=rec.get("issuing_authority") or meta.get("issuing_authority"),
            source_id=rec.get("source_id") or memory_id,source_url=rec.get("source_url"),drive_file_id=file_id,drive_url=rec.get("drive_url"),
            page=str(rec.get("page")) if rec.get("page") is not None else None,section=rec.get("section"),
            important_text=rec.get("important_text") or text[:4000],concept_summary=rec.get("concept_summary") or text[:1000],
            keywords=list(rec.get("keywords") or []),effective_from=rec.get("effective_from"),effective_to=rec.get("effective_to"),
            validity_status=rec.get("validity_status","unknown"),source_confidence=rec.get("source_confidence",0.9),
            provenance={"source":"google_drive","connector_record":True},source_hash=content_hash(text))
        service.upsert_memory(memory,actor="drive-indexer"); count+=1
    return count
