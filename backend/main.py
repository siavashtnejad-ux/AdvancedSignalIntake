from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings, BASE_DIR
from backend.database import Database
from backend.models import ScanRequest
from backend.services.scanner import run_scan
from backend.services.exports import export_json, export_csv, export_pdf

db=Database(settings.db_path)
db.init()

app=FastAPI(title=settings.app_name,version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok":True,"app":settings.app_name,"database":str(settings.db_path)}

@app.get("/api/sources")
def sources():
    out=db.list_sources()
    # Expose configuration readiness without exposing keys.
    for s in out:
        if s["code"]=="openalex":
            s["configured"]=bool(settings.openalex_api_key)
            s["configuration_note"]="OPENALEX_API_KEY required"
        elif s["code"]=="pubmed":
            s["configured"]=True
            s["configuration_note"]="NCBI_EMAIL recommended; NCBI_API_KEY optional"
        elif s["code"]=="crossref":
            s["configured"]=True
            s["configuration_note"]="CROSSREF_MAILTO recommended"
        else:
            s["configured"]=True
            s["configuration_note"]=""
    return out

@app.post("/api/scan")
async def scan(req: ScanRequest):
    try:
        req.max_results=min(req.max_results,settings.max_results_cap)
        return await run_scan(db,req)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500,detail=f"{type(exc).__name__}: {exc}")

@app.get("/api/scans")
def scans(limit: int=Query(default=50,ge=1,le=200)):
    return db.list_scans(limit)

@app.get("/api/scans/{scan_id}")
def scan_detail(scan_id:int):
    scan=db.get_scan(scan_id)
    if not scan: raise HTTPException(404,"Scan not found")
    return {"scan":scan,"signal":db.get_signal(scan_id),"evidence":db.evidence_for_scan(scan_id)}

@app.get("/api/evidence")
def evidence(scan_id:int):
    return db.evidence_for_scan(scan_id)

@app.get("/api/signals")
def signals(limit:int=Query(default=50,ge=1,le=200)):
    return db.list_signals(limit)

@app.get("/api/export/{scan_id}.json")
def export_json_route(scan_id:int):
    try: data=export_json(db,scan_id)
    except KeyError: raise HTTPException(404,"Scan not found")
    return Response(data,media_type="application/json",headers={"Content-Disposition":f'attachment; filename="scan-{scan_id}.json"'})

@app.get("/api/export/{scan_id}.csv")
def export_csv_route(scan_id:int):
    try: data=export_csv(db,scan_id)
    except KeyError: raise HTTPException(404,"Scan not found")
    return Response(data,media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="scan-{scan_id}.csv"'})

@app.get("/api/export/{scan_id}.pdf")
def export_pdf_route(scan_id:int):
    try: data=export_pdf(db,scan_id)
    except KeyError: raise HTTPException(404,"Scan not found")
    return Response(data,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="scan-{scan_id}.pdf"'})

frontend=BASE_DIR/"frontend"
app.mount("/",StaticFiles(directory=frontend,html=True),name="frontend")
