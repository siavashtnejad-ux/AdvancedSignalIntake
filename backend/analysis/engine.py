from __future__ import annotations
from backend.models import EvidenceRecord, SignalResult
from backend.analysis.ethics import analyze_ethics
from backend.analysis.maturity import analyze_maturity
from backend.analysis.iran import analyze_iran
from backend.analysis.trend import analyze_trend
from backend.analysis.scoring import novelty_score, clinical_activity, final_score, priority

def analyze_signal(query: str, records: list[EvidenceRecord], source_counts: dict[str,int], warnings: list[str]) -> SignalResult:
    ethics=analyze_ethics(records)
    maturity=analyze_maturity(records)
    iran=analyze_iran(records)
    trend=analyze_trend(records)
    clinical=clinical_activity(records)
    novelty=novelty_score(records)
    score=final_score(trend.score,clinical,ethics.score,iran.score,novelty)
    return SignalResult(
        query=query,signal_score=score,priority=priority(score),
        ethics=ethics,maturity=maturity,iran=iran,trend=trend,
        clinical_activity_score=clinical,novelty_score=novelty,
        evidence_count=len(records),source_counts=source_counts,warnings=warnings
    )
