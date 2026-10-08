PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS memory_objects (
 memory_id TEXT PRIMARY KEY, memory_type TEXT NOT NULL, title TEXT NOT NULL, topic TEXT,
 subtopics_json TEXT NOT NULL DEFAULT '[]', document_type TEXT, document_number TEXT,
 document_date TEXT, issuing_authority TEXT, source_id TEXT, source_url TEXT, drive_file_id TEXT,
 drive_url TEXT, page TEXT, section TEXT, important_text TEXT, concept_summary TEXT,
 keywords_json TEXT NOT NULL DEFAULT '[]', effective_from TEXT, effective_to TEXT,
 validity_status TEXT NOT NULL DEFAULT 'unknown', source_confidence REAL,
 inference_confidence REAL, provenance_json TEXT NOT NULL DEFAULT '{}', source_hash TEXT,
 version INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'active',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_used_at TEXT,
 use_count INTEGER NOT NULL DEFAULT 0, correction_count INTEGER NOT NULL DEFAULT 0,
 rejection_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_memory_topic ON memory_objects(topic);
CREATE INDEX IF NOT EXISTS idx_memory_doc_number ON memory_objects(document_number);
CREATE INDEX IF NOT EXISTS idx_memory_drive_file ON memory_objects(drive_file_id);
CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_objects(status);
CREATE INDEX IF NOT EXISTS idx_memory_validity ON memory_objects(validity_status);
CREATE TABLE IF NOT EXISTS memory_relations (
 relation_id TEXT PRIMARY KEY, from_memory_id TEXT NOT NULL, to_memory_id TEXT NOT NULL,
 relation_type TEXT NOT NULL, confidence REAL, evidence TEXT, created_at TEXT NOT NULL,
 created_by TEXT NOT NULL DEFAULT 'system',
 FOREIGN KEY(from_memory_id) REFERENCES memory_objects(memory_id),
 FOREIGN KEY(to_memory_id) REFERENCES memory_objects(memory_id)
);
CREATE INDEX IF NOT EXISTS idx_rel_from ON memory_relations(from_memory_id);
CREATE INDEX IF NOT EXISTS idx_rel_to ON memory_relations(to_memory_id);
CREATE TABLE IF NOT EXISTS memory_feedback (
 feedback_id TEXT PRIMARY KEY, memory_id TEXT NOT NULL, feedback_type TEXT NOT NULL,
 note TEXT, replacement_memory_id TEXT, created_at TEXT NOT NULL,
 created_by TEXT NOT NULL DEFAULT 'owner',
 FOREIGN KEY(memory_id) REFERENCES memory_objects(memory_id)
);
CREATE TABLE IF NOT EXISTS audit_events (
 audit_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, object_type TEXT NOT NULL,
 object_id TEXT NOT NULL, actor TEXT NOT NULL, old_value_json TEXT,
 new_value_json TEXT, reason TEXT, source TEXT, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_object ON audit_events(object_type, object_id);
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
 memory_id UNINDEXED, title, topic, document_number, issuing_authority,
 important_text, concept_summary, keywords
);
