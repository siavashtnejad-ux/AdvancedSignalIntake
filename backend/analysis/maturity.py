from __future__ import annotations
from backend.models import MaturityResult, EvidenceRecord

MARKERS = {
    "پژوهش پایه": ["in vitro","animal model","preclinical","proof of concept","proof-of-concept","mechanistic","laboratory"],
    "نمونه اولیه": ["prototype","pilot","feasibility","early-stage","early stage","first-in-human","first in human"],
    "کارآزمایی بالینی": ["clinical trial","randomized","phase 1","phase i","phase 2","phase ii","phase 3","phase iii"],
    "اعتبارسنجی بالینی": ["validation","external validation","prospective validation","multicenter","multi-center"],
    "پذیرش/استقرار": ["implementation","deployment","adoption","routine care","real-world","real world","clinical rollout","approved"],
}

STAGE_SCORE = {
    "پژوهش پایه":20,
    "نمونه اولیه":40,
    "کارآزمایی بالینی":60,
    "اعتبارسنجی بالینی":80,
    "پذیرش/استقرار":100,
}

def analyze_maturity(records: list[EvidenceRecord]) -> MaturityResult:
    corpus="\n".join(f"{r.title} {r.abstract}" for r in records).lower()
    found={}
    for stage,terms in MARKERS.items():
        hits=[t for t in terms if t in corpus]
        found[stage]=hits
    # ClinicalTrials evidence is an explicit maturity marker.
    trial_count=sum(1 for r in records if r.evidence_type=="clinical_trial")
    if trial_count:
        found["کارآزمایی بالینی"]=list(dict.fromkeys(found["کارآزمایی بالینی"]+["ClinicalTrials.gov evidence"]))
    ranked=sorted(STAGE_SCORE,key=lambda s:STAGE_SCORE[s],reverse=True)
    stage="پژوهش پایه"
    for s in ranked:
        if found[s]:
            stage=s
            break
    score=float(STAGE_SCORE[stage])
    # Blend evidence breadth without allowing it to jump multiple lifecycle stages.
    if trial_count and score<60: score=60.0
    markers=[m for s in ranked for m in found[s]][:20]
    return MaturityResult(stage=stage,score=round(score,1),markers=markers)
