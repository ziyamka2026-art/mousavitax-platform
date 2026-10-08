from __future__ import annotations
import os
from pathlib import Path
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,Field
from .model import Feedback
from .service import SecondBrainService
ROOT=Path(__file__).resolve().parents[2]
DB_PATH=Path(os.getenv("SECOND_BRAIN_DB_PATH",ROOT/"data"/"private_second_brain.sqlite3"))
service=SecondBrainService(DB_PATH)
router=APIRouter(prefix="/v1/memory",tags=["second-brain"])
def _owner_guard(scope):
    if scope not in {"owner","personal-bot"}: raise HTTPException(status_code=403,detail="private memory scope required")
class SearchIn(BaseModel):
    query:str=Field(...,min_length=2,max_length=2000)
    limit:int=Field(default=10,ge=1,le=50)
class FeedbackIn(BaseModel):
    memory_id:str; feedback_type:str; note:str|None=None; replacement_memory_id:str|None=None
@router.get("/health")
async def memory_health(): return {"status":"ok","scope":"owner-only","database":str(DB_PATH)}
@router.post("/search")
async def memory_search(body:SearchIn,x_memory_scope:str|None=Header(default=None)):
    _owner_guard(x_memory_scope); return {"items":service.search(body.query,body.limit)}
@router.get("/{memory_id}")
async def memory_get(memory_id:str,x_memory_scope:str|None=Header(default=None)):
    _owner_guard(x_memory_scope); item=service.get(memory_id)
    if not item: raise HTTPException(status_code=404,detail="memory not found")
    return item
@router.post("/feedback")
async def memory_feedback(body:FeedbackIn,x_memory_scope:str|None=Header(default=None)):
    _owner_guard(x_memory_scope); service.feedback(Feedback(body.memory_id,body.feedback_type,body.note,body.replacement_memory_id)); return {"ok":True}
