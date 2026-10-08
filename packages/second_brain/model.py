from dataclasses import dataclass,field
from typing import Any
MEMORY_TYPES={"document","experience","inference","observation","hypothesis"}
VALIDITY_STATUSES={"valid","superseded","repealed","unknown","review_required"}
RELATION_TYPES={"related_to","amends","supersedes","interprets","interpreted_by","cites","used_in","derived_from","contradicts","supports","same_subject"}
FEEDBACK_TYPES={"confirm","correct","reject","supersede"}
@dataclass
class MemoryObject:
 memory_id:str; memory_type:str; title:str; topic:str|None=None; subtopics:list[str]=field(default_factory=list)
 document_type:str|None=None; document_number:str|None=None; document_date:str|None=None; issuing_authority:str|None=None
 source_id:str|None=None; source_url:str|None=None; drive_file_id:str|None=None; drive_url:str|None=None
 page:str|None=None; section:str|None=None; important_text:str|None=None; concept_summary:str|None=None; keywords:list[str]=field(default_factory=list)
 effective_from:str|None=None; effective_to:str|None=None; validity_status:str="unknown"; source_confidence:float|None=None; inference_confidence:float|None=None
 provenance:dict[str,Any]=field(default_factory=dict); source_hash:str|None=None; version:int=1; status:str="active"
@dataclass
class Relation:
 relation_id:str; from_memory_id:str; to_memory_id:str; relation_type:str; confidence:float|None=None; evidence:str|None=None
@dataclass
class Feedback:
 memory_id:str; feedback_type:str; note:str|None=None; replacement_memory_id:str|None=None
