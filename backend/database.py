from __future__ import annotations
import sqlite3
import json
import hashlib
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    api_available INTEGER NOT NULL DEFAULT 1,
    base_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    max_results INTEGER NOT NULL,
    from_year INTEGER,
    to_year INTEGER,
    iran_focus INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',
    signal_score REAL,
    priority TEXT,
    analysis_json TEXT,
    warnings_json TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL UNIQUE,
    source_code TEXT NOT NULL,
    external_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    publication_date TEXT,
    year INTEGER,
    url TEXT,
    doi TEXT,
    authors_json TEXT NOT NULL,
    affiliations_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_evidence (
    scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    evidence_id INTEGER NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    PRIMARY KEY (scan_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL UNIQUE REFERENCES scans(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    signal_score REAL NOT NULL,
    priority TEXT NOT NULL,
    maturity TEXT,
    ethical_intensity TEXT,
    iran_relevance TEXT,
    trend_direction TEXT,
    clinical_activity_score REAL,
    novelty_score REAL,
    source_counts_json TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source_code);
CREATE INDEX IF NOT EXISTS idx_evidence_year ON evidence(year);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_score ON signals(signal_score DESC);
"""

SEED_SOURCES = [
    ("pubmed", "PubMed / MEDLINE", "literature", 1, "https://pubmed.ncbi.nlm.nih.gov/"),
    ("clinicaltrials", "ClinicalTrials.gov", "clinical_trials", 1, "https://clinicaltrials.gov/"),
    ("openalex", "OpenAlex", "scholarly_graph", 1, "https://openalex.org/"),
    ("crossref", "Crossref", "metadata", 1, "https://www.crossref.org/"),
]

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self):
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            for row in SEED_SOURCES:
                conn.execute(
                    """INSERT INTO sources(code,name,source_type,api_available,base_url,created_at)
                       VALUES(?,?,?,?,?,?)
                       ON CONFLICT(code) DO UPDATE SET
                         name=excluded.name,
                         source_type=excluded.source_type,
                         api_available=excluded.api_available,
                         base_url=excluded.base_url""",
                    (*row, utcnow()),
                )

    def create_scan(self, payload: dict[str, Any]) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO scans(query,sources_json,max_results,from_year,to_year,iran_focus,status,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (
                    payload["query"],
                    json.dumps(payload["sources"], ensure_ascii=False),
                    payload["max_results"],
                    payload.get("from_year"),
                    payload.get("to_year"),
                    1 if payload.get("iran_focus") else 0,
                    "running",
                    utcnow(),
                ),
            )
            return int(cur.lastrowid)

    def finish_scan(self, scan_id: int, signal_score: float, priority: str, analysis: dict, warnings: list[str]):
        with self.connect() as conn:
            conn.execute(
                """UPDATE scans
                   SET status='completed', signal_score=?, priority=?, analysis_json=?, warnings_json=?, completed_at=?
                   WHERE id=?""",
                (
                    signal_score,
                    priority,
                    json.dumps(analysis, ensure_ascii=False),
                    json.dumps(warnings, ensure_ascii=False),
                    utcnow(),
                    scan_id,
                ),
            )

    def fail_scan(self, scan_id: int, message: str):
        with self.connect() as conn:
            conn.execute(
                """UPDATE scans SET status='failed', warnings_json=?, completed_at=? WHERE id=?""",
                (json.dumps([message], ensure_ascii=False), utcnow(), scan_id),
            )

    @staticmethod
    def evidence_fingerprint(record: dict[str, Any]) -> str:
        basis = "|".join([
            record.get("source", ""),
            record.get("external_id", ""),
            record.get("doi") or "",
            (record.get("title") or "").strip().lower(),
        ])
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def upsert_evidence(self, scan_id: int, records: list[dict[str, Any]]) -> list[int]:
        ids = []
        with self.connect() as conn:
            for r in records:
                fp = self.evidence_fingerprint(r)
                now = utcnow()
                conn.execute(
                    """INSERT INTO evidence(
                        fingerprint,source_code,external_id,evidence_type,title,abstract,
                        publication_date,year,url,doi,authors_json,affiliations_json,metadata_json,
                        first_seen_at,last_seen_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(fingerprint) DO UPDATE SET
                        abstract=excluded.abstract,
                        publication_date=excluded.publication_date,
                        year=excluded.year,
                        url=excluded.url,
                        doi=excluded.doi,
                        authors_json=excluded.authors_json,
                        affiliations_json=excluded.affiliations_json,
                        metadata_json=excluded.metadata_json,
                        last_seen_at=excluded.last_seen_at""",
                    (
                        fp, r["source"], r["external_id"], r.get("evidence_type","publication"),
                        r.get("title",""), r.get("abstract",""), r.get("publication_date"),
                        r.get("year"), r.get("url",""), r.get("doi"),
                        json.dumps(r.get("authors",[]), ensure_ascii=False),
                        json.dumps(r.get("affiliations",[]), ensure_ascii=False),
                        json.dumps(r.get("metadata",{}), ensure_ascii=False),
                        now, now,
                    ),
                )
                row = conn.execute("SELECT id FROM evidence WHERE fingerprint=?", (fp,)).fetchone()
                eid = int(row["id"])
                ids.append(eid)
                conn.execute(
                    "INSERT OR IGNORE INTO scan_evidence(scan_id,evidence_id) VALUES(?,?)",
                    (scan_id, eid),
                )
        return ids

    def save_signal(self, scan_id: int, query: str, signal: dict[str, Any]):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO signals(
                    scan_id,query,signal_score,priority,maturity,ethical_intensity,iran_relevance,
                    trend_direction,clinical_activity_score,novelty_score,source_counts_json,analysis_json,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(scan_id) DO UPDATE SET
                    signal_score=excluded.signal_score,
                    priority=excluded.priority,
                    maturity=excluded.maturity,
                    ethical_intensity=excluded.ethical_intensity,
                    iran_relevance=excluded.iran_relevance,
                    trend_direction=excluded.trend_direction,
                    clinical_activity_score=excluded.clinical_activity_score,
                    novelty_score=excluded.novelty_score,
                    source_counts_json=excluded.source_counts_json,
                    analysis_json=excluded.analysis_json""",
                (
                    scan_id, query, signal["signal_score"], signal["priority"],
                    signal["maturity"]["stage"], signal["ethics"]["intensity"],
                    signal["iran"]["level"], signal["trend"]["direction"],
                    signal["clinical_activity_score"], signal["novelty_score"],
                    json.dumps(signal["source_counts"], ensure_ascii=False),
                    json.dumps(signal, ensure_ascii=False),
                    utcnow(),
                ),
            )

    def list_sources(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM sources ORDER BY id").fetchall()]

    def list_scans(self, limit: int = 50):
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT id,query,status,signal_score,priority,sources_json,created_at,completed_at
                   FROM scans ORDER BY id DESC LIMIT ?""", (limit,)
            ).fetchall()
            out=[]
            for r in rows:
                d=dict(r)
                d["sources"]=json.loads(d.pop("sources_json") or "[]")
                out.append(d)
            return out

    def get_scan(self, scan_id: int):
        with self.connect() as conn:
            r=conn.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
            if not r: return None
            d=dict(r)
            d["sources"]=json.loads(d.pop("sources_json") or "[]")
            d["analysis"]=json.loads(d.pop("analysis_json") or "{}")
            d["warnings"]=json.loads(d.pop("warnings_json") or "[]")
            return d

    def get_signal(self, scan_id: int):
        with self.connect() as conn:
            r=conn.execute("SELECT analysis_json FROM signals WHERE scan_id=?", (scan_id,)).fetchone()
            return json.loads(r["analysis_json"]) if r else None

    def list_signals(self, limit: int = 50):
        with self.connect() as conn:
            rows=conn.execute(
                """SELECT scan_id,query,signal_score,priority,maturity,ethical_intensity,
                          iran_relevance,trend_direction,created_at
                   FROM signals ORDER BY signal_score DESC, id DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def evidence_for_scan(self, scan_id: int):
        with self.connect() as conn:
            rows=conn.execute(
                """SELECT e.* FROM evidence e
                   JOIN scan_evidence se ON se.evidence_id=e.id
                   WHERE se.scan_id=? ORDER BY e.year DESC, e.id DESC""", (scan_id,)
            ).fetchall()
            out=[]
            for r in rows:
                d=dict(r)
                d["authors"]=json.loads(d.pop("authors_json") or "[]")
                d["affiliations"]=json.loads(d.pop("affiliations_json") or "[]")
                d["metadata"]=json.loads(d.pop("metadata_json") or "{}")
                out.append(d)
            return out
