from __future__ import annotations
import asyncio
from backend.models import ScanRequest, ScanResponse, EvidenceRecord
from backend.connectors.pubmed import PubMedConnector
from backend.connectors.clinicaltrials import ClinicalTrialsConnector
from backend.connectors.openalex import OpenAlexConnector
from backend.connectors.crossref import CrossrefConnector
from backend.analysis.engine import analyze_signal
from backend.database import Database

CONNECTORS={
    "pubmed":PubMedConnector,
    "clinicaltrials":ClinicalTrialsConnector,
    "openalex":OpenAlexConnector,
    "crossref":CrossrefConnector,
}

def normalized_title(s: str) -> str:
    import re
    return re.sub(r"\W+"," ",(s or "").lower()).strip()

def dedupe(records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    seen=set()
    out=[]
    for r in records:
        key=("doi",r.doi.lower()) if r.doi else ("title",normalized_title(r.title))
        if not key[1]: key=("source_id",f"{r.source}:{r.external_id}")
        if key in seen: continue
        seen.add(key)
        out.append(r)
    return out

async def run_scan(db: Database, req: ScanRequest) -> ScanResponse:
    if req.from_year and req.to_year and req.from_year>req.to_year:
        raise ValueError("from_year cannot be greater than to_year")
    payload=req.model_dump()
    scan_id=db.create_scan(payload)
    try:
        async def one(source):
            connector=CONNECTORS[source]()
            try:
                return await connector.search(req)
            except Exception as exc:
                from backend.models import ConnectorResult
                return ConnectorResult(source=source,total=0,records=[],warnings=[f"{source}: {type(exc).__name__}: {exc}"])

        results=await asyncio.gather(*(one(s) for s in req.sources))
        records=[]
        source_counts={}
        warnings=[]
        for r in results:
            records.extend(r.records)
            source_counts[r.source]=r.total
            warnings.extend(r.warnings)

        records=dedupe(records)
        signal=analyze_signal(req.query,records,source_counts,warnings)
        db.upsert_evidence(scan_id,[r.model_dump() for r in records])
        db.save_signal(scan_id,req.query,signal.model_dump())
        db.finish_scan(scan_id,signal.signal_score,signal.priority,signal.model_dump(),warnings)
        return ScanResponse(scan_id=scan_id,query=req.query,signal=signal,evidence=records)
    except Exception as exc:
        db.fail_scan(scan_id,str(exc))
        raise
