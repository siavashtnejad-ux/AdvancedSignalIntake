from __future__ import annotations
from backend.models import EthicsResult, EvidenceRecord

# Based on the five ethics content domains in the project's search strategy.
DOMAINS = {
    "research_ethics": [
        "informed consent","research integrity","scientific misconduct","plagiarism",
        "data fabrication","vulnerable research","irb","ethics committee","dual-use",
        "publication ethics","authorship","clinical trial registration"
    ],
    "clinical_ethics": [
        "truth-telling","disclosure","end-of-life","do-not-resuscitate","dnr",
        "withholding treatment","withdrawing treatment","paternalism","patient autonomy",
        "surrogate decision","futile care","palliative","confidentiality",
        "conscientious objection","shared decision"
    ],
    "technology_data_ethics": [
        "artificial intelligence","machine learning","algorithm","bias","biobank",
        "genetic privacy","genomic data","telemedicine","digital health","surveillance",
        "electronic health record","privacy","accountability","wearable","health data",
        "explainability","transparency"
    ],
    "justice_governance": [
        "health equity","resource allocation","rationing","sanction","drug shortage",
        "access to medicine","universal health coverage","insurance equity",
        "health disparity","refugee","migrant","priority setting","distributive justice",
        "health policy","governance","regulation"
    ],
    "organizational_ethics": [
        "conflict of interest","whistleblow","institutional corruption","professionalism",
        "dual practice","hospital governance","workplace harassment","burnout",
        "corporate influence","pharmaceutical industry","compliance","accountability"
    ],
}

def analyze_ethics(records: list[EvidenceRecord]) -> EthicsResult:
    corpus="\n".join(f"{r.title} {r.abstract}" for r in records).lower()
    matched={}
    domain_scores={}
    total_hits=0
    for domain,terms in DOMAINS.items():
        hits=[]
        hit_count=0
        for t in terms:
            count=corpus.count(t.lower())
            if count:
                hits.append(t)
                hit_count += min(count, 5)
        matched[domain]=hits
        # Cap domain score so a single repeated term cannot dominate.
        domain_scores[domain]=round(min(100.0, hit_count*6 + len(hits)*5),1)
        total_hits += hit_count
    active=sum(1 for v in domain_scores.values() if v>=15)
    score=round(min(100.0, (sum(domain_scores.values())/max(len(domain_scores),1))*0.75 + active*5),1)
    intensity="بالا" if score>=60 else "متوسط" if score>=30 else "پایین"
    return EthicsResult(domains=domain_scores,matched_terms=matched,intensity=intensity,score=score)
