from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,Field
from .service import SecondBrainService
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[2]
DB=Path(os.getenv("SECOND_BRAIN_DB_PATH",ROOT/"data"/"private_second_brain.sqlite3"))
service=SecondBrainService(DB)
router=APIRouter(prefix="/v1/memory",tags=["second-brain"])
def guard(scope):
 if scope not in {"owner","personal-bot"}:raise HTTPException(403,"private memory scope required")
class SearchIn(BaseModel):
 query:str=Field(...,min_length=2,max_length=2000);limit:int=Field(10,ge=1,le=50)
@router.get("/health")
async def health():return {"status":"ok","scope":"owner-only"}
@router.post("/search")
async def search(b:SearchIn,x_memory_scope:str|None=Header(None)):
 guard(x_memory_scope);return {"items":service.search(b.query,b.limit)}
@router.get("/{memory_id}")
async def get(memory_id:str,x_memory_scope:str|None=Header(None)):
 guard(x_memory_scope);x=service.get(memory_id)
 if not x:raise HTTPException(404,"memory not found")
 return x
