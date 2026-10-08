from __future__ import annotations
import hashlib,json,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path
from .model import MEMORY_TYPES,VALIDITY_STATUSES,RELATION_TYPES,FEEDBACK_TYPES
def now(): return datetime.now(timezone.utc).isoformat()
def uid(p): return f"{p}-{uuid.uuid4().hex[:16]}"
def js(x): return json.dumps(x,ensure_ascii=False,separators=(",",":"))
def content_hash(x): return hashlib.sha256((x or "").encode("utf-8")).hexdigest()
class SecondBrainService:
 def __init__(self,db_path):
  self.db_path=Path(db_path); self.db_path.parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:c.executescript((Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8"))
 def db(self):
  c=sqlite3.connect(self.db_path); c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");return c
 def search(self,q,limit=10):
  with self.db() as c:return [dict(x) for x in c.execute("SELECT m.*,bm25(memory_fts) rank FROM memory_fts JOIN memory_objects m ON m.memory_id=memory_fts.memory_id WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?",(q,max(1,min(limit,50))).fetchall())]
 def get(self,i):
  with self.db() as c:
   x=c.execute("SELECT * FROM memory_objects WHERE memory_id=?",(i,)).fetchone()
   if not x:return None
   r=c.execute("SELECT * FROM memory_relations WHERE from_memory_id=? OR to_memory_id=?",(i,i)).fetchall()
   return {"memory":dict(x),"relations":[dict(v) for v in r]}
 def audit(self,c,typ,obj,i,actor,new,reason,source=None):
  c.execute("INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?)",(uid("audit"),typ,obj,i,actor,None,js(new),reason,source,now()))
