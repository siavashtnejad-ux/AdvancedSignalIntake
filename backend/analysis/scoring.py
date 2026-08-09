from __future__ import annotations

def novelty_score(records) -> float:
    markers=[
        "novel","emerging","first-in-human","first in human","proof-of-concept",
        "proof of concept","prototype","new approach","new method","transformative",
        "disruptive","early-stage","early stage"
    ]
    corpus="\n".join(f"{r.title} {r.abstract}" for r in records).lower()
    hits=sum(1 for m in markers if m in corpus)
    # Recency adds a small novelty component.
    years=[r.year for r in records if r.year]
    recency=0
    if years:
        from datetime import date
        y=date.today().year
        recency=sum(1 for yr in years if yr>=y-1)/len(years)*30
    return round(min(100.0,hits*12+recency),1)

def clinical_activity(records) -> float:
    trials=[r for r in records if r.evidence_type=="clinical_trial"]
    if not trials: return 0.0
    advanced=0
    active=0
    for r in trials:
        phases=[str(x).upper() for x in (r.metadata.get("phases") or [])]
        status=str(r.metadata.get("status") or "").upper()
        if any(x in {"PHASE2","PHASE3","PHASE4"} for x in phases): advanced+=1
        if status in {"RECRUITING","ACTIVE_NOT_RECRUITING","ENROLLING_BY_INVITATION","NOT_YET_RECRUITING"}: active+=1
    base=min(70.0,len(trials)*7)
    return round(min(100.0,base+min(15,advanced*4)+min(15,active*3)),1)

def final_score(trend, clinical, ethics, iran, novelty):
    # Exploratory heuristic - intentionally explicit and editable.
    value=(
        trend*0.25 +
        clinical*0.25 +
        ethics*0.20 +
        iran*0.15 +
        novelty*0.15
    )
    return round(max(0.0,min(100.0,value)),1)

def priority(score: float) -> str:
    if score>=75: return "اولویت بالا"
    if score>=55: return "اولویت متوسط"
    if score>=35: return "پایش"
    return "اولویت پایین"
