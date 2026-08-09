from __future__ import annotations
from datetime import date
from backend.connectors.base import BaseConnector
from backend.models import ConnectorResult, EvidenceRecord, ScanRequest
from backend.config import settings

def first_date(item):
    for key in ("published-print","published-online","published","created"):
        parts=((item.get(key) or {}).get("date-parts") or [])
        if parts and parts[0]:
            y=parts[0][0] if len(parts[0])>0 else None
            m=parts[0][1] if len(parts[0])>1 else None
            d=parts[0][2] if len(parts[0])>2 else None
            if y:
                return int(y), "-".join(str(x).zfill(2) if i else str(x) for i,x in enumerate([y,m,d]) if x is not None)
    return None,None

class CrossrefConnector(BaseConnector):
    code="crossref"
    BASE="https://api.crossref.org/works"

    async def search(self, request: ScanRequest) -> ConnectorResult:
        params={
            "query.bibliographic":request.query,
            "rows":str(min(request.max_results,100)),
            "sort":"published",
            "order":"desc",
            "select":"DOI,title,abstract,author,container-title,published,published-online,published-print,created,URL,publisher,type,subject,reference-count,is-referenced-by-count"
        }
        filters=[]
        if request.from_year: filters.append(f"from-pub-date:{request.from_year}-01-01")
        if request.to_year: filters.append(f"until-pub-date:{request.to_year}-12-31")
        if filters: params["filter"]=",".join(filters)
        if settings.crossref_mailto: params["mailto"]=settings.crossref_mailto
        async with self.client() as client:
            r=await client.get(self.BASE,params=params)
            r.raise_for_status()
            message=r.json().get("message",{})
        records=[]
        for item in message.get("items",[]):
            doi=item.get("DOI") or ""
            title=(item.get("title") or ["Untitled"])[0]
            abstract=item.get("abstract") or ""
            authors=[]
            for a in item.get("author") or []:
                name=" ".join(x for x in [a.get("given",""),a.get("family","")] if x).strip()
                if name: authors.append(name)
            year,date_text=first_date(item)
            container=(item.get("container-title") or [""])[0]
            records.append(EvidenceRecord(
                source=self.code,external_id=doi or item.get("URL",""),evidence_type="publication",
                title=title,abstract=abstract,publication_date=date_text,year=year,
                url=item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),doi=doi or None,
                authors=authors,affiliations=[],
                metadata={
                    "container_title":container,"publisher":item.get("publisher"),
                    "type":item.get("type"),"subjects":item.get("subject") or [],
                    "reference_count":item.get("reference-count",0),
                    "citation_count":item.get("is-referenced-by-count",0)
                }
            ))
        total=int(message.get("total-results") or len(records))
        return ConnectorResult(source=self.code,total=total,records=records)
