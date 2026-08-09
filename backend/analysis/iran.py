from __future__ import annotations
from backend.models import IranResult, EvidenceRecord

IRAN_TERMS = [
    " iran ","iranian","tehran","isfahan","mashhad","shiraz","tabriz","qom",
    "iran university","iranian registry","ministry of health iran","mohme",
    "سپاس","ایران","تهران","اصفهان","مشهد","شیراز","تبریز"
]
CULTURAL_TERMS = ["islamic jurisprudence","fiqh","fatwa","sharia","sanction","تحریم","فقه","فتوا"]

def analyze_iran(records: list[EvidenceRecord]) -> IranResult:
    reasons=[]
    score=0.0
    for r in records:
        text=(" "+r.title+" "+r.abstract+" "+" ".join(r.affiliations)+" "+str(r.metadata)+" ").lower()
        for term in IRAN_TERMS:
            if term.lower() in text:
                reasons.append(f"{r.source}: {term.strip()}")
                score += 10
                break
        countries=r.metadata.get("countries") if isinstance(r.metadata,dict) else None
        if isinstance(countries,list) and any(str(c).lower() in {"iran","ir"} for c in countries):
            reasons.append(f"{r.source}: Iran country/location metadata")
            score += 15
        for term in CULTURAL_TERMS:
            if term.lower() in text:
                reasons.append(f"{r.source}: {term}")
                score += 4
                break
    score=min(100.0,score)
    level="بالا" if score>=60 else "متوسط" if score>=25 else "پایین"
    return IranResult(level=level,score=round(score,1),reasons=list(dict.fromkeys(reasons))[:20])
