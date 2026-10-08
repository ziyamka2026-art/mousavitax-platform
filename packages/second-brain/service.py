"""SQLite-backed private memory service."""
from __future__ import annotations
import hashlib,json,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .model import FEEDBACK_TYPES,MEMORY_TYPES,RELATION_TYPES,VALIDITY_STATUSES,Feedback,MemoryObject,Relation
def _now(): return datetime.now(timezone.utc).isoformat()
def _id(prefix): return f"{prefix}-{uuid.uuid4().hex[:16]}"
def _json(value): return json.dumps(value,ensure_ascii=False,separators=(",",":"))
def content_hash(text): return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
class SecondBrainService:
    def __init__(self,db_path):
        self.db_path=Path(db_path); self.db_path.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as db: db.executescript((Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8"))
    def _connect(self):
        db=sqlite3.connect(self.db_path); db.row_factory=sqlite3.Row; db.execute("PRAGMA foreign_keys=ON"); return db
    def upsert_memory(self,memory,actor="system"):
        if memory.memory_type not in MEMORY_TYPES: raise ValueError("invalid memory_type")
        if memory.validity_status not in VALIDITY_STATUSES: raise ValueError("invalid validity_status")
        now=_now()
        with self._connect() as db:
            old=db.execute("SELECT version FROM memory_objects WHERE memory_id=?",(memory.memory_id,)).fetchone()
            version=int(old["version"])+1 if old else memory.version
            db.execute("""INSERT INTO memory_objects
            (memory_id,memory_type,title,topic,subtopics_json,document_type,document_number,document_date,issuing_authority,source_id,source_url,drive_file_id,drive_url,page,section,important_text,concept_summary,keywords_json,effective_from,effective_to,validity_status,source_confidence,inference_confidence,provenance_json,source_hash,version,status,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(memory_id) DO UPDATE SET
            memory_type=excluded.memory_type,title=excluded.title,topic=excluded.topic,subtopics_json=excluded.subtopics_json,document_type=excluded.document_type,document_number=excluded.document_number,document_date=excluded.document_date,issuing_authority=excluded.issuing_authority,source_id=excluded.source_id,source_url=excluded.source_url,drive_file_id=excluded.drive_file_id,drive_url=excluded.drive_url,page=excluded.page,section=excluded.section,important_text=excluded.important_text,concept_summary=excluded.concept_summary,keywords_json=excluded.keywords_json,effective_from=excluded.effective_from,effective_to=excluded.effective_to,validity_status=excluded.validity_status,source_confidence=excluded.source_confidence,inference_confidence=excluded.inference_confidence,provenance_json=excluded.provenance_json,source_hash=excluded.source_hash,version=excluded.version,status=excluded.status,updated_at=excluded.updated_at""",
            (memory.memory_id,memory.memory_type,memory.title,memory.topic,_json(memory.subtopics),memory.document_type,memory.document_number,memory.document_date,memory.issuing_authority,memory.source_id,memory.source_url,memory.drive_file_id,memory.drive_url,memory.page,memory.section,memory.important_text,memory.concept_summary,_json(memory.keywords),memory.effective_from,memory.effective_to,memory.validity_status,memory.source_confidence,memory.inference_confidence,_json(memory.provenance),memory.source_hash,version,memory.status,now,now))
            db.execute("DELETE FROM memory_fts WHERE memory_id=?",(memory.memory_id,))
            db.execute("INSERT INTO memory_fts VALUES (?,?,?,?,?,?,?,?)",(memory.memory_id,memory.title,memory.topic,memory.document_number,memory.issuing_authority,memory.important_text,memory.concept_summary," ".join(memory.keywords)))
            self._audit(db,"memory_upserted","memory",memory.memory_id,actor,None,memory.__dict__,"memory ingest/update",memory.source_url or memory.drive_url)
        return memory.memory_id
    def add_relation(self,relation,actor="system"):
        if relation.relation_type not in RELATION_TYPES: raise ValueError("invalid relation_type")
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO memory_relations VALUES (?,?,?,?,?,?,?,?)",(relation.relation_id,relation.from_memory_id,relation.to_memory_id,relation.relation_type,relation.confidence,relation.evidence,_now(),actor))
            self._audit(db,"relation_added","relation",relation.relation_id,actor,None,relation.__dict__,"relationship indexing",None)
        return relation.relation_id
    def search(self,query,limit=10):
        limit=max(1,min(limit,50))
        with self._connect() as db:
            rows=db.execute("SELECT m.*,bm25(memory_fts) AS rank FROM memory_fts JOIN memory_objects m ON m.memory_id=memory_fts.memory_id WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?",(query,limit)).fetchall()
            return [dict(r) for r in rows]
    def get(self,memory_id):
        with self._connect() as db:
            row=db.execute("SELECT * FROM memory_objects WHERE memory_id=?",(memory_id,)).fetchone()
            if not row:return None
            rel=db.execute("SELECT * FROM memory_relations WHERE from_memory_id=? OR to_memory_id=?",(memory_id,memory_id)).fetchall()
            return {"memory":dict(row),"relations":[dict(r) for r in rel]}
    def feedback(self,item,actor="owner"):
        if item.feedback_type not in FEEDBACK_TYPES: raise ValueError("invalid feedback_type")
        with self._connect() as db:
            if not db.execute("SELECT 1 FROM memory_objects WHERE memory_id=?",(item.memory_id,)).fetchone(): raise KeyError("memory not found")
            db.execute("INSERT INTO memory_feedback VALUES (?,?,?,?,?,?,?)",(_id("feedback"),item.memory_id,item.feedback_type,item.note,item.replacement_memory_id,_now(),actor))
            if item.feedback_type=="confirm": db.execute("UPDATE memory_objects SET inference_confidence=MIN(COALESCE(inference_confidence,0)+0.1,1),last_used_at=? WHERE memory_id=?",(_now(),item.memory_id))
            elif item.feedback_type=="correct": db.execute("UPDATE memory_objects SET correction_count=correction_count+1,status='review_required',last_used_at=? WHERE memory_id=?",(_now(),item.memory_id))
            elif item.feedback_type=="reject": db.execute("UPDATE memory_objects SET rejection_count=rejection_count+1,status='rejected',last_used_at=? WHERE memory_id=?",(_now(),item.memory_id))
            elif item.feedback_type=="supersede": db.execute("UPDATE memory_objects SET status='superseded',last_used_at=? WHERE memory_id=?",(_now(),item.memory_id))
            self._audit(db,"memory_feedback","memory",item.memory_id,actor,None,item.__dict__,item.feedback_type,None)
    def _audit(self,db,event_type,object_type,object_id,actor,old,new,reason,source):
        db.execute("INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?)",(_id("audit"),event_type,object_type,object_id,actor,_json(old) if old is not None else None,_json(new) if new is not None else None,reason,source,_now()))
