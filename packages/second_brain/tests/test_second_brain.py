import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))
from second_brain.model import MemoryObject, Relation, Feedback
from second_brain.service import SecondBrainService, content_hash

def make_memory(text="قانون مالیات بر ارزش افزوده"):
    return MemoryObject(
        memory_id="m1", memory_type="document", title="قانون مالیات",
        topic="مالیات بر ارزش افزوده", important_text=text,
        concept_summary="مقررات مالیاتی", keywords=["مالیات","ارزش افزوده"],
        source_id="SRC-1", source_hash=content_hash(text)
    )

def test_roundtrip_and_fts(tmp_path):
    s=SecondBrainService(tmp_path/"brain.sqlite3")
    m=make_memory()
    assert s.upsert_memory(m)=="m1"
    assert s.search("مالیات")
    assert s.get("m1")["memory"]["version"]==1
    assert s.upsert_memory(m)=="m1"
    assert s.get("m1")["memory"]["version"]==1

def test_relation_and_feedback(tmp_path):
    s=SecondBrainService(tmp_path/"brain.sqlite3")
    s.upsert_memory(make_memory())
    rel=Relation(relation_id="r1",from_memory_id="m1",to_memory_id="m1",relation_type="same_subject")
    s.add_relation(rel)
    s.feedback(Feedback(memory_id="m1",feedback_type="confirm"))
    got=s.get("m1")
    assert len(got["relations"])==1
    assert got["memory"]["last_used_at"] is not None

def test_hash_changes():
    assert content_hash("الف") != content_hash("ب")
