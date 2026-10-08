from pathlib import Path
import os
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .model import Feedback, MemoryObject, Relation
from .service import SecondBrainService

ROOT=Path(__file__).resolve().parents[2]
DB=Path(os.getenv("SECOND_BRAIN_DB_PATH", str(ROOT/"data"/"private_second_brain.sqlite3")))
service=SecondBrainService(DB)
router=APIRouter(prefix="/v1/memory", tags=["second-brain"])

def guard(scope):
    if scope not in {"owner","personal-bot"}:
        raise HTTPException(403,"private memory scope required")

class SearchIn(BaseModel):
    query:str=Field(...,min_length=2,max_length=2000)
    limit:int=Field(10,ge=1,le=50)

class IngestIn(BaseModel):
    memory: dict
    actor:str="owner"

class FeedbackIn(BaseModel):
    memory_id:str
    feedback_type:str
    note:str|None=None
    replacement_memory_id:str|None=None

@router.get("/health")
async def health():
    return {"status":"ok","scope":"owner/personal-bot","private":True}

@router.post("/search")
async def search(b:SearchIn,x_memory_scope:str|None=Header(None)):
    guard(x_memory_scope)
    return {"items":service.search(b.query,b.limit)}

@router.post("/ingest")
async def ingest(b:IngestIn,x_memory_scope:str|None=Header(None)):
    guard(x_memory_scope)
    try: memory=MemoryObject(**b.memory)
    except Exception as e: raise HTTPException(422,f"invalid memory: {e}")
    return {"memory_id":service.upsert_memory(memory,b.actor)}

@router.get("/{memory_id}")
async def get(memory_id:str,x_memory_scope:str|None=Header(None)):
    guard(x_memory_scope)
    x=service.get(memory_id)
    if not x: raise HTTPException(404,"memory not found")
    return x

@router.get("/{memory_id}/relations")
async def relations(memory_id:str,x_memory_scope:str|None=Header(None)):
    guard(x_memory_scope)
    x=service.get(memory_id)
    if not x: raise HTTPException(404,"memory not found")
    return {"items":x["relations"]}

@router.post("/feedback")
async def feedback(b:FeedbackIn,x_memory_scope:str|None=Header(None)):
    guard(x_memory_scope)
    try: service.feedback(Feedback(**b.model_dump()))
    except KeyError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(422,str(e))
    return {"ok":True}
