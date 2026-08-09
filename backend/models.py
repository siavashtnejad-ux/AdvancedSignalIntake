from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

SourceName = Literal["pubmed", "clinicaltrials", "openalex", "crossref"]

class ScanRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    sources: list[SourceName] = Field(default_factory=lambda: ["pubmed", "clinicaltrials", "openalex", "crossref"])
    max_results: int = Field(default=25, ge=1, le=100)
    from_year: int | None = Field(default=None, ge=1900, le=2100)
    to_year: int | None = Field(default=None, ge=1900, le=2100)
    iran_focus: bool = False

class EvidenceRecord(BaseModel):
    source: str
    external_id: str
    evidence_type: str = "publication"
    title: str
    abstract: str = ""
    publication_date: str | None = None
    year: int | None = None
    url: str = ""
    doi: str | None = None
    authors: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ConnectorResult(BaseModel):
    source: str
    total: int = 0
    records: list[EvidenceRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class EthicsResult(BaseModel):
    domains: dict[str, float]
    matched_terms: dict[str, list[str]]
    intensity: str
    score: float

class MaturityResult(BaseModel):
    stage: str
    score: float
    markers: list[str]

class IranResult(BaseModel):
    level: str
    score: float
    reasons: list[str]

class TrendResult(BaseModel):
    direction: str
    score: float
    recent_count: int
    previous_count: int
    growth_ratio: float

class SignalResult(BaseModel):
    query: str
    signal_score: float
    priority: str
    ethics: EthicsResult
    maturity: MaturityResult
    iran: IranResult
    trend: TrendResult
    clinical_activity_score: float
    novelty_score: float
    evidence_count: int
    source_counts: dict[str, int]
    warnings: list[str] = Field(default_factory=list)

class ScanResponse(BaseModel):
    scan_id: int
    query: str
    signal: SignalResult
    evidence: list[EvidenceRecord]
