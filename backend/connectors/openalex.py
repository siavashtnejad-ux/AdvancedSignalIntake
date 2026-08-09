from __future__ import annotations
from backend.connectors.base import BaseConnector
from backend.models import ConnectorResult, EvidenceRecord, ScanRequest
from backend.config import settings

class OpenAlexConnector(BaseConnector):
    code="openalex"
    BASE="https://api.openalex.org/works"

    @staticmethod
    def abstract_from_inverted(index):
        if not isinstance(index,dict): return ""
        pairs=[]
        for word, positions in index.items():
            for pos in positions or []:
                pairs.append((pos,word))
        return " ".join(word for _,word in sorted(pairs))

    async def search(self, request: ScanRequest) -> ConnectorResult:
        if not settings.openalex_api_key:
            return ConnectorResult(
                source=self.code,total=0,records=[],
                warnings=["OpenAlex skipped: OPENALEX_API_KEY is not configured. Since February 2026 OpenAlex requires an API key for normal API use."]
            )
        filters=[]
        if request.from_year: filters.append(f"from_publication_date:{request.from_year}-01-01")
        if request.to_year: filters.append(f"to_publication_date:{request.to_year}-12-31")
        # Iran focus is handled as a local relevance signal to avoid over-constraining recall.
        params={
            "search":request.query,
            "per-page":str(min(request.max_results,100)),
            "api_key":settings.openalex_api_key,
        }
        if filters: params["filter"]=",".join(filters)
        async with self.client() as client:
            r=await client.get(self.BASE,params=params)
            r.raise_for_status()
            data=r.json()
        records=[]
        for w in data.get("results",[]):
            wid=(w.get("id") or "").rsplit("/",1)[-1]
            doi=(w.get("doi") or "").replace("https://doi.org/","") or None
            authors=[]
            affiliations=[]
            countries=[]
            for a in w.get("authorships") or []:
                an=((a.get("author") or {}).get("display_name"))
                if an: authors.append(an)
                for inst in a.get("institutions") or []:
                    name=inst.get("display_name")
                    cc=inst.get("country_code")
                    if name: affiliations.append(name)
                    if cc: countries.append(cc)
            primary=w.get("primary_location") or {}
            source=(primary.get("source") or {}).get("display_name") or ""
            url=primary.get("landing_page_url") or w.get("doi") or w.get("id") or ""
            year=w.get("publication_year")
            records.append(EvidenceRecord(
                source=self.code,external_id=wid,evidence_type="publication",
                title=w.get("display_name") or "Untitled",
                abstract=self.abstract_from_inverted(w.get("abstract_inverted_index")),
                publication_date=w.get("publication_date"),year=year,url=url,doi=doi,
                authors=authors,affiliations=list(dict.fromkeys(affiliations)),
                metadata={
                    "cited_by_count":w.get("cited_by_count",0),
                    "open_access":w.get("open_access") or {},
                    "source":source,
                    "countries":countries,
                    "type":w.get("type"),
                    "topics":[t.get("display_name") for t in (w.get("topics") or []) if t.get("display_name")]
                }
            ))
        total=int((data.get("meta") or {}).get("count") or len(records))
        return ConnectorResult(source=self.code,total=total,records=records)
