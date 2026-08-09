from __future__ import annotations
from datetime import date
from backend.models import TrendResult, EvidenceRecord

def analyze_trend(records: list[EvidenceRecord]) -> TrendResult:
    current=date.today().year
    recent=sum(1 for r in records if r.year and current-1 <= r.year <= current)
    previous=sum(1 for r in records if r.year and current-3 <= r.year <= current-2)
    if previous==0:
        ratio=2.0 if recent>0 else 0.0
    else:
        ratio=recent/previous
    if ratio>=1.5 and recent>=3:
        direction="صعودی"
        score=min(100.0,55+(ratio-1.5)*25)
    elif ratio<=0.67 and previous>=3:
        direction="نزولی"
        score=max(0.0,35*ratio)
    else:
        direction="پایدار/نامشخص"
        score=45.0 if (recent+previous)>0 else 20.0
    return TrendResult(
        direction=direction,score=round(min(100.0,score),1),
        recent_count=recent,previous_count=previous,growth_ratio=round(ratio,2)
    )
